import sys, os
sys.path = [p for p in sys.path if p not in ('', '.', os.getcwd())]
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

import tkinter as tk
import cv2
import sqlite3
from datetime import datetime
from PIL import Image, ImageTk
from tkinter import messagebox

# =====================================================
# PORTABLE PATHS
# =====================================================
DB_FOLDER          = os.path.join(PROJECT, "data", "DB")
SUBJECT_BASE_PATH  = os.path.join(PROJECT, "data", "subjects")
VIDEO_PATH         = os.path.join(PROJECT, "text_to_sign", "videos")

os.makedirs(DB_FOLDER, exist_ok=True)

PERFORMANCE_DB     = os.path.join(DB_FOLDER, "performance.db")
LESSON_PROGRESS_DB = os.path.join(DB_FOLDER, "lesson_progress.db")

# =====================================================
# THEME  (matches auth.py + teacher_dashboard.py)
# =====================================================
DARK_BG       = "#080d18"
CARD_BG       = "#0f1829"
CARD_BORDER   = "#1a2845"
SIDEBAR_BG    = "#07111f"
INPUT_BG      = "#0c1422"
HOVER_BG      = "#162035"
ACCENT_BLUE   = "#1e6fff"
ACCENT_CYAN   = "#00d4ff"
ACCENT_GREEN  = "#00c896"
ACCENT_RED    = "#ff4d6d"
ACCENT_ORANGE = "#f59e0b"
ACCENT_PURPLE = "#7b5ea7"
TEXT_PRIMARY  = "#dce8ff"
TEXT_SEC      = "#7a9bc4"
TEXT_MUTED    = "#3d5578"
TEXT_DIM      = "#4a6580"

FONT_TITLE  = ("Georgia", 20, "bold")
FONT_SUB    = ("Georgia", 10)
FONT_LABEL  = ("Georgia", 10, "bold")
FONT_BODY   = ("Courier New", 10)
FONT_SMALL  = ("Courier New", 9)

VIDEO_WIDTH  = 300
VIDEO_HEIGHT = 480

# =====================================================
# DATABASE SETUP  (unchanged)
# =====================================================
def init_databases():
    with sqlite3.connect(PERFORMANCE_DB) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, subject TEXT, lesson_name TEXT,
            accuracy REAL, timestamp TEXT)""")
    with sqlite3.connect(LESSON_PROGRESS_DB) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS lesson_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, subject TEXT, lesson_name TEXT,
            progress REAL, timestamp TEXT)""")


def save_progress(user_id, subject, lesson_name, value):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(PERFORMANCE_DB) as conn:
        conn.execute(
            "INSERT INTO performance (user_id,subject,lesson_name,accuracy,timestamp) VALUES (?,?,?,?,?)",
            (user_id, subject, lesson_name, value, now))
    with sqlite3.connect(LESSON_PROGRESS_DB) as conn:
        conn.execute(
            "INSERT INTO lesson_progress (user_id,subject,lesson_name,progress,timestamp) VALUES (?,?,?,?,?)",
            (user_id, subject, lesson_name, value, now))


init_databases()

# =====================================================
# HELPERS
# =====================================================
def load_subjects():
    if not os.path.exists(SUBJECT_BASE_PATH):
        return {}
    folders = [f for f in os.listdir(SUBJECT_BASE_PATH)
               if os.path.isdir(os.path.join(SUBJECT_BASE_PATH, f))]
    colors = [ACCENT_BLUE, ACCENT_GREEN, ACCENT_PURPLE, ACCENT_CYAN, ACCENT_ORANGE]
    return {folder: colors[i % len(colors)]
            for i, folder in enumerate(sorted(folders))}


