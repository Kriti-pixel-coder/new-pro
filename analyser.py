import subprocess
import json
import os
import hashlib

def run_analysis(target_path):
    print(f"[ANALYZER] Scanning {target_path} for real-world vulnerabilities...")
    
    cmd = [
        "semgrep", "scan", 
        "--config", "p/python",
        "--config", "p/secrets",
        "--config", "p/owasp-top-ten",
        "--config", "demo_rules.yaml",
        "--json", target_path
    ]
    
    # --- THE WINDOWS UNICODE FIX ---
    custom_env = os.environ.copy()
    custom_env["PYTHONUTF8"] = "1"
    
    result = subprocess.run(
        cmd, 
        capture_output=True, 
        text=True, 
        encoding='utf-8', 
        errors='ignore', 
        env=custom_env  
    )
    
    try:
        if not result.stdout.strip():
            print(f"⚠️ Semgrep returned empty output!")
            print(f"💡 Hidden Error (stderr): {result.stderr}")
            return -1
            
        raw_data = json.loads(result.stdout)
        results = raw_data.get("results", [])
        
        bugs = []
        seen_lines = set() 
        
        for r in results:
            line_number = r.get('start', {}).get('line') or r.get('range', {}).get('start', {}).get('line')
            file_path = r.get('path') 
            
            unique_bug_id = (file_path, line_number)
            
            if line_number and unique_bug_id not in seen_lines:
                seen_lines.add(unique_bug_id)
                
                # Generate a stable string ID to track across scans
                bug_id_str = hashlib.md5(f"{file_path}:{line_number}:{r['extra']['message']}".encode()).hexdigest()
                
                bugs.append({
                    "id": bug_id_str,
                    "file": file_path,
                    "line": line_number,
                    "type": r['extra']['message'],
                    "severity": r['extra']['severity']
                })
        
        
        # DEMO LIFESAVER: Cap higher now for Mega-Batching
        demo_limit = 50
        if len(bugs) > demo_limit:
            print(f"⚠️ Found {len(bugs)} bugs! Capping to top {demo_limit} for processing...")
            bugs = bugs[:demo_limit]
                
        with open("bugs.json", "w", encoding="utf-8") as f:
            json.dump(bugs, f, indent=2)
            
        return len(bugs)
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parsing Error: Semgrep outputted text instead of JSON.")
        print(f"💡 Raw Semgrep Output: {result.stdout[:500]}") 
        print(f"💡 Hidden Semgrep Error: {result.stderr[:500]}")
        return -1
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return -1