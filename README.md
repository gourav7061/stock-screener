# MyProjectUnderstanding

A WAT framework project — **Workflows**, **Agents**, **Tools** architecture for reliable AI-driven automation.

## What Is This?

This project implements the **WAT framework** as described in [CLAUDE.md](CLAUDE.md). It separates concerns so that probabilistic AI (you, the agent) handles reasoning and decision-making, while deterministic code (Python scripts) handles execution.

**Read [CLAUDE.md](CLAUDE.md) first** — it's the source of truth for how this project works.

## Directory Layout

```
workflows/          # Markdown SOPs defining what to do and how
  └── README.md     # How to write a workflow
tools/              # Python scripts for deterministic execution
  ├── google_auth.py     # Google OAuth helper (scaffolding)
  └── [future tools...]
.tmp/               # Temporary/intermediate files (regenerable, gitignored)
.env                # Environment variables (local only, NEVER commit)
.env.example        # Template showing expected env var names
requirements.txt    # Python dependencies
CLAUDE.md           # Architecture and framework instructions
```

## Getting Started

### 1. Install Python Dependencies

```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env and add any real API keys
```

### 3. (Optional) Set Up Google OAuth

If you'll be using Google Sheets, Slides, or other Google APIs:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or use an existing one
3. Enable the **Google Sheets API** and **Google Slides API**
4. Create an "OAuth 2.0 Client ID" of type "Desktop application"
5. Download the credentials JSON file
6. Save it as `credentials.json` in this directory (it's gitignored)

The first time you run a tool that needs Google API access, you'll be prompted to authorize in your browser. The token is then cached locally.

### 4. Create Your First Workflow

1. Write a Markdown SOP in `workflows/` describing your task (see `workflows/README.md`)
2. Implement Python tools in `tools/` to do the actual work
3. Run the workflow via the agent orchestration loop

## Philosophy

- **Read [CLAUDE.md](CLAUDE.md)** for the architectural principles
- **Look for existing tools first** — reuse before building
- **Workflows are instructions to the agent** — write them like you're briefing a teammate
- **Tools are deterministic** — they handle the execution, leaving the agent free to coordinate
- **Local files are disposable** — anything important lives in cloud services (Google Sheets, etc.)

## Troubleshooting

### Import errors with google_auth
Ensure you've installed requirements.txt:
```bash
pip install -r requirements.txt
```

### credentials.json not found
This is expected if you haven't set up Google OAuth yet. You only need it if a workflow requires Google API access. See "Set Up Google OAuth" above.

### .env not loading
Make sure you've created `.env` (not just `.env.example`):
```bash
cp .env.example .env
```

## Questions?

Refer to [CLAUDE.md](CLAUDE.md) for detailed architectural guidance.