def dark_btn(parent, text, command, color=ACCENT_BLUE, width=None):
    kw = dict(text=text, command=command,
              bg=color, fg=TEXT_PRIMARY,
              activebackground=HOVER_BG, activeforeground=ACCENT_CYAN,
              font=("Segoe UI", 10, "bold"),
              bd=0, padx=16, pady=9, cursor="hand2", relief="flat")
    if width:
        kw["width"] = width
    b = tk.Button(parent, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=HOVER_BG, fg=ACCENT_CYAN))
    b.bind("<Leave>", lambda e: b.config(bg=color, fg=TEXT_PRIMARY))
    return b


def page_header(parent, title, subtitle=""):
    hdr = tk.Frame(parent, bg=DARK_BG)
    hdr.pack(fill="x", padx=22, pady=(18, 4))
    tk.Label(hdr, text=title, bg=DARK_BG, fg=TEXT_PRIMARY,
             font=FONT_TITLE).pack(anchor="w")
    if subtitle:
        tk.Label(hdr, text=subtitle, bg=DARK_BG, fg=TEXT_SEC,
                 font=FONT_SMALL).pack(anchor="w", pady=(2, 0))
    tk.Frame(parent, bg=CARD_BORDER, height=1).pack(fill="x", padx=22, pady=(6, 0))


def card_frame(parent, expand=False):
    """Bordered dark card."""
    outer = tk.Frame(parent, bg=CARD_BORDER, padx=1, pady=1)
    if expand:
        outer.pack(fill="both", expand=True, padx=18, pady=10)
    else:
        outer.pack(fill="x", padx=18, pady=10)
    inner = tk.Frame(outer, bg=CARD_BG, padx=20, pady=16)
    inner.pack(fill="both", expand=expand)
    return inner


