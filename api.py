import asyncio
import json
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import subprocess
import os
import shutil
from fastapi.responses import StreamingResponse, FileResponse

app = FastAPI()

# Allow CORS for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LogStreamManager:
    def __init__(self):
        self.logs = []
        self.subscribers = []
        self.is_running = False

    def add_log(self, log_msg: str):
        self.logs.append(log_msg)
        for queue in self.subscribers:
            queue.put_nowait(log_msg)

    async def run_pipeline(self, repo_url: str = None, is_retry: bool = False):
        self.is_running = True
        self.logs.clear()
        
        if is_retry:
            self.add_log("🔄 Retrying RAKSHAK Pipeline...")
        else:
            # Prevent the UI from showing old bugs during the cloning phase
            if os.path.exists("bugs.json"):
                try:
                    os.remove("bugs.json")
                except:
                    pass
            self.add_log(f"Starting RAKSHAK Pipeline for {repo_url}...")
        
        try:
            # Create a script file to run the main logic and pass the URL
            # Since main.py uses `input()`, we will feed it via STDIN
            
            # Force UTF-8 encoding so emojis in print statements don't crash the script on Windows
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            args = ["python", "-u", "main.py"]
            if is_retry:
                args.append("--retry")
            
            process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env
            )
            
            if not is_retry and repo_url:
                # Send the URL to the script's `input()` prompt
                process.stdin.write((repo_url + "\n").encode())
                await process.stdin.drain()
            
            process.stdin.close()
            
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                decoded_line = line.decode('utf-8').strip()
                if decoded_line:
                    self.add_log(decoded_line)
                    
            await process.wait()
            self.add_log("Pipeline Execution Finished.")
            
        except Exception as e:
            self.add_log(f"Error executing pipeline: {e}")
            
        self.is_running = False

log_manager = LogStreamManager()

@app.post("/api/scan")
async def start_scan(payload: dict, background_tasks: BackgroundTasks):
    repo_url = payload.get("repo_url")
    if log_manager.is_running:
        return {"status": "error", "message": "Pipeline is already running."}
        
    background_tasks.add_task(log_manager.run_pipeline, repo_url)
    return {"status": "success", "message": "Pipeline started."}

@app.post("/api/retry")
async def retry_scan(background_tasks: BackgroundTasks):
    if log_manager.is_running:
        return {"status": "error", "message": "Pipeline is already running."}
        
    background_tasks.add_task(log_manager.run_pipeline, None, True)
    return {"status": "success", "message": "Retry started."}

@app.get("/api/logs")
async def stream_logs():
    async def event_generator():
        # Send existing logs first
        for log in log_manager.logs:
            yield f"data: {json.dumps({'message': log})}\n\n"
            
        q = asyncio.Queue()
        log_manager.subscribers.append(q)
        try:
            while True:
                msg = await q.get()
                yield f"data: {json.dumps({'message': msg})}\n\n"
        except asyncio.CancelledError:
            log_manager.subscribers.remove(q)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/bugs")
async def get_bugs():
    bugs_path = "bugs.json"
    unresolved_path = "unresolved_bugs.json"
    
    all_bugs = []
    
    # 1. Load Unresolved Bugs
    unresolved_list = []
    if os.path.exists(unresolved_path):
        try:
            with open(unresolved_path, "r", encoding="utf-8") as f:
                unresolved_list = json.load(f)
        except Exception:
            pass
            
    # Create a fast lookup for unresolved bugs
    unresolved_signatures = {f"{b.get('file')}:{b.get('line')}" for b in unresolved_list}
    
    # 2. Load Current Bugs (from the latest scan)
    if os.path.exists(bugs_path):
        try:
            with open(bugs_path, "r", encoding="utf-8") as f:
                current_bugs = json.load(f)
                
            for i, bug in enumerate(current_bugs):
                bug_sig = f"{bug.get('file')}:{bug.get('line')}"
                
                bug["id"] = f"vuln_{i}_{bug.get('line', 0)}"
                
                # If this bug is in the unresolved list, it's Unresolved.
                # If the pipeline is running, it's being fixed.
                # If the pipeline is stopped, it's Open.
                if bug_sig in unresolved_signatures:
                    bug["status"] = "Unresolved"
                elif log_manager.is_running:
                    bug["status"] = "Fixing..."
                else:
                    bug["status"] = "Open"
                    
                semgrep_sev = bug.get("severity", "WARNING").upper()
                bug["severity"] = "Critical" if semgrep_sev == "ERROR" else "High" if semgrep_sev == "WARNING" else "Medium"
                
                all_bugs.append(bug)
        except Exception:
            pass
            
    return all_bugs

@app.get("/api/download")
async def download_secured():
    workspace_dir = os.path.join(os.getcwd(), "scanned_repo")
    if not os.path.exists(workspace_dir):
        return {"status": "error", "message": "No secured repository found. Run a scan first."}
    
    # Create a temporary zip file
    zip_basename = os.path.join(os.getcwd(), "secured_code")
    zip_path = shutil.make_archive(zip_basename, 'zip', workspace_dir)
    
    return FileResponse(
        path=zip_path,
        filename="secured_code.zip",
        media_type="application/zip"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
