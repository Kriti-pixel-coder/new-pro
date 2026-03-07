import os
import json
import time
from google import genai

# Paste your API key here
client = genai.Client(api_key="AIzaSyDAk2rXS8XQ4ltUeZHjyq5t4S_Nvcn14NA")

def run_remediation(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        vulnerabilities = json.load(f)

    # 1. Group bugs by file
    files_to_fix = {}
    for v in vulnerabilities:
        path = v['file']
        if path not in files_to_fix: files_to_fix[path] = []
        files_to_fix[path].append(v)

    if not files_to_fix:
        return

    # 2. THE MEGA-BATCH ENGINE
    file_paths = list(files_to_fix.keys())
    chunk_size = 3 # Process 3 files at once to save your RPD!
    
    for i in range(0, len(file_paths), chunk_size):
        chunk = file_paths[i:i + chunk_size]
        
        print(f"\n🚀 MEGA-BATCH: Sending {len(chunk)} files to Gemini 2.5...")
        
        # Build the combined prompt
        prompt_context = ""
        for path in chunk:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            context_blocks = []
            for b in files_to_fix[path]:
                line_idx = b['line'] - 1
                start_idx = max(0, line_idx - 20)
                end_idx = min(len(lines), line_idx + 21)
                        
                snippet = "".join(lines[start_idx:end_idx])
                context_blocks.append(f"BUG ON LINE {b['line']} ({b['type']}):\n{snippet}")
            
            bugs = "\n\n".join(context_blocks)
            prompt_context += f"\n\n--- FILE: {path} ---\n{bugs}\n"

        prompt = f"""Act as a Senior Security Engineer. Fix ALL vulnerabilities in the multiple files provided below.
        
        {prompt_context}
        
        CRITICAL RULES:
        1. You MUST return the fixed code in a strict JSON format.
        2. The JSON keys MUST be the exact file paths provided.
        3. The JSON values MUST be an array of objects containing `"original_snippet"` and `"fixed_snippet"`.
        4. "original_snippet" MUST BE an exact substring matching the raw code, containing the vulnerability.
        5. "fixed_snippet" MUST BE the corrected replacement code for that snippet.
        6. Do NOT include any markdown formatting, explanations, or ```json blocks. Return ONLY the raw parseable JSON object.
        
        Example Output Format:
        {{
          "path/to/file1.py": [
             {{
                "original_snippet": "os.system('rm -rf ' + user_input)",
                "fixed_snippet": "subprocess.run(['rm', '-rf', user_input], check=True)"
             }}
          ]
        }}
        """
        # Retry loop with exponential backoff for rate limits
        max_api_retries = 3
        for attempt in range(max_api_retries):
            try:
                # --- USING YOUR NEW MODEL ---
                response = client.models.generate_content(
                    model="gemini-2.0-flash-lite", 
                    contents=prompt
                )
                
                # 3. UNPACK THE MEGA-BATCH
                clean_json = response.text.strip().replace("```json", "").replace("```", "")
                fixed_files = json.loads(clean_json)
                
                for path, fixes in fixed_files.items():
                    with open(path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                    
                    for fix in fixes:
                        if "original_snippet" in fix and "fixed_snippet" in fix:
                            file_content = file_content.replace(fix["original_snippet"], fix["fixed_snippet"])
                    
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(file_content)
                    print(f"✅ Secured {path}")
                    
                # A 2-second wait keeps you safely under logic limits without wasting time
                time.sleep(2) 
                break  # Success, exit retry loop
                
            except json.JSONDecodeError:
                print("❌ AI failed to format the batch properly. It will try again next iteration.")
                time.sleep(5)
                break  # Don't retry on bad JSON, move to next iteration
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    wait_time = 35 * (attempt + 1)  # 35s, 70s, 105s
                    print(f"⏳ Rate limited (attempt {attempt + 1}/{max_api_retries}). Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    if attempt == max_api_retries - 1:
                        print("❌ Max retries hit for this batch. Moving to next iteration.")
                else:
                    print(f"❌ Batch Error: {e}")
                    time.sleep(10)
                    break