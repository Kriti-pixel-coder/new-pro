import asyncio
import json
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import subprocess
import os

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
    if not os.path.exists(bugs_path):
        return []
        
    try:
        with open(bugs_path, "r", encoding="utf-8") as f:
            vulnerabilities = json.load(f)
            
        # Give each bug a unique ID and default status for the UI
        for i, bug in enumerate(vulnerabilities):
            bug["id"] = f"vuln_{i}_{bug.get('line', 0)}"
            bug["status"] = "Open"
            # Map semgrep severity to UI severity
            semgrep_sev = bug.get("severity", "WARNING").upper()
            bug["severity"] = "Critical" if semgrep_sev == "ERROR" else "High" if semgrep_sev == "WARNING" else "Medium"
            
        return vulnerabilities
    except Exception as e:
        return []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
