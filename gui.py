import subprocess
import math
import os
import random
import time
from tkinter import Canvas, PhotoImage
from pathlib import Path

# Force CPU mode
os.environ["OLLAMA_NO_GPU"] = "1"

# Start Ollama server silently
subprocess.Popen(
    ["ollama", "serve"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

time.sleep(2)

from backend.brain import (
    format_startup_check_report,
    run_startup_checks,
    startup_checks_passed,
    stream_jarvis_response,
)
import customtkinter as ctk
import threading
import re

try:
    from PIL import Image
except ImportError:
    Image = None

THEME = {
    "app": "#050d1a",
    "panel": "#0a1628",
    "panel_alt": "#0d1e35",
    "field": "#071220",
    "border": "#00d9ff",
    "border_soft": "#1a4c68",
    "text": "#e0f7ff",
    "muted": "#6a9fb8",
    "accent": "#00d9ff",
    "accent_alt": "#00ffea",
    "success": "#00ff9f",
    "error": "#ff5b6b",
}

ASSET_DIR = Path(__file__).resolve().parent / "assets"
MATRIX_CHARS = "01ABCDEFGHIJKLMNOPQRSTUVWXYZ"
MATRIX_FONT_SIZE = 16
MATRIX_HEIGHT = 86
MATRIX_SPEED_MS = 50
CORE_HEIGHT = 230
CORE_SPEED_MS = 33

assistant_awake = False
waking_up = False
startup_results = []

# =========================
# WINDOW SETUP
# =========================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()

app.title("JARVIS")
app.geometry("1000x700")
app.minsize(760, 560)
app.configure(fg_color=THEME["app"])

app_icon = None

if (ASSET_DIR / "jarvis_icon.png").exists():
    try:
        app_icon = PhotoImage(file=ASSET_DIR / "jarvis_icon.png")
        app.iconphoto(False, app_icon)
    except Exception:
        app_icon = None

# =========================
# LAYOUT
# =========================

shell = ctk.CTkFrame(
    app,
    fg_color=THEME["app"],
    corner_radius=0
)

shell.pack(fill="both", expand=True, padx=24, pady=20)

header = ctk.CTkFrame(
    shell,
    fg_color=THEME["panel"],
    border_color=THEME["border_soft"],
    border_width=1,
    corner_radius=8
)

header.pack(fill="x", pady=(0, 14))
header.grid_columnconfigure(1, weight=1)

if Image is not None and (ASSET_DIR / "jarvis_icon.png").exists():
    jarvis_icon = ctk.CTkImage(
        light_image=Image.open(ASSET_DIR / "jarvis_icon.png"),
        dark_image=Image.open(ASSET_DIR / "jarvis_icon.png"),
        size=(42, 42)
    )
else:
    jarvis_icon = None

icon_label = ctk.CTkLabel(
    header,
    image=jarvis_icon,
    text="" if jarvis_icon else "J",
    width=54,
    font=("Consolas", 24, "bold"),
    text_color=THEME["accent"]
)

icon_label.grid(row=0, column=0, rowspan=2, padx=(14, 8), pady=12)

title = ctk.CTkLabel(
    header,
    text="JARVIS",
    font=("Consolas", 30, "bold"),
    text_color=THEME["accent"]
)

title.grid(row=0, column=1, sticky="w", pady=(12, 0))

subtitle = ctk.CTkLabel(
    header,
    text="Awaiting wake phrase",
    font=("Consolas", 13),
    text_color=THEME["muted"]
)

subtitle.grid(row=1, column=1, sticky="w", pady=(0, 12))

status_pill = ctk.CTkLabel(
    header,
    text="SYSTEM OFFLINE",
    font=("Consolas", 12, "bold"),
    text_color=THEME["text"],
    fg_color=THEME["panel_alt"],
    corner_radius=6,
    padx=12,
    pady=6
)

status_pill.grid(row=0, column=2, rowspan=2, padx=14, pady=12)

# =========================
# RESPONSE ACTIVITY EFFECT
# =========================

matrix_frame = ctk.CTkFrame(
    shell,
    fg_color=THEME["field"],
    border_color=THEME["border_soft"],
    border_width=1,
    corner_radius=8,
    height=MATRIX_HEIGHT
)

matrix_canvas = Canvas(
    matrix_frame,
    height=MATRIX_HEIGHT,
    bg=THEME["field"],
    highlightthickness=0
)

matrix_canvas.pack(fill="both", expand=True, padx=1, pady=1)

matrix_drops = []
matrix_after_id = None
matrix_running = False

# =========================
# IDLE CORE EFFECT
# =========================

core_frame = ctk.CTkFrame(
    shell,
    fg_color=THEME["field"],
    border_color=THEME["border_soft"],
    border_width=1,
    corner_radius=8,
    height=CORE_HEIGHT
)

core_canvas = Canvas(
    core_frame,
    height=CORE_HEIGHT,
    bg=THEME["field"],
    highlightthickness=0
)

core_canvas.pack(fill="both", expand=True, padx=1, pady=1)

core_after_id = None
core_angle = 0
core_running = False

# =========================
# CHAT DISPLAY
# =========================

chat_box = ctk.CTkTextbox(
    shell,
    font=("Consolas", 15)
)

chat_box.configure(
    fg_color=THEME["field"],
    text_color=THEME["text"],
    border_color=THEME["border_soft"],
    border_width=1,
    corner_radius=8,
    scrollbar_button_color=THEME["panel_alt"],
    scrollbar_button_hover_color=THEME["accent"]
)

chat_box.pack(fill="both", expand=True)

chat_box.insert("end", "JARVIS core offline.\n")
chat_box.insert("end", "Type \"Wake up\" to initialize systems.\n\n")

# =========================
# INPUT FRAME
# =========================

input_frame = ctk.CTkFrame(
    shell,
    fg_color=THEME["panel"],
    border_color=THEME["border_soft"],
    border_width=1,
    corner_radius=8
)

input_frame.pack(fill="x", pady=(14, 0))
input_frame.grid_columnconfigure(0, weight=1)

# =========================
# USER INPUT
# =========================

user_input = ctk.CTkEntry(
    input_frame,
    height=44,
    font=("Consolas", 15),
    fg_color=THEME["panel_alt"],
    border_color=THEME["border_soft"],
    text_color=THEME["text"],
    placeholder_text='Type "Wake up" to initialize JARVIS...',
    placeholder_text_color=THEME["muted"]
)

user_input.grid(row=0, column=0, sticky="ew", padx=(12, 10), pady=12)

footer = ctk.CTkLabel(
    shell,
    text="Offline | Awaiting wake phrase",
    font=("Consolas", 11),
    text_color=THEME["muted"]
)

footer.pack(anchor="e", pady=(8, 0))

# =========================
# SEND FUNCTION
# =========================

def append_chat_text(text):
    chat_box.insert("end", text)
    chat_box.see("end")


def set_input_enabled(enabled):
    state = "normal" if enabled else "disabled"
    user_input.configure(state=state)
    send_button.configure(state=state)


def set_system_status(text, color, text_color="#001018"):
    status_pill.configure(text=text, fg_color=color, text_color=text_color)


def set_offline_state():
    set_system_status("SYSTEM OFFLINE", THEME["panel_alt"], THEME["text"])
    subtitle.configure(text="Awaiting wake phrase", text_color=THEME["muted"])
    footer.configure(text="Offline | Awaiting wake phrase")
    user_input.configure(placeholder_text='Type "Wake up" to initialize JARVIS...')


def set_waking_state():
    set_system_status("WAKING UP", THEME["accent"], "#001018")
    subtitle.configure(text="Initializing local systems", text_color=THEME["accent_alt"])
    footer.configure(text="Waking up | Running startup diagnostics")
    user_input.configure(placeholder_text="Initializing JARVIS...")


def set_online_state():
    set_system_status("SYSTEM ONLINE", THEME["success"], "#001018")
    subtitle.configure(text="Local assistant interface", text_color=THEME["muted"])
    footer.configure(text="Online | Ollama local model | MySQL memory core")
    user_input.configure(placeholder_text="Transmit message to JARVIS...")


def append_from_worker(text):
    app.after(0, append_chat_text, text)


def draw_core_ring(center_x, center_y, radius, width, offset, speed, color, dash=None):
    start = (core_angle * speed + offset) % 360

    core_canvas.create_arc(
        center_x - radius,
        center_y - radius,
        center_x + radius,
        center_y + radius,
        start=start,
        extent=300,
        style="arc",
        outline=color,
        width=width,
        dash=dash
    )


def draw_core_pulse(center_x, center_y, radius, thickness):
    pulse = math.sin(time.time() * 2) * 5

    core_canvas.create_oval(
        center_x - radius - pulse,
        center_y - radius - pulse,
        center_x + radius + pulse,
        center_y + radius + pulse,
        outline="#7ffcff",
        width=thickness
    )


def draw_core_dots(center_x, center_y, radius, count, speed):
    for index in range(count):
        angle = math.radians((360 / count) * index + core_angle * speed)
        x = center_x + math.cos(angle) * radius
        y = center_y + math.sin(angle) * radius
        size = 3

        core_canvas.create_oval(
            x - size,
            y - size,
            x + size,
            y + size,
            fill=THEME["accent"],
            outline=""
        )


def draw_core_scanlines(width, height):
    for y in range(0, height, 4):
        core_canvas.create_line(
            0,
            y,
            width,
            y,
            fill="#081522"
        )


def draw_idle_core():
    global core_after_id
    global core_angle

    if not core_running:
        return

    width = max(core_canvas.winfo_width(), 700)
    height = max(core_canvas.winfo_height(), CORE_HEIGHT)
    center_x = width // 2
    center_y = height // 2
    scale = min(width / 700, height / 260)

    core_canvas.delete("all")
    draw_core_scanlines(width, height)

    core_canvas.create_oval(
        center_x - int(215 * scale),
        center_y - int(95 * scale),
        center_x + int(215 * scale),
        center_y + int(95 * scale),
        outline="#0a3d62",
        width=2
    )

    draw_core_ring(center_x, center_y, int(96 * scale), 3, 0, 1.0, THEME["accent"])
    draw_core_ring(center_x, center_y, int(76 * scale), 2, 90, -1.5, "#7ffcff", dash=(4, 8))
    draw_core_ring(center_x, center_y, int(58 * scale), 3, 180, 0.7, THEME["accent"])
    draw_core_ring(center_x, center_y, int(42 * scale), 2, 270, -2.2, "#7ffcff")
    draw_core_pulse(center_x, center_y, int(30 * scale), 3)

    core_canvas.create_oval(
        center_x - int(50 * scale),
        center_y - int(50 * scale),
        center_x + int(50 * scale),
        center_y + int(50 * scale),
        outline=THEME["accent"],
        width=2
    )

    core_canvas.create_oval(
        center_x - int(38 * scale),
        center_y - int(38 * scale),
        center_x + int(38 * scale),
        center_y + int(38 * scale),
        outline="#7ffcff",
        width=1
    )

    draw_core_dots(center_x, center_y, int(108 * scale), 24, 2)
    draw_core_dots(center_x, center_y, int(66 * scale), 12, -1.4)

    core_canvas.create_text(
        center_x,
        center_y,
        text="J.A.R.V.I.S",
        fill="#7ffcff",
        font=("Consolas", max(14, int(20 * scale)), "bold")
    )

    core_angle += 2
    core_after_id = app.after(CORE_SPEED_MS, draw_idle_core)


def start_idle_core():
    global core_running

    if core_running:
        return

    core_running = True
    core_frame.pack(fill="x", pady=(0, 14), before=chat_box)
    draw_idle_core()


def stop_idle_core():
    global core_after_id
    global core_running

    core_running = False

    if core_after_id is not None:
        app.after_cancel(core_after_id)
        core_after_id = None

    core_canvas.delete("all")
    core_frame.pack_forget()


def reset_matrix_drops():
    global matrix_drops

    width = max(matrix_canvas.winfo_width(), 900)
    columns = max(1, width // MATRIX_FONT_SIZE)
    matrix_drops = [
        random.randint(0, MATRIX_HEIGHT // MATRIX_FONT_SIZE)
        for _ in range(columns)
    ]


def draw_matrix():
    global matrix_after_id

    if not matrix_running:
        return

    width = max(matrix_canvas.winfo_width(), 900)
    height = max(matrix_canvas.winfo_height(), MATRIX_HEIGHT)
    columns = max(1, width // MATRIX_FONT_SIZE)

    if len(matrix_drops) != columns:
        reset_matrix_drops()

    matrix_canvas.create_rectangle(
        0,
        0,
        width,
        height,
        fill=THEME["field"],
        outline=THEME["field"],
        stipple="gray25"
    )

    for index, drop in enumerate(matrix_drops):
        x = index * MATRIX_FONT_SIZE
        y = drop * MATRIX_FONT_SIZE

        matrix_canvas.create_text(
            x,
            y,
            text=random.choice(MATRIX_CHARS),
            fill="#7fdfff",
            font=("Consolas", MATRIX_FONT_SIZE, "bold"),
            anchor="nw"
        )

        matrix_canvas.create_text(
            x,
            y - MATRIX_FONT_SIZE,
            text=random.choice(MATRIX_CHARS),
            fill=THEME["accent"],
            font=("Consolas", MATRIX_FONT_SIZE),
            anchor="nw"
        )

        if y > height and random.random() > 0.975:
            matrix_drops[index] = 0
        else:
            matrix_drops[index] += 1

    matrix_after_id = app.after(MATRIX_SPEED_MS, draw_matrix)


def start_matrix_effect():
    global matrix_running

    if matrix_running:
        return

    stop_idle_core()
    matrix_running = True
    reset_matrix_drops()
    matrix_frame.pack(fill="x", pady=(0, 14), before=chat_box)
    draw_matrix()


def stop_matrix_effect():
    global matrix_after_id
    global matrix_running

    matrix_running = False

    if matrix_after_id is not None:
        app.after_cancel(matrix_after_id)
        matrix_after_id = None

    matrix_canvas.delete("all")
    matrix_frame.pack_forget()


def finish_response():
    stop_matrix_effect()
    start_idle_core()
    append_chat_text("\n\n")
    set_input_enabled(True)
    user_input.focus()


def append_error(error):
    stop_matrix_effect()
    start_idle_core()
    append_chat_text(f"\n\nJARVIS error: {error}\n\n")
    set_input_enabled(True)
    user_input.focus()


def finish_wake_sequence(results):
    global assistant_awake
    global startup_results
    global waking_up

    startup_results = results
    stop_matrix_effect()

    if startup_checks_passed(results):
        assistant_awake = True
        waking_up = False
        set_online_state()
        append_chat_text("\n")
        append_chat_text("JARVIS: Systems online.\n")
        append_chat_text(format_startup_check_report(results) + "\n\n")
        start_idle_core()
    else:
        assistant_awake = False
        waking_up = False
        set_offline_state()
        append_chat_text("\n")
        append_chat_text("JARVIS: Startup diagnostics failed.\n")
        append_chat_text(format_startup_check_report(results) + "\n\n")

    set_input_enabled(True)
    user_input.focus()


def run_wake_checks():
    import time

    time.sleep(1.5)
    results = run_startup_checks()
    app.after(0, finish_wake_sequence, results)


def wake_up_jarvis():
    global waking_up

    if waking_up:
        return

    waking_up = True
    stop_idle_core()
    set_waking_state()
    append_chat_text("JARVIS: Wake phrase accepted.\n")
    append_chat_text("JARVIS: Initializing systems")
    set_input_enabled(False)
    start_matrix_effect()

    thread = threading.Thread(
        target=run_wake_checks,
        daemon=True,
    )

    thread.start()


def stream_words(message):
    import time

    buffer = ""

    try:
        for chunk in stream_jarvis_response(message):
            buffer += chunk

            while True:
                match = re.search(r"\s+", buffer)

                if match is None:
                    break

                word = buffer[:match.end()]
                buffer = buffer[match.end():]

                append_from_worker(word)
                time.sleep(0.04)

        if buffer:
            append_from_worker(buffer)

        app.after(0, finish_response)
    except Exception as error:
        app.after(0, append_error, str(error))


def send_message():

    message = user_input.get()

    if message.strip() == "":
        return

    # Display user message immediately
    append_chat_text(f"Edwin: {message}\n\n")

    # Clear input
    user_input.delete(0, "end")

    if not assistant_awake:
        if message.strip().lower() == "wake up":
            wake_up_jarvis()
        elif waking_up:
            append_chat_text("JARVIS: Initialization already in progress.\n\n")
        else:
            append_chat_text("JARVIS: Core offline. Say \"Wake up\" to initialize systems.\n\n")

        return

    append_chat_text("JARVIS: ")

    set_input_enabled(False)
    start_matrix_effect()

    # Stream AI response in a separate thread
    thread = threading.Thread(
        target=stream_words,
        args=(message,),
        daemon=True,
    )

    thread.start()

# =========================
# SEND BUTTON
# =========================

send_button = ctk.CTkButton(
    input_frame,
    text="Send",
    command=send_message,
    width=116,
    height=44,
    fg_color=THEME["accent"],
    hover_color="#4d9fff",
    text_color="#001018",
    font=("Consolas", 14, "bold"),
    corner_radius=7
)

send_button.grid(row=0, column=1, padx=(0, 12), pady=12)

user_input.bind("<Return>", lambda event: send_message())
user_input.focus()


def close_app():
    stop_matrix_effect()
    stop_idle_core()
    app.destroy()


app.protocol("WM_DELETE_WINDOW", close_app)


def pulse_title(step=0):
    colors = [THEME["accent"], THEME["accent_alt"], "#7ab8ff", THEME["accent_alt"]]
    title.configure(text_color=colors[step % len(colors)])
    app.after(900, pulse_title, step + 1)


pulse_title()
set_offline_state()

# =========================
# RUN APP
# =========================

app.mainloop()
