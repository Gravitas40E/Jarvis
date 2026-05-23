import os
from pathlib import Path

os.environ["OLLAMA_NO_GPU"] = "1"

import mysql.connector
import ollama
from mysql.connector import Error as MySQLError

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"


def load_env_file(path=ENV_PATH):
    if not path.exists():
        return

    for line in path.read_text().splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def get_env_int(name, default):
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


load_env_file()

DB_CONFIG = {
    "host": os.getenv("JARVIS_DB_HOST", "localhost"),
    "port": get_env_int("JARVIS_DB_PORT", 3306),
    "user": os.getenv("JARVIS_DB_USER", "jarvis"),
    "password": os.getenv("JARVIS_DB_PASSWORD", "jarvis_admin"),
    "database": os.getenv("JARVIS_DB_NAME", "jarvis_memory"),
}

DB_AUTH_PLUGIN = os.getenv("JARVIS_DB_AUTH_PLUGIN", "").strip()

if DB_AUTH_PLUGIN:
    DB_CONFIG["auth_plugin"] = DB_AUTH_PLUGIN

MODEL_NAME = os.getenv("JARVIS_MODEL", "jarvis")
DEFAULT_MEMORY_LIMIT = get_env_int("JARVIS_MEMORY_LIMIT", 5)

db = None
cursor = None


def get_database():
    global db

    if db is None or not db.is_connected():
        db = mysql.connector.connect(**DB_CONFIG)

    return db


def get_cursor():
    global cursor

    database = get_database()

    if cursor is None:
        cursor = database.cursor()

    return cursor


def save_memory(content, category="conversation", importance=5):
    sql = """
    INSERT INTO memories (category, content, importance)
    VALUES (%s, %s, %s)
    """

    database = get_database()
    active_cursor = get_cursor()

    active_cursor.execute(sql, (category, content, importance))
    database.commit()


def recall_memories(limit=DEFAULT_MEMORY_LIMIT):
    active_cursor = get_cursor()

    active_cursor.execute(
        """
        SELECT content
        FROM memories
        ORDER BY importance DESC
        LIMIT %s
        """,
        (limit,),
    )

    return "\n".join(memory[0] for memory in active_cursor.fetchall())


def check_mysql_connection():
    try:
        get_database()
        return True, "MySQL reachable."
    except MySQLError as error:
        return False, f"MySQL is not reachable: {error}"


def check_memories_table():
    try:
        active_cursor = get_cursor()
        active_cursor.execute("SHOW TABLES LIKE %s", ("memories",))

        if active_cursor.fetchone():
            return True, "memories table exists."

        return False, "memories table does not exist in jarvis_memory."
    except MySQLError as error:
        return False, f"Could not check memories table: {error}"


def check_ollama_running():
    try:
        ollama.list()
        return True, "Ollama is running."
    except Exception as error:
        return False, f"Ollama is not running or not reachable: {error}"


def _model_name(model):
    if isinstance(model, dict):
        return model.get("name") or model.get("model") or ""

    return getattr(model, "model", None) or getattr(model, "name", "")


def check_jarvis_model_available():
    try:
        response = ollama.list()
        models = response.get("models", []) if isinstance(response, dict) else getattr(response, "models", [])
        model_names = [_model_name(model) for model in models]

        if any(name == MODEL_NAME or name.startswith(f"{MODEL_NAME}:") for name in model_names):
            return True, f"{MODEL_NAME} model is available."

        available_models = ", ".join(name for name in model_names if name) or "none"
        return False, f"{MODEL_NAME} model is not available. Installed models: {available_models}"
    except Exception as error:
        return False, f"Could not check Ollama models: {error}"


def run_startup_checks():
    checks = [
        ("MySQL connection", check_mysql_connection),
        ("memories table", check_memories_table),
        ("Ollama server", check_ollama_running),
        ("jarvis model", check_jarvis_model_available),
    ]

    results = []

    for name, check in checks:
        passed, message = check()
        results.append(
            {
                "name": name,
                "passed": passed,
                "message": message,
            }
        )

    return results


def startup_checks_passed(results):
    return all(result["passed"] for result in results)


def format_startup_check_report(results):
    lines = []

    for result in results:
        status = "OK" if result["passed"] else "FAILED"
        lines.append(f"{status}: {result['name']} - {result['message']}")

    return "\n".join(lines)


def build_prompt(user_input, memory_context):
    return f"""
Relevant memories about Edwin:
{memory_context}

User:
{user_input}
"""


def should_save_memory(user_input):
    return "remember" in user_input.lower()


def ask_jarvis(user_input):
    memory_context = recall_memories()
    full_prompt = build_prompt(user_input, memory_context)

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": full_prompt,
            }
        ],
    )

    reply = response["message"]["content"]

    if should_save_memory(user_input):
        save_memory(user_input, category="user_memory", importance=7)

    return reply


def stream_jarvis_response(user_input):
    memory_context = recall_memories()
    full_prompt = build_prompt(user_input, memory_context)

    stream = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": full_prompt,
            }
        ],
        stream=True,
    )

    for chunk in stream:
        content = chunk["message"]["content"]

        if content:
            yield content

    if should_save_memory(user_input):
        save_memory(user_input, category="user_memory", importance=7)


def run_cli():
    print("JARVIS memory system online.")

    while True:
        user_input = input("\nEdwin: ")

        if user_input.lower() == "exit":
            break

        reply = ask_jarvis(user_input)
        print(f"\nJARVIS: {reply}")

        if should_save_memory(user_input):
            print("\n[Memory Stored]")
