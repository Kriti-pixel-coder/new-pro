import time
import os
import shutil
import stat
import subprocess
from analyser import run_analysis
from healer import run_remediation 

def on_rm_error(func, path, exc_info):
    """Error handler for shutil.rmtree to force remove read-only files (Windows .git folders)"""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def clone_repo(repo_url, target_dir):
    """Clones a GitHub repo into a local directory."""
    print(f"\n🔄 Cloning repository: {repo_url}...")
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir, onerror=on_rm_error)
    try:
        subprocess.run(["git", "clone", repo_url, target_dir], check=True, capture_output=True)
        print(f"✅ Successfully cloned into '{target_dir}'")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to clone repo: {e.stderr.decode()}")
        exit(1)

def start_autonomous_remediation(target_path):
    """Runs the scanning and healing loop sequentially, one bug type at a time, with 3 retries each."""
    import json
    
    # Ensure starting clean
    if os.path.exists("unresolved_bugs.json"):
        os.remove("unresolved_bugs.json")
    
    unresolved_bugs = []
    
    print(f"\n{'='*20} INITIAL SCAN {'='*20}")
    bug_count = run_analysis(target_path)
    
    if bug_count == 0:
        print(f"\n🎉 SUCCESS: No vulnerabilities found in {target_path}!")
        return
    elif bug_count == -1:
        print("\n⚠️ Analyzer crashed. Check your Semgrep installation.")
        return
        
    print(f"❗ Found {bug_count} vulnerabilities initially.")
    
    # Load all bugs to determine unique types
    with open("bugs.json", "r", encoding="utf-8") as f:
        all_bugs = json.load(f)
        
    # Extract unique bug types
    bug_types = list(set(bug['type'] for bug in all_bugs))
    print(f"📋 Found {len(bug_types)} unique vulnerability types.")
    
    for current_type in bug_types:
        print(f"\n{'='*20} TARGETING BUG TYPE: {current_type} {'='*20}")
        
        for attempt in range(1, 4): # Up to 3 retries per type
            print(f"\n--- Attempt {attempt}/3 for '{current_type}' ---")
            
            # Read current bugs
            with open("bugs.json", "r", encoding="utf-8") as f:
                current_bugs = json.load(f)
                
            # Filter actionable bugs for THIS TYPE that are not already unresolved
            actionable_bugs = []
            unresolved_ids = {b['id'] for b in unresolved_bugs}
            
            for bug in current_bugs:
                if bug['type'] == current_type and bug['id'] not in unresolved_ids:
                    actionable_bugs.append(bug)
                    
            if not actionable_bugs:
                print(f"✅ No more actionable bugs of type '{current_type}' left.")
                break # Move to next type
                
            print(f"🔨 Sending {len(actionable_bugs)} bugs of type '{current_type}' to AI...")
            
            # Write only these specific bugs for healer
            with open("actionable_bugs.json", "w", encoding="utf-8") as f:
                json.dump(actionable_bugs, f, indent=2)
                
            # Run remediation specifically for these bugs
            run_remediation("actionable_bugs.json", target_bug_type=current_type)
            
            # Verify fixes
            print("\n🔍 Verifying fixes...")
            new_bug_count = run_analysis(target_path)
            
            with open("bugs.json", "r", encoding="utf-8") as f:
                new_scan_bugs = json.load(f)
                
            # Count remaining bugs of THIS type
            remaining_of_type = [b for b in new_scan_bugs if b['type'] == current_type]
            
            if len(remaining_of_type) == 0:
                 print(f"🎉 Successfully fixed all bugs of type '{current_type}'!")
                 break # Done with this type, move to next
                 
            if len(remaining_of_type) >= len(actionable_bugs):
                print(f"⚠️ No progress made on '{current_type}' in this attempt.")
                
            if attempt == 3 and len(remaining_of_type) > 0:
                print(f"❌ Could not fully resolve '{current_type}' after 3 attempts.")
                # Mark remaining as unresolved
                current_ids = {b['id'] for b in new_scan_bugs}
                for b in actionable_bugs:
                    if b['id'] in current_ids:
                        unresolved_bugs.append(b)
                
                # Update unresolved JSON file
                with open("unresolved_bugs.json", "w", encoding="utf-8") as f:
                    json.dump(unresolved_bugs, f, indent=2)
                    
            time.sleep(2) # Brief pause between attempts
            
    print(f"\n{'='*20} FINAL SUMMARY {'='*20}")
    if unresolved_bugs:
        print(f"⚠️ {len(unresolved_bugs)} vulnerabilities remain unresolved after max retries.")
        print("   They have been logged to unresolved_bugs.json for frontend display.")
    else:
        print(f"🎉 All target vulnerabilities patched successfully!")

if __name__ == "__main__":
    import sys
    print("🛡️  Welcome to the Autonomous DevSecOps Agent 🛡️")
    workspace_dir = os.path.join(os.getcwd(), "scanned_repo")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--retry":
        print("\n🔄 Retrying Autonomous Remediation on existing workspace...")
        start_autonomous_remediation(workspace_dir)
    else:
        repo_input = input("Enter a public GitHub Repo URL: ")
        clone_repo(repo_input, workspace_dir)
        start_autonomous_remediation(workspace_dir)
        
    print(f"\n🚀 ALL DONE! Secured code is in: '{workspace_dir}'")