# =====================================================
# MAIN PAGE
# =====================================================
def page(parent, user_id):
    frame = tk.Frame(parent, bg=DARK_BG)
    frame.pack(fill="both", expand=True)

    def clear():
        for w in frame.winfo_children():
            w.destroy()

    # =====================================================
    # ISL PLAYBACK
    # =====================================================
    def play_text_as_isl(text, subject, lesson_name):
        clear()

        page_header(frame, "\U0001f590  ISL Playback",
                    f"Subject: {subject}  \u00b7  Lesson: {lesson_name}")

        # ── main three-column layout ──────────────────────────────
        body = tk.Frame(frame, bg=DARK_BG)
        body.pack(fill="both", expand=True, padx=18, pady=8)
        body.grid_columnconfigure(0, weight=0)
        body.grid_columnconfigure(1, weight=1)
        body.grid_columnconfigure(2, weight=0)

        # ── LEFT: controls ────────────────────────────────────────
        left_outer = tk.Frame(body, bg=CARD_BORDER, padx=1, pady=1)
        left_outer.grid(row=0, column=0, sticky="n", padx=(0, 10))
        left = tk.Frame(left_outer, bg=CARD_BG, padx=16, pady=20)
        left.pack()

        tk.Label(left, text="Controls", bg=CARD_BG, fg=TEXT_SEC,
                 font=FONT_LABEL).pack(pady=(0, 12))

        # ── CENTER: video ─────────────────────────────────────────
        vid_outer = tk.Frame(body, bg=CARD_BORDER, padx=1, pady=1)
        vid_outer.grid(row=0, column=1, sticky="nsew", padx=4)
        vid_inner = tk.Frame(vid_outer, bg="#000000",
                             width=VIDEO_WIDTH, height=VIDEO_HEIGHT)
        vid_inner.pack(fill="both", expand=True)
        vid_inner.pack_propagate(False)
        video_label = tk.Label(vid_inner, bg="#000000")
        video_label.pack(fill="both", expand=True)

        # ── RIGHT: text display ───────────────────────────────────
        right_outer = tk.Frame(body, bg=CARD_BORDER, padx=1, pady=1)
        right_outer.grid(row=0, column=2, sticky="ns", padx=(10, 0))
        right = tk.Frame(right_outer, bg=CARD_BG, padx=10, pady=12, width=240)
        right.pack(fill="both", expand=True)
        right.pack_propagate(False)

        tk.Label(right, text="Lesson Text", bg=CARD_BG, fg=TEXT_SEC,
                 font=FONT_LABEL).pack(anchor="w", pady=(0, 6))

        sb = tk.Scrollbar(right, bg=CARD_BG, troughcolor=DARK_BG)
        sb.pack(side="right", fill="y")
        text_widget = tk.Text(right, wrap="word", font=FONT_BODY,
                              yscrollcommand=sb.set,
                              bg=INPUT_BG, fg=TEXT_PRIMARY,
                              selectbackground=ACCENT_BLUE,
                              insertbackground=ACCENT_CYAN,
                              relief="flat", padx=8, pady=8)
        text_widget.pack(fill="both", expand=True)
        sb.config(command=text_widget.yview)

        text_upper = text.upper()
        text_widget.insert("1.0", text_upper)
        text_widget.config(state="disabled")

        # ── PROGRESS BAR ──────────────────────────────────────────
        prog_outer = tk.Frame(frame, bg=CARD_BORDER, padx=1, pady=1)
        prog_outer.pack(fill="x", padx=18, pady=(6, 12))
        prog_inner = tk.Frame(prog_outer, bg=CARD_BG, padx=16, pady=10)
        prog_inner.pack(fill="x")

        pbar_row = tk.Frame(prog_inner, bg=CARD_BG)
        pbar_row.pack(fill="x")
        tk.Label(pbar_row, text="Progress", bg=CARD_BG, fg=TEXT_SEC,
                 font=FONT_LABEL).pack(side="left")
        pct_var = tk.StringVar(value="0.00%")
        tk.Label(pbar_row, textvariable=pct_var, bg=CARD_BG,
                 fg=ACCENT_CYAN, font=FONT_LABEL).pack(side="right")

        prog_canvas = tk.Canvas(prog_inner, height=10,
                                bg=INPUT_BG, highlightthickness=0)
        prog_canvas.pack(fill="x", pady=(6, 0))
        prog_fill = prog_canvas.create_rectangle(0, 0, 0, 10,
                                                 fill=ACCENT_GREEN, width=0)

        valid_chars   = [c for c in text_upper if c.isalnum()]
        total_letters = len(valid_chars)

        state = {
            "current_index":  0,
            "played_letters": 0,
            "is_paused":      False,
            "cap":            None,
            "is_playing":     False,
        }

        def current_pct():
            return (state["played_letters"] / total_letters * 100
                    if total_letters else 0)

        def update_progress():
            pct = current_pct()
            prog_canvas.update_idletasks()
            w = prog_canvas.winfo_width()
            fw = (pct / 100) * w
            prog_canvas.coords(prog_fill, 0, 0, fw, 10)
            pct_var.set(f"{pct:.2f}%")

        def highlight_letter(index):
            text_widget.config(state="normal")
            text_widget.tag_remove("highlight", "1.0", "end")
            pos = f"1.0+{index}c"
            text_widget.tag_add("highlight", pos, f"{pos}+1c")
            text_widget.tag_config("highlight",
                                   background=ACCENT_BLUE,
                                   foreground="white")
            text_widget.see(pos)
            text_widget.config(state="disabled")

        def play_next():
            if state["current_index"] < len(text_upper) - 1:
                state["current_index"] += 1
                play_letter()
            else:
                # Lesson fully completed — save final 100%
                save_progress(user_id, subject, lesson_name, 100.0)
                messagebox.showinfo("Completed", "Lesson Completed!")

        def play_letter():
            idx    = state["current_index"]
            if idx >= len(text_upper):
                return
            letter = text_upper[idx]
            if not letter.isalnum():
                play_next()
                return

            video_file = os.path.join(VIDEO_PATH, f"{letter}.mp4")
            if not os.path.exists(video_file):
                play_next()
                return

            highlight_letter(idx)
            if state["cap"]:
                state["cap"].release()

            state["cap"]        = cv2.VideoCapture(video_file)
            state["is_playing"] = True
            state["played_letters"] += 1
            update_progress()

            # Save partial progress after every letter played
            pct = current_pct()
            save_progress(user_id, subject, lesson_name, round(pct, 2))

            def stream():
                if state["is_paused"]:
                    video_label.after(100, stream)
                    return
                cap = state["cap"]
                if cap is None:
                    return
                ret, frame_img = cap.read()
                if ret:
                    frame_img = cv2.resize(frame_img, (VIDEO_WIDTH, VIDEO_HEIGHT))
                    frame_img = cv2.cvtColor(frame_img, cv2.COLOR_BGR2RGB)
                    img = ImageTk.PhotoImage(Image.fromarray(frame_img))
                    video_label.imgtk = img
                    video_label.configure(image=img)
                    video_label.after(30, stream)
                else:
                    cap.release()
                    state["cap"]        = None
                    state["is_playing"] = False
                    play_next()

            stream()

        def toggle():
            state["is_paused"] = not state["is_paused"]
            if not state["is_paused"] and not state["is_playing"]:
                play_letter()

        def next_letter():
            if state["cap"]:
                state["cap"].release()
                state["cap"] = None
            if state["current_index"] < len(text_upper) - 1:
                state["current_index"] += 1
            play_letter()

        def previous_letter():
            if state["cap"]:
                state["cap"].release()
                state["cap"] = None
            if state["current_index"] > 0:
                state["current_index"] -= 1
            play_letter()

        # ── Manual Save Progress handler ──────────────────────────
        def manual_save_progress():
            pct = current_pct()
            if pct <= 0:
                messagebox.showinfo(
                    "Save Progress",
                    "No progress to save yet.\nPlay at least one letter first.")
                return
            save_progress(user_id, subject, lesson_name, round(pct, 2))
            messagebox.showinfo(
                "Progress Saved",
                f"Progress saved: {pct:.1f}%")

        # ── Control buttons in left panel ─────────────────────────
        for txt, cmd, col in [
            ("\u25b6  Play / Pause",      toggle,                ACCENT_GREEN),
            ("\u23ee  Previous",           previous_letter,       ACCENT_PURPLE),
            ("\u23ed  Next",               next_letter,           ACCENT_BLUE),
            ("\U0001f4be  Save Progress",  manual_save_progress,  ACCENT_ORANGE),
            ("\u2b05  Back",               lambda: show_lessons(subject), ACCENT_RED),
        ]:
            b = dark_btn(left, txt, cmd, col, width=16)
            b.pack(fill="x", pady=6)

        play_letter()

    # =====================================================
    # LESSON LIST
    # =====================================================
    def show_lessons(subject):
        clear()
        page_header(frame, f"\U0001f4da  {subject}",
                    "Select a lesson to begin ISL playback")

        body = tk.Frame(frame, bg=DARK_BG)
        body.pack(fill="both", expand=True)

        inner = card_frame(body, expand=True)

        subject_path = os.path.join(SUBJECT_BASE_PATH, subject)
        if not os.path.exists(subject_path):
            tk.Label(inner, text="Subject folder not found.",
                     bg=CARD_BG, fg=ACCENT_RED,
                     font=FONT_BODY).pack(pady=20)
            dark_btn(inner, "\u2b05  Go Back", show_subjects, ACCENT_RED).pack(pady=10)
            return

        files = [f for f in os.listdir(subject_path) if f.endswith(".txt")]

        if not files:
            tk.Label(inner, text="No lessons found in this subject.",
                     bg=CARD_BG, fg=TEXT_SEC,
                     font=FONT_BODY).pack(pady=20)
        else:
            lesson_grid = tk.Frame(inner, bg=CARD_BG)
            lesson_grid.pack(fill="both", expand=True)

            for i, file in enumerate(sorted(files)):
                full_path = os.path.join(subject_path, file)

                def open_lesson(p=full_path, f=file):
                    with open(p, "r", encoding="utf-8") as fh:
                        content = fh.read()
                    play_text_as_isl(content, subject, f)

                row = tk.Frame(lesson_grid, bg=CARD_BORDER, padx=1, pady=1)
                row.pack(fill="x", pady=5)
                row_inner = tk.Frame(row, bg=HOVER_BG, padx=16, pady=12)
                row_inner.pack(fill="both")

                tk.Label(row_inner, text=f"\U0001f4c4  {file[:-4]}",
                         bg=HOVER_BG, fg=TEXT_PRIMARY,
                         font=("Georgia", 12, "bold"),
                         anchor="w").pack(side="left", fill="x", expand=True)

                open_btn = dark_btn(row_inner, "\u25b6  Open", open_lesson, ACCENT_BLUE)
                open_btn.pack(side="right")

        tk.Frame(inner, bg=CARD_BG, height=10).pack()
        dark_btn(inner, "\u2b05  Back to Subjects", show_subjects, ACCENT_RED).pack(anchor="w")

    # =====================================================
    # SUBJECT PAGE
    # =====================================================
    def show_subjects():
        clear()
        page_header(frame, "\U0001f4d8  Subjects",
                    "Choose a subject to explore lessons")

        body = tk.Frame(frame, bg=DARK_BG)
        body.pack(fill="both", expand=True)

        subjects = load_subjects()
        if not subjects:
            inner = card_frame(body)
            tk.Label(inner,
                     text="No subjects found.\nPlease add subjects in the Teacher Dashboard.",
                     bg=CARD_BG, fg=TEXT_SEC,
                     font=FONT_BODY, justify="center").pack(pady=20)
            return

        # Grid of subject cards
        grid_frame = tk.Frame(body, bg=DARK_BG)
        grid_frame.pack(padx=22, pady=12, fill="both", expand=True)

        cols = 3
        for i, (subject, color) in enumerate(subjects.items()):
            row_i = i // cols
            col_i = i % cols

            outer = tk.Frame(grid_frame, bg=CARD_BORDER, padx=1, pady=1)
            outer.grid(row=row_i, column=col_i, padx=10, pady=10, sticky="nsew")
            grid_frame.grid_columnconfigure(col_i, weight=1)

            inner = tk.Frame(outer, bg=CARD_BG, padx=20, pady=22)
            inner.pack(fill="both", expand=True)

            tk.Frame(inner, bg=color, height=3).pack(fill="x", pady=(0, 12))

            subj_path = os.path.join(SUBJECT_BASE_PATH, subject)
            count = len([f for f in os.listdir(subj_path)
                         if f.endswith(".txt")]) if os.path.exists(subj_path) else 0

            tk.Label(inner, text=subject,
                     bg=CARD_BG, fg=TEXT_PRIMARY,
                     font=("Georgia", 14, "bold"),
                     anchor="center").pack(fill="x")
            tk.Label(inner, text=f"{count} lesson{'s' if count != 1 else ''}",
                     bg=CARD_BG, fg=TEXT_SEC,
                     font=FONT_SMALL).pack(pady=(4, 14))

            b = tk.Button(inner, text="\u25b6  Start",
                          bg=color, fg="white",
                          activebackground=HOVER_BG,
                          activeforeground=ACCENT_CYAN,
                          font=("Segoe UI", 10, "bold"),
                          bd=0, padx=14, pady=7, cursor="hand2",
                          command=lambda s=subject: show_lessons(s))
            b.pack()
            b.bind("<Enter>", lambda e, btn=b, c=color: btn.config(bg=HOVER_BG))
            b.bind("<Leave>", lambda e, btn=b, c=color: btn.config(bg=c))

    show_subjects()
    return frame