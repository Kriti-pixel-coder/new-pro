import os
import json
import time
import requests

# ============================================================================
#  🔗 KAGGLE CODEQWEN CONNECTION
#  Set the KAGGLE_API_URL environment variable to your ngrok URL, OR
#  paste your ngrok URL directly below.
#  Example: https://xxxx-xxxx-xxxx.ngrok-free.app
# ============================================================================
KAGGLE_API_URL = os.environ.get("KAGGLE_API_URL", "https://ira-nonevaporating-phonogramically.ngrok-free.dev")

def run_remediation(json_path, target_bug_type=None):
    with open(json_path, "r", encoding="utf-8") as f:
        vulnerabilities = json.load(f)

    # 1. Group bugs by file
    if target_bug_type:
        target_bugs = [v for v in vulnerabilities if v['type'] == target_bug_type]
        print(f"\n🚀 HEALER: Preparing to fix {len(target_bugs)} instances of '{target_bug_type}'...")
    else:
        target_bugs = vulnerabilities
        print(f"\n🚀 HEALER [MEGA-BATCH]: Preparing to fix {len(target_bugs)} vulnerabilities across all types...")

    if not target_bugs:
        return

    # 2. Build ONE consolidated prompt for all bugs
    prompt_context = ""
    
    files_for_this_type = {}
    for b in target_bugs:
        path = b['file']
        if path not in files_for_this_type: files_for_this_type[path] = []
        files_for_this_type[path].append(b)
        
    def fuzzy_replace(content, original, fixed):
        """Try exact match first, then fallback to whitespace-insensitive match."""
        # 1. Exact Match
        if original in content:
            return content.replace(original, fixed), True
            
        # 2. Fuzzy Match (Ignore horizontal whitespace per line)
        import re
        def normalize(s):
            return "\n".join([line.strip() for line in s.strip().split("\n")])
        
        norm_original = normalize(original)
        if not norm_original: return content, False
        
        # Split content into lines and check for the normalized snippet
        content_lines = content.splitlines()
        orig_lines = norm_original.splitlines()
        
        for i in range(len(content_lines) - len(orig_lines) + 1):
            window = content_lines[i : i + len(orig_lines)]
            norm_window = "\n".join([l.strip() for l in window])
            
            if norm_window == norm_original:
                # We found the block! Replace it.
                new_content_lines = content_lines[:i] + [fixed] + content_lines[i + len(orig_lines):]
                return "\n".join(new_content_lines), True
                
        return content, False

    for path, bugs_in_file in files_for_this_type.items():
        try:
            # Let's cleanly resolve the file path in case it's wrong in JSON
            actual_path = path
            if not os.path.exists(actual_path):
                base_name = os.path.basename(path)
                potential_path = os.path.join(os.getcwd(), "scanned_repo", "dummy_repo", base_name)
                if os.path.exists(potential_path):
                    actual_path = potential_path
                else: 
                    print(f"   ❌ ERROR: Could not find file on disk: '{path}'")
                    continue
                    
            with open(actual_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # splitlines(True) keeps whitespace and newlines perfectly intact
            lines = content.splitlines(keepends=True)

            # Merge overlapping 41-line windows (+/- 20 lines) to save tokens
            ranges = []
            for b in bugs_in_file:
                line_idx = b['line'] - 1
                start_idx = max(0, line_idx - 20)
                end_idx = min(len(lines), line_idx + 21)
                ranges.append([start_idx, end_idx])

            # Merge standard interval algorithm
            ranges.sort()
            merged_ranges = []
            if ranges:
                curr_start, curr_end = ranges[0]
                for next_start, next_end in ranges[1:]:
                    if next_start <= curr_end:
                        curr_end = max(curr_end, next_end)
                    else:
                        merged_ranges.append((curr_start, curr_end))
                        curr_start, curr_end = next_start, next_end
                merged_ranges.append((curr_start, curr_end))

            applied_any = False
            for start, end in merged_ranges:
                snippet = "".join(lines[start:end])
                
                issues_text = ""
                for b in bugs_in_file:
                    if start <= b['line'] - 1 < end:
                        issues_text += f"- Issue at line {b['line']}: {b['type']}\n"
                
                prompt = f"""[INST] You are an expert security engineer. Fix the vulnerabilities in the following code snippet. 
Return strictly the fixed raw code only.
Do not use markdown blocks (like ```python or ```).
Do not include explanations or any other text.
The code you return will completely and directly replace the original snippet.

Vulnerabilities:
{issues_text}

Original Code Snippet:
{snippet}
[/INST]"""

                max_api_retries = 3
                print("\n--- DEBUG: PROMPT SENT TO AI ---")
                print(prompt)
                print("--------------------------------\n")
                
                for attempt in range(max_api_retries):
                    try:
                        print(f"   📡 Sending to {KAGGLE_API_URL}/generate ...")
                        api_response = requests.post(
                            f"{KAGGLE_API_URL}/generate",
                            json={"prompt": prompt, "max_tokens": 4096},
                            headers={"ngrok-skip-browser-warning": "true"},
                            timeout=300 
                        )
                        api_response.raise_for_status()

                        raw_text = api_response.json().get("response", "")
                        
                        print("\n--- DEBUG: RAW RESPONSE FROM AI ---")
                        print(raw_text)
                        print("-----------------------------------\n")

                        # clean markdown blocks if the AI still included them
                        clean_text = raw_text.strip()
                        if clean_text.startswith("```"):
                            import re
                            match = re.search(r'```(?:python|py|json)?\n?(.*?)\s*```', clean_text, re.DOTALL)
                            if match:
                                clean_text = match.group(1).strip()
                            else:
                                clean_text = clean_text.replace("```python", "").replace("```json", "").replace("```", "").strip()
                                
                        # Handle case where AI still stubbornly returns JSON
                        if clean_text.startswith("{") and "}" in clean_text:
                            try:
                                parsed = json.loads(clean_text)
                                if isinstance(parsed, dict):
                                    extracted = None
                                    if "fixed_code" in parsed:
                                        extracted = parsed["fixed_code"]
                                    elif "code" in parsed:
                                        extracted = parsed["code"]
                                    elif len(parsed) == 1:
                                        extracted = list(parsed.values())[0]
                                    
                                    if isinstance(extracted, list):
                                        clean_text = "\n".join([str(x) for x in extracted])
                                    elif extracted is not None:
                                        clean_text = str(extracted)
                            except Exception:
                                pass
                                
                        # Ensure it ends with a newline if the original did
                        if snippet.endswith("\n") and not clean_text.endswith("\n"):
                            clean_text += "\n"

                        if clean_text:
                            new_content, success = fuzzy_replace(content, snippet, clean_text)
                            if success:
                                content = new_content
                                applied_any = True
                                break # Move to next snippet
                            else:
                                print(f"   ⚠️ Could not fuzzy match original snippet. Overwriting file with direct replace...")
                                if snippet in content:
                                    content = content.replace(snippet, clean_text)
                                    applied_any = True
                                    break
                                else:
                                    print("   ❌ Direct replace failed too.")
                        else:
                            print("   ❌ AI returned empty response. Retrying...")
                            time.sleep(3)
                            
                    except requests.exceptions.Timeout:
                        print(f"⏳ Timeout (Attempt {attempt+1}). Model heavy load...")
                        time.sleep(15)
                    except requests.exceptions.ConnectionError as e:
                        if "RemoteDisconnected" in str(e) or "Connection aborted" in str(e):
                            print(f"⌛ Ngrok connection timed out while AI was still generating (took >60s).")
                            print("   🚨 The Kaggle server is STILL processing this request in the background.")
                            print("   🚨 We will wait 3 minutes before retrying to prevent overloading Kaggle's queue!")
                            time.sleep(180)
                        else:
                            print(f"❌ Connection Error: {e}")
                            time.sleep(5)
                    except Exception as e:
                        print(f"❌ Error: {e}")
                        time.sleep(5)
                        
            if applied_any:
                with open(actual_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"   ✅ Applied fixes to {os.path.basename(actual_path)}")

        except Exception as e:
            print(f"⚠️ Error reading/processing {path}: {e}")
