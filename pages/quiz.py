import sys, os
sys.path = [p for p in sys.path if p not in ('', '.', os.getcwd())]
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

import tkinter as tk
import random
import cv2
import sqlite3
from datetime import datetime
from PIL import Image, ImageTk

# ============================
# PORTABLE PATHS
# ============================
VIDEO_PATH   = os.path.join(PROJECT, "text_to_sign", "videos")
QUIZ_DB_PATH = os.path.join(PROJECT, "data", "DB", "quiz.db")

VIDEO_WIDTH         = 300
VIDEO_HEIGHT        = 320
POINTS_PER_QUESTION = 10

WORD_LIST = ["APPLE", "DOG", "CAT", "BOOK", "WATER", "SCHOOL"]

# ============================
# THEME
# ============================
DARK_BG       = "#080d18"
CARD_BG       = "#0f1829"
CARD_BORDER   = "#1a2845"
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

FONT_TITLE = ("Georgia", 20, "bold")
FONT_LABEL = ("Georgia", 10, "bold")
FONT_BODY  = ("Courier New", 10)
FONT_SMALL = ("Courier New", 9)

# ============================
# DATABASE SETUP  (unchanged)
# ============================
def init_quiz_db():
    os.makedirs(os.path.dirname(QUIZ_DB_PATH), exist_ok=True)
    with sqlite3.connect(QUIZ_DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, level TEXT, score INTEGER,
                total_questions INTEGER, accuracy REAL, timestamp TEXT)""")
        conn.commit()


def save_quiz_result(user_id, level, score, total_questions):
    accuracy  = (score / (total_questions * POINTS_PER_QUESTION) * 100
                 if total_questions else 0.0)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(QUIZ_DB_PATH) as conn:
        conn.execute("""INSERT INTO quiz_performance
            (user_id,level,score,total_questions,accuracy,timestamp)
            VALUES (?,?,?,?,?,?)""",
            (user_id, level, score, total_questions, accuracy, timestamp))
        conn.commit()


init_quiz_db()

# ============================
# HELPERS
# ============================
def dark_btn(parent, text, command, color=ACCENT_BLUE, width=None):
    kw = dict(text=text, command=command,
              bg=color, fg=TEXT_PRIMARY,
              activebackground=HOVER_BG, activeforeground=ACCENT_CYAN,
              font=("Segoe UI", 10, "bold"),
              bd=0, padx=14, pady=8, cursor="hand2", relief="flat")
    if width:
        kw["width"] = width
    b = tk.Button(parent, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=HOVER_BG, fg=ACCENT_CYAN))
    b.bind("<Leave>", lambda e: b.config(bg=color, fg=TEXT_PRIMARY))
    return b


def card(parent, expand=False):
    outer = tk.Frame(parent, bg=CARD_BORDER, padx=1, pady=1)
    if expand:
        outer.pack(fill="both", expand=True, padx=18, pady=8)
    else:
        outer.pack(fill="x", padx=18, pady=8)
    inner = tk.Frame(outer, bg=CARD_BG, padx=18, pady=14)
    inner.pack(fill="both", expand=expand)
    return inner


# ============================
# QUIZ PAGE
# ============================
def page(parent, user_id):
    frame = tk.Frame(parent, bg=DARK_BG)
    frame.pack(fill="both", expand=True)

    # ── Header ───────────────────────────────────────────────
    hdr = tk.Frame(frame, bg=DARK_BG)
    hdr.pack(fill="x", padx=22, pady=(18, 4))
    tk.Label(hdr, text="\U0001f3af  Quiz & Practice",
             bg=DARK_BG, fg=TEXT_PRIMARY, font=FONT_TITLE).pack(anchor="w")
    tk.Label(hdr, text="Watch the ISL sign and choose the correct answer",
             bg=DARK_BG, fg=TEXT_SEC, font=FONT_SMALL).pack(anchor="w", pady=(2, 0))
    tk.Frame(frame, bg=CARD_BORDER, height=1).pack(fill="x", padx=22, pady=(6, 0))

    selected_level = tk.StringVar(value="level1")

    state = {
        "score":          0,
        "question_index": 0,
        "question_list":  [],
        "cap":            None,
    }

    # ── Main layout: left controls | center video | right options ──
    body = tk.Frame(frame, bg=DARK_BG)
    body.pack(fill="both", expand=True, padx=18, pady=10)
    body.grid_columnconfigure(0, weight=0)
    body.grid_columnconfigure(1, weight=1)
    body.grid_columnconfigure(2, weight=0)

    # LEFT — level + score
    left_outer = tk.Frame(body, bg=CARD_BORDER, padx=1, pady=1)
    left_outer.grid(row=0, column=0, sticky="n", padx=(0, 10))
    left = tk.Frame(left_outer, bg=CARD_BG, padx=18, pady=20)
    left.pack()

    tk.Label(left, text="Level", bg=CARD_BG, fg=TEXT_SEC,
             font=FONT_LABEL).pack(anchor="w", pady=(0, 8))

    for val, lbl in [("level1", "\U0001f524  A–Z, 0–9"),
                     ("level2", "\U0001f4dd  Words")]:
        rb = tk.Radiobutton(left, text=lbl, variable=selected_level, value=val,
                            bg=CARD_BG, fg=TEXT_PRIMARY,
                            selectcolor=ACCENT_BLUE,
                            activebackground=CARD_BG,
                            activeforeground=ACCENT_CYAN,
                            font=FONT_BODY)
        rb.pack(anchor="w", pady=3)

    tk.Frame(left, bg=CARD_BORDER, height=1).pack(fill="x", pady=14)

    tk.Label(left, text="Score", bg=CARD_BG, fg=TEXT_SEC,
             font=FONT_LABEL).pack(anchor="w")
    score_var = tk.StringVar(value="0")
    tk.Label(left, textvariable=score_var,
             bg=CARD_BG, fg=ACCENT_CYAN,
             font=("Georgia", 28, "bold")).pack(pady=(4, 14))

    tk.Frame(left, bg=CARD_BORDER, height=1).pack(fill="x", pady=(0, 14))

    result_var = tk.StringVar(value="")
    result_lbl = tk.Label(left, textvariable=result_var,
                          bg=CARD_BG, fg=ACCENT_GREEN,
                          font=("Segoe UI", 11, "bold"),
                          wraplength=160, justify="center")
    result_lbl.pack(pady=(0, 16))

    start_btn = dark_btn(left, "\u25b6  Start Quiz",
                         lambda: _start(), ACCENT_BLUE, width=16)
    start_btn.pack(fill="x", pady=4)

    # CENTER — video
    vid_outer = tk.Frame(body, bg=CARD_BORDER, padx=1, pady=1)
    vid_outer.grid(row=0, column=1, sticky="nsew", padx=6)
    vid_bg = tk.Frame(vid_outer, bg="#000000",
                      width=VIDEO_WIDTH, height=VIDEO_HEIGHT)
    vid_bg.pack(fill="both", expand=True)
    vid_bg.pack_propagate(False)
    video_label = tk.Label(vid_bg, bg="#000000")
    video_label.pack(fill="both", expand=True)

    # CENTER bottom — question counter
    qcount_var = tk.StringVar(value="")
    tk.Label(vid_outer, textvariable=qcount_var,
             bg=CARD_BG, fg=TEXT_SEC, font=FONT_SMALL).pack(pady=4)

    # RIGHT — answer options
    right_outer = tk.Frame(body, bg=CARD_BORDER, padx=1, pady=1)
    right_outer.grid(row=0, column=2, sticky="ns", padx=(10, 0))
    right = tk.Frame(right_outer, bg=CARD_BG, padx=16, pady=20, width=200)
    right.pack(fill="both", expand=True)
    right.pack_propagate(False)

    tk.Label(right, text="Choose Answer", bg=CARD_BG, fg=TEXT_SEC,
             font=FONT_LABEL).pack(pady=(0, 10))

    options_frame = tk.Frame(right, bg=CARD_BG)
    options_frame.pack(fill="both", expand=True)

    # ── VIDEO PLAYER ─────────────────────────────────────────
    def stop_video():
        if state["cap"]:
            state["cap"].release()
            state["cap"] = None
        video_label.config(image="")
        video_label.imgtk = None

    def play_video(path):
        stop_video()
        if not os.path.exists(path):
            result_var.set("Video not found!")
            result_lbl.config(fg=ACCENT_RED)
            return
        state["cap"] = cv2.VideoCapture(path)

        def stream():
            cap = state["cap"]
            if cap is None:
                return
            ret, frame_img = cap.read()
            if ret:
                frame_img = cv2.resize(frame_img, (VIDEO_WIDTH, VIDEO_HEIGHT))
                frame_img = cv2.cvtColor(frame_img, cv2.COLOR_BGR2RGB)
                img = ImageTk.PhotoImage(image=Image.fromarray(frame_img))
                video_label.imgtk = img
                video_label.configure(image=img)
                video_label.after(30, stream)
            else:
                cap.release()
                state["cap"] = None

        stream()

    def play_word(word):
        letters = list(word)
        idx_st  = {"i": 0}

        def next_letter():
            i = idx_st["i"]
            if i >= len(letters):
                return
            path = os.path.join(VIDEO_PATH, f"{letters[i]}.mp4")
            if not os.path.exists(path):
                idx_st["i"] += 1
                next_letter()
                return
            stop_video()
            local_cap = cv2.VideoCapture(path)

            def stream():
                ret, frame_img = local_cap.read()
                if ret:
                    frame_img = cv2.resize(frame_img, (VIDEO_WIDTH, VIDEO_HEIGHT))
                    frame_img = cv2.cvtColor(frame_img, cv2.COLOR_BGR2RGB)
                    img = ImageTk.PhotoImage(image=Image.fromarray(frame_img))
                    video_label.imgtk = img
                    video_label.configure(image=img)
                    video_label.after(30, stream)
                else:
                    local_cap.release()
                    idx_st["i"] += 1
                    next_letter()

            stream()

        next_letter()

    # ── QUIZ LOGIC  (unchanged) ───────────────────────────────
    def load_questions():
        state["question_list"].clear()
        if selected_level.get() == "level1":
            items  = [chr(i) for i in range(65, 91)] + [str(i) for i in range(10)]
            q_type = "single"
        else:
            items  = WORD_LIST
            q_type = "word"

        for item in items:
            wrong   = [x for x in items if x != item]
            random.shuffle(wrong)
            options = wrong[:3] + [item]
            random.shuffle(options)
            state["question_list"].append({
                "answer":  item,
                "options": options,
                "type":    q_type,
            })
        random.shuffle(state["question_list"])

    def load_question():
        qi = state["question_index"]
        if qi >= len(state["question_list"]):
            finish_quiz()
            return

        current = state["question_list"][qi]
        qcount_var.set(f"Question {qi + 1} / {len(state['question_list'])}")

        for w in options_frame.winfo_children():
            w.destroy()

        if current["type"] == "single":
            play_video(os.path.join(VIDEO_PATH, f"{current['answer']}.mp4"))
        else:
            play_word(current["answer"])

        opt_colors = [ACCENT_BLUE, ACCENT_PURPLE, ACCENT_GREEN, ACCENT_ORANGE]
        for j, option in enumerate(current["options"]):
            col = opt_colors[j % len(opt_colors)]
            b = tk.Button(options_frame,
                          text=option,
                          bg=col, fg="white",
                          activebackground=HOVER_BG,
                          activeforeground=ACCENT_CYAN,
                          font=("Segoe UI", 11, "bold"),
                          bd=0, pady=10, cursor="hand2",
                          width=14,
                          command=lambda opt=option: check_answer(opt))
            b.pack(fill="x", pady=5)
            b.bind("<Enter>", lambda e, btn=b: btn.config(bg=HOVER_BG))
            b.bind("<Leave>", lambda e, btn=b, c=col: btn.config(bg=c))

    def check_answer(selected):
        qi = state["question_index"]
        if qi >= len(state["question_list"]):
            return
        correct = state["question_list"][qi]["answer"]
        if selected == correct:
            state["score"] += POINTS_PER_QUESTION
            result_var.set("\u2705  Correct!")
            result_lbl.config(fg=ACCENT_GREEN)
        else:
            result_var.set(f"\u274c  Wrong\nCorrect: {correct}")
            result_lbl.config(fg=ACCENT_RED)

        score_var.set(str(state["score"]))
        state["question_index"] += 1

        if state["question_index"] < len(state["question_list"]):
            frame.after(800, load_question)
        else:
            finish_quiz()

    def finish_quiz():
        total = len(state["question_list"])
        if total == 0:
            return
        save_quiz_result(user_id, selected_level.get(), state["score"], total)
        acc = (state["score"] / (total * POINTS_PER_QUESTION)) * 100
        result_var.set(f"\U0001f3c6  Quiz Done!\nAccuracy: {acc:.1f}%")
        result_lbl.config(fg=ACCENT_CYAN)
        qcount_var.set("Completed")
        stop_video()

    def _start():
        stop_video()
        state["score"]          = 0
        state["question_index"] = 0
        score_var.set("0")
        result_var.set("")
        qcount_var.set("")
        load_questions()
        load_question()

    return frame