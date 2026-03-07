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
    """Runs the scanning and healing loop with a 15s safety delay."""
    max_retries = 10
    iteration = 0
    
    while iteration < max_retries:
        iteration += 1
        print(f"\n{'='*20} ITERATION {iteration} {'='*20}")
        
        # 1. ANALYZE
        bug_count = run_analysis(target_path)
        
        if bug_count == 0:
            print(f"\n🎉 SUCCESS: All vulnerabilities patched in {target_path}!")
            return
        elif bug_count == -1:
            print("\n⚠️ Analyzer crashed. Check your Semgrep installation.")
            return
            
        print(f"❗ Found {bug_count} vulnerabilities. Starting AI Healing...")
        
        # 2. HEAL
        run_remediation("bugs.json")
        
        # 3. THE 5S RATE LIMIT SHIELD
        print(f"\n⏳ Iteration {iteration} complete. Waiting 5s to reset API limits...")
        for i in range(10, 0, -1):
            print(f"\rNext scan in: {i}s  ", end="")
            time.sleep(1)
        print("\n")
        
    print(f"\n{'='*20} FINAL VERIFICATION {'='*20}")
    final_bug_count = run_analysis(target_path)
    
    if final_bug_count == 0:
        print(f"\n🎉 SUCCESS: All vulnerabilities patched in {target_path}!")
    elif final_bug_count == -1:
        print("\n⚠️ Analyzer crashed during final verification.")
    else:
        print(f"⚠️ Max iterations reached. {final_bug_count} vulnerabilities remain. Manual review recommended.")

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