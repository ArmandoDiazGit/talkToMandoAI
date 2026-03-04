# FastAPI AI API (Backend)

A lightweight FastAPI backend that accepts a prompt and returns an AI-generated response.  
This repo is meant to be used as the backend for https://github.com/ArmandoDiazGit/MandoAI

---

## Features
- ✅ FastAPI REST API
- ✅ Prompt → AI response endpoint
- ✅ Uses an API key stored in a local `.env`
- ✅ Auto-generated Swagger docs (`/docs`)

---

## Tech Stack
- **Python** + **FastAPI**
- **Uvicorn** (ASGI server)
- **httpx** (HTTP client for calling the AI provider)
- **python-dotenv** (loads `.env` locally)

---

## Prerequisites
- Python **3.10+** (3.11+ recommended)

Check your version:
```bash
python --version
```

---
### 1) Clone repo
```bash
git clone https://github.com/ArmandoDiazGit/talkToMandoAI.git
cd talkToMandoAI
```

### 2) Create & activate virtual enviroment
- macOs or Linux
```
python -m venv .venv
source .venv/bin/activate
```
- windows
  ```
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```

### 3) Install dependencies
``` pip install -r requirements.txt ```

### 4) Create a .env file (required)
- Create a file named .env in the project root (same level as requirements.txt), then add your API key:
``` OPENAI_API_KEY=your_api_key_here ```

### 5) Start the server
``` uvicorn main:app --reload ```
