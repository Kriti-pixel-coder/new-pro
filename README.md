# 🛡️ Rakshak — AI-Powered Automated Security Remediation

> **Closing the Gap Between Detection and Remediation**

Rakshak is an autonomous, end-to-end DevSecOps pipeline that doesn't just *find* vulnerabilities — it *fixes* them. By combining static analysis with a large language model, it automatically patches security bugs in your codebase and verifies the fixes, reducing remediation time from days to minutes.

---

## 🚨 The Problem

- **Alert Fatigue:** Security tools generate thousands of alerts, overwhelming development teams.
- **Slow Remediation:** Manually investigating and fixing vulnerabilities is time-consuming and error-prone.
- **Vulnerability Window:** The longer a vulnerability remains unpatched, the higher the risk of exploitation.
- **Context Switching:** Developers lose productivity switching between writing features and patching security flaws.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔄 Automated Remediation Loop | Automatically patches vulnerabilities discovered by static analysis |
| 🎯 Granular Issue Handling | Groups bugs by type, processes each sequentially with up to 3 retries |
| 🤖 Multi-Model AI Support | Integrates with Google Gemini and CodeQwen (via Kaggle) |
| ✅ Robust Verification | Re-runs Semgrep after each fix to confirm resolution |
| 📊 Real-time Dashboard | Modern Next.js web frontend to track vulnerability status |
| 🔍 Smart Patching | Fuzzy matching ensures patches apply correctly even with whitespace differences |

---

## ⚙️ Architecture

```
GitHub Repo URL
      │
      ▼
 ┌──────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────────┐
 │  Scanner  │───▶│  Extractor  │───▶│  AI Healer  │───▶│   Patcher    │
 │ (Semgrep) │    │(Context Win)│    │  (LLM API)  │    │(Fuzzy Match) │
 └──────────┘    └─────────────┘    └─────────────┘    └──────────────┘
                                                               │
                                                               ▼
                                                        ┌──────────────┐
                                                        │   Verifier   │◀─── Loop (up to 3x)
                                                        │  (Re-Scan)   │
                                                        └──────────────┘
```

### Pipeline Steps

1. **Scanner** (`analyser.py`) — Runs Semgrep with rulesets (`p/python`, `p/secrets`, `p/owasp-top-ten`, and custom rules) to identify vulnerabilities. Outputs `bugs.json`.
2. **Extractor** — Extracts code context (±20 lines) around each vulnerability to give the AI meaningful context, merging overlapping windows.
3. **AI Healer** (`healer.py`) — Sends the code context and vulnerability details to a CodeQwen model (hosted on Kaggle via ngrok) or Gemini, which returns a corrected code snippet.
4. **Patcher** — Applies the AI-generated fix back to the source file using exact matching with a fuzzy whitespace-insensitive fallback.
5. **Verifier** (`main.py`) — Re-scans the modified file. If the bug persists, it retries up to 3 times per bug type.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Core Logic | Python 3 |
| Static Analysis | Semgrep (`p/python`, `p/secrets`, `p/owasp-top-ten`) |
| AI Engine | CodeQwen (Kaggle) via ngrok · Google Gemini API |
| Web Frontend | Next.js (React) + TailwindCSS |
| Automation / DB | n8n Workflows · Supabase (PostgreSQL) |
| API Bridge | FastAPI (`api.py`) |

---

## 📁 Project Structure

```
rakshak/
├── main.py               # Orchestration: clone → scan → heal → verify loop
├── analyser.py           # Semgrep-based vulnerability scanner
├── healer.py             # AI-powered code patcher (CodeQwen / Gemini)
├── api.py                # FastAPI server exposing pipeline status to frontend
├── demo_rules.yaml       # Custom Semgrep rules for demo scenarios
├── bugs.json             # Latest scan results (auto-generated)
├── actionable_bugs.json  # Current batch being remediated (auto-generated)
├── scanned_repo/         # Cloned target repository (auto-generated)
├── dummy_repo/           # Sample vulnerable app for testing
└── rakshak-web/          # Next.js real-time monitoring dashboard
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- [Semgrep](https://semgrep.dev/docs/getting-started/) installed and on PATH
- Node.js 18+ (for the web dashboard)
- A running CodeQwen server on Kaggle exposed via ngrok **OR** a Gemini API key

### 1. Clone this repository

```bash
git clone <your-repo-url>
cd rakshak
```

### 2. Install Python dependencies

```bash
pip install requests google-generativeai fastapi uvicorn
```

### 3. Configure the AI Backend

**Option A — CodeQwen on Kaggle (recommended for free GPU):**

Set the `KAGGLE_API_URL` environment variable to your ngrok URL from the [Kaggle notebook](https://www.kaggle.com/code/kriti270106/notebook8d949cbc41):

```bash
# Windows
set KAGGLE_API_URL=https://your-ngrok-url.ngrok-free.app

# Linux / macOS
export KAGGLE_API_URL=https://your-ngrok-url.ngrok-free.app
```

**Option B — Google Gemini:**

Set your `GEMINI_API_KEY` and update `healer.py` to use the Gemini SDK.

### 4. Run the Remediation Pipeline

```bash
python main.py
# Enter a public GitHub repo URL when prompted
```

To retry on an already-cloned repo:

```bash
python main.py --retry
```

### 5. Start the Web Dashboard (optional)

```bash
# Terminal 1: Start the API backend
python api.py

# Terminal 2: Start the Next.js frontend
cd rakshak-web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the real-time dashboard.

---

## 🔧 Configuration

| File | Purpose |
|---|---|
| `demo_rules.yaml` | Custom Semgrep rules — add your own YAML rules here |
| `healer.py` (line 12) | Hard-coded fallback ngrok URL if env var is not set |
| `analyser.py` (line 65) | `demo_limit = 50` — cap on bugs processed per run |

---

## 🔮 Future Scope

- **IDE Integrations** — VS Code and JetBrains extensions for inline fixes.
- **CI/CD Integration** — GitHub Actions / GitLab CI plugins that open PRs with fixes.
- **Auto-Generated Tests** — AI-written unit tests targeting the exact vulnerability fixed.
- **Local Fine-Tuned Models** — On-premise LLMs with zero API cost.
- **Broader Language Support** — Deep patches for C/C++, Rust, and Go.

---

## 📄 License

This project is for educational and research purposes.
