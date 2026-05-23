# JARVIS

Local-first JARVIS assistant with a CustomTkinter GUI, Ollama model responses, MySQL-backed memory, wake/offline states, and themed visual effects.

<img width="543" height="228" alt="image" src="https://github.com/user-attachments/assets/6acc4c93-903d-485b-a1b6-348f8ad0048d" />

## Features

- Offline startup state until you type `Wake up`
- Startup diagnostics for MySQL, the `memories` table, Ollama, and the configured model
- Word-by-word streamed responses
- MySQL memory storage
- JARVIS-themed idle core and response matrix animations
- Configuration through `.env`

<img width="1919" height="1029" alt="image" src="https://github.com/user-attachments/assets/f813804a-7fa1-4d54-9825-9af429f2bd18" />

<img width="1919" height="1028" alt="image" src="https://github.com/user-attachments/assets/72740696-d186-40dd-88a7-98cfe19aae56" />

<img width="1919" height="1024" alt="image" src="https://github.com/user-attachments/assets/fdacd2e3-714b-40d7-b4cc-1c46f8217694" />

<img width="1033" height="240" alt="image" src="https://github.com/user-attachments/assets/04c1cb33-5d9e-42b2-9365-40e843cc1b60" />

## System Overview

JARVIS is designed as a local-first experimental assistant system focused on intelligent interaction, modularity, and responsive UI behavior.

The assistant combines:

* a CustomTkinter desktop interface
* local AI inference through Ollama
* persistent conversational memory with MySQL
* streamed response rendering
* animated system states and diagnostics

The project explores how AI systems can feel more interactive, atmospheric, and responsive rather than functioning as simple text interfaces.

## Future Goals

- Voice interaction
- Tool execution
- Plugin architecture
- Memory summarization
- Autonomous workflows
- Emotion/state simulation
- Multi-agent experimentation

## Requirements

- Python 3.11+
- Ollama installed and running
- An Ollama model named `jarvis`
- MySQL server

## Setup

Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and adjust values if needed:

```powershell
Copy-Item .env.example .env
```

Create the MySQL database, user, and memory table. If MySQL CLI is available:

```powershell
mysql -u root -p < mysql_setup.sql
```

The default app config expects:

```text
database: jarvis_memory
user: jarvis
password: jarvis_admin
auth plugin: mysql_native_password
```

## Run

```powershell
.\.venv\Scripts\python.exe gui.py
```

When the GUI opens, type:

```text
Wake up
```

JARVIS will run startup diagnostics and come online if MySQL, Ollama, and the configured model are available.

## Project Structure

```text
backend/
  brain.py       Core model, memory, startup checks, and CLI helpers
  Jarvis.py      Console entry point
assets/
  jarvis_icon.png
gui.py           Desktop GUI
mysql_setup.sql  Database/user/table setup
schema.sql       Memory table schema
```

## Notes

`.env`, `.venv`, Python cache files, logs, and large `.vsix` bundles are ignored by Git.
