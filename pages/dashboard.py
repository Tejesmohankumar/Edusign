import sys, os
sys.path = [p for p in sys.path if p not in ('', '.', os.getcwd())]
_PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT not in sys.path:
    sys.path.append(_PROJECT)
PROJECT = _PROJECT

import tkinter as tk
from tkinter import font as tkfont
import sqlite3
from collections import defaultdict
from datetime import datetime
import math
import random

# =====================================================
# PORTABLE DATABASE PATHS
# =====================================================
DB_FOLDER         = os.path.join(PROJECT, "data", "DB")
PERFORMANCE_DB    = os.path.join(DB_FOLDER, "performance.db")
QUIZ_DB           = os.path.join(DB_FOLDER, "quiz.db")
SUBJECT_BASE_PATH = os.path.join(PROJECT, "data", "subjects")

# =====================================================
# THEME
# =====================================================
DARK_BG        = "#0b0f1a"
CARD_BG        = "#131929"
CARD_BORDER    = "#1e2d4a"
ACCENT_BLUE    = "#2979ff"
ACCENT_CYAN    = "#00e5ff"
ACCENT_PURPLE  = "#7c4dff"
ACCENT_GREEN   = "#00e676"
ACCENT_AMBER   = "#ffab40"
TEXT_PRIMARY   = "#e8f0fe"
TEXT_SECONDARY = "#8fa8c8"
TEXT_MUTED     = "#4a6080"
HOVER_BG       = "#1a2540"

FONT_HERO  = ("Georgia", 22, "bold")
FONT_TITLE = ("Georgia", 15, "bold")
FONT_CARD  = ("Georgia", 12, "bold")
FONT_BODY  = ("Courier", 10)
FONT_SMALL = ("Courier", 9)
FONT_LABEL = ("Georgia", 9)
FONT_STAT  = ("Georgia", 28, "bold")

# =====================================================
# DATA HELPERS
# =====================================================
def get_performance_data(user_id):
    if not os.path.exists(PERFORMANCE_DB):
        return {}
    try:
        conn = sqlite3.connect(PERFORMANCE_DB)
        cur  = conn.cursor()
        cur.execute("""
            SELECT subject, lesson_name, accuracy, timestamp
            FROM performance WHERE user_id=?
            ORDER BY timestamp ASC
        """, (str(user_id),))
        rows = cur.fetchall()
        conn.close()
    except Exception:
        return {}
    subject_data = defaultdict(dict)
    for subject, lesson, score, ts in rows:
        subject_data[subject][lesson] = max(0.0, min(100.0, float(score)))
    return dict(subject_data)


def get_performance_data_detailed(user_id):
    """Returns per-lesson best accuracy AND last-played timestamp per subject."""
    if not os.path.exists(PERFORMANCE_DB):
        return {}
    try:
        conn = sqlite3.connect(PERFORMANCE_DB)
        cur  = conn.cursor()
        cur.execute("""
            SELECT subject, lesson_name, MAX(accuracy), MAX(timestamp)
            FROM performance WHERE user_id=?
            GROUP BY subject, lesson_name
            ORDER BY subject, lesson_name ASC
        """, (str(user_id),))
        rows = cur.fetchall()
        conn.close()
    except Exception:
        return {}
    # {subject: {lesson: (best_acc, last_ts)}}
    data = defaultdict(dict)
    for subject, lesson, acc, ts in rows:
        data[subject][lesson] = (max(0.0, min(100.0, float(acc))), ts)
    return dict(data)


def get_quiz_data(user_id):
    if not os.path.exists(QUIZ_DB):
        return []
    try:
        conn = sqlite3.connect(QUIZ_DB)
        cur  = conn.cursor()
        cur.execute("""
            SELECT accuracy, timestamp, level
            FROM quiz_performance WHERE user_id=?
            ORDER BY timestamp DESC LIMIT 10
        """, (str(user_id),))
        rows = cur.fetchall()
        conn.close()
        return [(max(0.0, min(100.0, float(r[0]))), r[1], r[2]) for r in rows]
    except Exception:
        return []


def get_total_lessons_per_subject():
    totals = {}
    if not os.path.exists(SUBJECT_BASE_PATH):
        return totals
    for subj in os.listdir(SUBJECT_BASE_PATH):
        p = os.path.join(SUBJECT_BASE_PATH, subj)
        if os.path.isdir(p):
            totals[subj] = len([f for f in os.listdir(p) if f.endswith(".txt")])
    return totals


def get_lessons_list_per_subject():
    """Returns {subject: [lesson_name, ...]} for all .txt files."""
    result = {}
    if not os.path.exists(SUBJECT_BASE_PATH):
        return result
    for subj in os.listdir(SUBJECT_BASE_PATH):
        p = os.path.join(SUBJECT_BASE_PATH, subj)
        if os.path.isdir(p):
            result[subj] = sorted(
                f[:-4] for f in os.listdir(p) if f.endswith(".txt")
            )
    return result


def get_streak(user_id):
    if not os.path.exists(PERFORMANCE_DB):
        return 0
    try:
        conn = sqlite3.connect(PERFORMANCE_DB)
        cur  = conn.cursor()
        cur.execute("""
            SELECT DISTINCT date(timestamp) as d
            FROM performance WHERE user_id=?
            ORDER BY d DESC
        """, (str(user_id),))
        days = [row[0] for row in cur.fetchall()]
        conn.close()
        if not days:
            return 0
        streak = 1
        for i in range(1, len(days)):
            d1 = datetime.strptime(days[i-1], "%Y-%m-%d")
            d2 = datetime.strptime(days[i],   "%Y-%m-%d")
            if (d1 - d2).days == 1:
                streak += 1
            else:
                break
        return streak
    except Exception:
        return 0


# =====================================================
# CANVAS DRAWING HELPERS
# =====================================================
def draw_rounded_rect(canvas, x1, y1, x2, y2, r=12, **kw):
    pts = [
        x1+r, y1,  x2-r, y1,
        x2,   y1,  x2,   y1+r,
        x2,   y2-r, x2,  y2,
        x2-r, y2,  x1+r, y2,
        x1,   y2,  x1,   y2-r,
        x1,   y1+r, x1,  y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


def draw_glow_bar(canvas, x1, y1, x2, y2, pct, color, r=4):
    draw_rounded_rect(canvas, x1, y1, x2, y2, r=r, fill="#1a2540", outline="")
    if pct > 0:
        fill_x = x1 + ((x2 - x1) * min(pct, 100) / 100)
        fill_x = max(x1 + r * 2, fill_x)
        draw_rounded_rect(canvas, x1, y1, fill_x, y2, r=r, fill=color, outline="")
        hy2 = y1 + (y2 - y1) * 0.4
        draw_rounded_rect(canvas, x1+2, y1+1, fill_x-2, hy2, r=2,
                          fill="white", outline="", stipple="gray50")


# =====================================================
# MAIN PAGE
# =====================================================
def page(parent, user_id):
    root = tk.Frame(parent, bg=DARK_BG)
    root.pack(fill="both", expand=True)

    # ── Fetch data ───────────────────────────────────────────
    perf_data        = get_performance_data(user_id)
    perf_detailed    = get_performance_data_detailed(user_id)
    quiz_data        = get_quiz_data(user_id)
    total_lessons    = get_total_lessons_per_subject()
    lessons_list     = get_lessons_list_per_subject()
    streak           = get_streak(user_id)

    completed_lessons = sum(len(v) for v in perf_data.values())
    total_available   = sum(total_lessons.values()) or 1
    overall_pct       = min(100.0, (completed_lessons / total_available) * 100)
    quiz_avg          = (sum(r[0] for r in quiz_data) / len(quiz_data)) if quiz_data else 0

    # ── Top bar ──────────────────────────────────────────────
    topbar = tk.Frame(root, bg=DARK_BG, pady=14)
    topbar.pack(fill="x", padx=24)

    topbar_left = tk.Frame(topbar, bg=DARK_BG)
    topbar_left.pack(side="left")
    tk.Label(topbar_left, text="Student Dashboard",
             bg=DARK_BG, fg=TEXT_PRIMARY, font=FONT_HERO).pack(anchor="w")
    tk.Label(topbar_left,
             text=datetime.now().strftime("%A, %d %B %Y"),
             bg=DARK_BG, fg=TEXT_MUTED, font=FONT_BODY).pack(anchor="w")

    def refresh_dashboard():
        nonlocal perf_data, perf_detailed, quiz_data, streak
        nonlocal completed_lessons, overall_pct, quiz_avg, total_lessons, lessons_list
        perf_data         = get_performance_data(user_id)
        perf_detailed     = get_performance_data_detailed(user_id)
        quiz_data         = get_quiz_data(user_id)
        total_lessons     = get_total_lessons_per_subject()
        lessons_list      = get_lessons_list_per_subject()
        streak            = get_streak(user_id)
        completed_lessons = sum(len(v) for v in perf_data.values())
        overall_pct       = min(100.0, (completed_lessons / total_available) * 100)
        quiz_avg          = (sum(r[0] for r in quiz_data) / len(quiz_data)) if quiz_data else 0
        rebuild_content()

    topbar_right = tk.Frame(topbar, bg=DARK_BG)
    topbar_right.pack(side="right")
    ref_btn = tk.Label(topbar_right, text="\u27f3  Refresh",
                       bg=CARD_BG, fg=ACCENT_CYAN,
                       font=FONT_BODY, padx=12, pady=6, cursor="hand2")
    ref_btn.pack()
    ref_btn.bind("<Button-1>", lambda e: refresh_dashboard())
    ref_btn.bind("<Enter>",    lambda e: ref_btn.config(bg=HOVER_BG))
    ref_btn.bind("<Leave>",    lambda e: ref_btn.config(bg=CARD_BG))

    tk.Frame(root, bg=CARD_BORDER, height=1).pack(fill="x", padx=24, pady=(0, 4))

    # ── Scrollable content ───────────────────────────────────
    scroll_canvas = tk.Canvas(root, bg=DARK_BG, highlightthickness=0)
    scrollbar     = tk.Scrollbar(root, orient="vertical",
                                 command=scroll_canvas.yview,
                                 bg=CARD_BG, troughcolor=DARK_BG)
    scroll_canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    scroll_canvas.pack(side="left", fill="both", expand=True)

    content = tk.Frame(scroll_canvas, bg=DARK_BG)
    content_window = scroll_canvas.create_window((0, 0), window=content, anchor="nw")

    def on_configure(e):
        scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))
        scroll_canvas.itemconfig(content_window, width=scroll_canvas.winfo_width())

    content.bind("<Configure>", on_configure)
    scroll_canvas.bind("<Configure>", on_configure)
    scroll_canvas.bind_all("<MouseWheel>",
                           lambda e: scroll_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    # =====================================================
    # CONTENT BUILDER
    # =====================================================
    def rebuild_content():
        for w in content.winfo_children():
            w.destroy()

        pad = 24

        # ── HERO BANNER ──────────────────────────────────────
        hero = tk.Frame(content, bg="#0d1526")
        hero.pack(fill="x", padx=pad, pady=(10, 6))

        left_hero = tk.Frame(hero, bg="#0d1526", padx=20, pady=20)
        left_hero.pack(side="left", fill="both", expand=True)

        greeting = ("Good Morning"   if datetime.now().hour < 12 else
                    "Good Afternoon" if datetime.now().hour < 17 else "Good Evening")
        tk.Label(left_hero, text=f"{greeting}!",
                 bg="#0d1526", fg=TEXT_MUTED, font=FONT_BODY).pack(anchor="w")
        tk.Label(left_hero, text="Keep signing,\nkeep growing. \U0001f91f",
                 bg="#0d1526", fg=TEXT_PRIMARY,
                 font=("Georgia", 20, "bold"), justify="left").pack(anchor="w", pady=(4, 10))

        pill = tk.Frame(left_hero, bg=ACCENT_BLUE, padx=16, pady=6)
        pill.pack(anchor="w")
        tk.Label(pill,
                 text=f"\U0001f4c8  {overall_pct:.0f}% Overall Progress  \u2014  {streak} Day Streak \U0001f525",
                 bg=ACCENT_BLUE, fg="white",
                 font=("Georgia", 10, "bold")).pack()

        right_hero = tk.Frame(hero, bg="#0d1526", width=240, height=120, padx=10, pady=10)
        right_hero.pack(side="right")
        right_hero.pack_propagate(False)

        illus = tk.Canvas(right_hero, width=220, height=110,
                          bg="#0d1526", highlightthickness=0)
        illus.pack()

        colors_cycle = [ACCENT_BLUE, ACCENT_CYAN, ACCENT_PURPLE, ACCENT_GREEN, ACCENT_AMBER]
        for i in range(5):
            x = 20 + i * 40
            illus.create_oval(x, 60, x+24, 90, fill=colors_cycle[i], outline="")
            for j in range(4):
                fh = [20, 15, 17, 14][j]
                fx = x + j * 6
                illus.create_oval(fx, fh, fx+6, 65, fill=colors_cycle[i], outline="")
            illus.create_oval(x-6, 65, x+4, 82, fill=colors_cycle[i], outline="")
        for i in range(8):
            dx = 15 + i * 25
            dy = 8 + (i % 3) * 12
            illus.create_oval(dx, dy, dx+6, dy+6, fill=colors_cycle[i % 5], outline="")

        # ── STAT CARDS (3 cards — lesson accuracy removed) ───
        stats_row = tk.Frame(content, bg=DARK_BG)
        stats_row.pack(fill="x", padx=pad, pady=6)

        def stat_card(parent, icon, label, value, color, sub=""):
            c = tk.Frame(parent, bg=CARD_BG, padx=18, pady=16)
            c.pack(side="left", expand=True, fill="both", padx=5)
            tk.Label(c, text=icon, bg=CARD_BG, fg=color,
                     font=("Segoe UI Emoji", 18)).pack(anchor="w")
            tk.Label(c, text=str(value), bg=CARD_BG, fg=color,
                     font=FONT_STAT).pack(anchor="w", pady=(6, 0))
            tk.Label(c, text=label, bg=CARD_BG, fg=TEXT_PRIMARY,
                     font=FONT_CARD).pack(anchor="w")
            if sub:
                tk.Label(c, text=sub, bg=CARD_BG, fg=TEXT_MUTED,
                         font=FONT_SMALL).pack(anchor="w", pady=(2, 0))
            tk.Frame(c, bg=color, height=2).pack(fill="x", pady=(10, 0))

        stat_card(stats_row, "\U0001f4d6", "Lessons Done",
                  completed_lessons, ACCENT_BLUE, f"of {total_available} total")
        stat_card(stats_row, "\U0001f3af", "Quiz Accuracy",
                  f"{quiz_avg:.0f}%", ACCENT_CYAN, f"Last {len(quiz_data)} attempts")
        stat_card(stats_row, "\U0001f525", "Day Streak",
                  streak, ACCENT_AMBER, "consecutive days")

        # ── PROGRESS + DETAILED SUBJECTS ─────────────────────
        mid_row = tk.Frame(content, bg=DARK_BG)
        mid_row.pack(fill="x", padx=pad, pady=6)

        # Overall circular progress (unchanged)
        left_mid = tk.Frame(mid_row, bg=CARD_BG, padx=20, pady=20)
        left_mid.pack(side="left", fill="both", padx=(0, 6))

        tk.Label(left_mid, text="Overall Progress",
                 bg=CARD_BG, fg=TEXT_PRIMARY, font=FONT_TITLE).pack(anchor="w")
        tk.Label(left_mid, text="Based on completed lessons",
                 bg=CARD_BG, fg=TEXT_MUTED, font=FONT_SMALL).pack(anchor="w", pady=(0, 12))

        arc_size = 140
        arc_c    = tk.Canvas(left_mid, width=arc_size, height=arc_size,
                             bg=CARD_BG, highlightthickness=0)
        arc_c.pack()
        r = 55
        cx = cy = arc_size // 2
        arc_c.create_oval(cx-r, cy-r, cx+r, cy+r, outline=CARD_BORDER, width=12)
        if overall_pct > 0:
            extent = (min(overall_pct, 100) / 100) * 359.9
            arc_c.create_arc(cx-r, cy-r, cx+r, cy+r,
                             start=90, extent=-extent,
                             outline=ACCENT_BLUE, width=12, style="arc")
        arc_c.create_text(cx, cy-10, text=f"{overall_pct:.0f}%",
                          fill=ACCENT_BLUE, font=("Georgia", 22, "bold"))
        arc_c.create_text(cx, cy+14, text="Complete",
                          fill=TEXT_MUTED, font=FONT_SMALL)

        info_row = tk.Frame(left_mid, bg=CARD_BG)
        info_row.pack(fill="x", pady=(14, 0))
        for label, val, color in [
            ("Completed", completed_lessons, ACCENT_GREEN),
            ("Remaining", total_available - completed_lessons, ACCENT_AMBER),
        ]:
            col = tk.Frame(info_row, bg=CARD_BG)
            col.pack(side="left", expand=True)
            tk.Label(col, text=label, bg=CARD_BG, fg=TEXT_MUTED, font=FONT_SMALL).pack()
            tk.Label(col, text=str(val), bg=CARD_BG, fg=color,
                     font=("Georgia", 16, "bold")).pack()

        # ── DETAILED SUBJECT BREAKDOWN ────────────────────────
        right_mid = tk.Frame(mid_row, bg=DARK_BG)
        right_mid.pack(side="left", fill="both", expand=True, padx=(6, 0))

        tk.Label(right_mid, text="Subject Progress",
                 bg=DARK_BG, fg=TEXT_PRIMARY, font=FONT_TITLE).pack(anchor="w")
        tk.Label(right_mid, text="Completion, accuracy, and lesson breakdown per subject",
                 bg=DARK_BG, fg=TEXT_MUTED, font=FONT_SMALL).pack(anchor="w", pady=(0, 8))

        if not perf_data and not total_lessons:
            empty_card = tk.Frame(right_mid, bg=CARD_BG, pady=30)
            empty_card.pack(fill="x")
            tk.Label(empty_card,
                     text="\U0001f91f  No lessons completed yet!\n\nStart your first lesson to\nsee your progress here.",
                     bg=CARD_BG, fg=TEXT_MUTED, font=FONT_BODY, justify="center").pack()
        else:
            subj_colors = [ACCENT_BLUE, ACCENT_CYAN, ACCENT_PURPLE, ACCENT_GREEN, ACCENT_AMBER]

            # Show every subject that exists in the folder
            all_subjects = sorted(total_lessons.keys())

            for idx, subject in enumerate(all_subjects):
                color      = subj_colors[idx % len(subj_colors)]
                total_s    = max(total_lessons.get(subject, 0), 1)
                done_lessons = perf_detailed.get(subject, {})
                done_s     = len(done_lessons)
                pct_s      = min(100.0, (done_s / total_s) * 100)
                all_accs   = [v[0] for v in done_lessons.values()]
                acc_s      = sum(all_accs) / len(all_accs) if all_accs else 0
                best_acc   = max(all_accs) if all_accs else 0
                worst_acc  = min(all_accs) if all_accs else 0

                # Outer subject card
                sc = tk.Frame(right_mid, bg=CARD_BG, padx=0, pady=0)
                sc.pack(fill="x", pady=4)

                # Colour accent strip on left
                strip_row = tk.Frame(sc, bg=CARD_BG)
                strip_row.pack(fill="x")
                tk.Frame(strip_row, bg=color, width=4).pack(side="left", fill="y")

                sc_inner = tk.Frame(strip_row, bg=CARD_BG, padx=14, pady=10)
                sc_inner.pack(side="left", fill="both", expand=True)

                # ── Header row ───────────────────────────────
                hdr_row = tk.Frame(sc_inner, bg=CARD_BG)
                hdr_row.pack(fill="x")
                tk.Label(hdr_row, text=f"\u25cf  {subject}",
                         bg=CARD_BG, fg=color,
                         font=("Georgia", 12, "bold")).pack(side="left")
                tk.Label(hdr_row,
                         text=f"{done_s} / {total_s} lessons",
                         bg=CARD_BG, fg=TEXT_MUTED,
                         font=FONT_SMALL).pack(side="right")

                # ── Progress bar ──────────────────────────────
                bar_c = tk.Canvas(sc_inner, height=10, bg=CARD_BG, highlightthickness=0)
                bar_c.pack(fill="x", pady=(6, 4))

                def draw_bar(c=bar_c, p=pct_s, col=color):
                    c.update_idletasks()
                    w_ = c.winfo_width() or 400
                    draw_glow_bar(c, 0, 0, w_, 10, p, col, r=5)
                    pct_x = max((p / 100) * w_, 36)
                    c.create_text(min(pct_x - 4, w_ - 4), 5,
                                  text=f"{p:.0f}%", fill="white",
                                  font=("Courier", 7, "bold"), anchor="e")

                sc_inner.after(50, draw_bar)

                # ── Mini stat chips ───────────────────────────
                chips_row = tk.Frame(sc_inner, bg=CARD_BG)
                chips_row.pack(fill="x", pady=(4, 6))

                def chip(parent, label, val, color, bg=CARD_BG):
                    f = tk.Frame(parent, bg=HOVER_BG, padx=8, pady=3)
                    f.pack(side="left", padx=(0, 6))
                    tk.Label(f, text=label, bg=HOVER_BG, fg=TEXT_MUTED,
                             font=("Courier", 8)).pack(side="left")
                    tk.Label(f, text=val, bg=HOVER_BG, fg=color,
                             font=("Georgia", 9, "bold")).pack(side="left", padx=(4, 0))

                if done_s > 0:
                    acc_color  = (ACCENT_GREEN if acc_s >= 75 else
                                  ACCENT_AMBER if acc_s >= 50 else "#ef4444")
                    best_color = (ACCENT_GREEN if best_acc >= 75 else
                                  ACCENT_AMBER if best_acc >= 50 else "#ef4444")
                    chip(chips_row, "Avg acc",  f"{acc_s:.0f}%",   acc_color)
                    chip(chips_row, "Best",     f"{best_acc:.0f}%", best_color)
                    chip(chips_row, "Worst",    f"{worst_acc:.0f}%",
                         ACCENT_GREEN if worst_acc >= 75 else
                         ACCENT_AMBER if worst_acc >= 50 else "#ef4444")
                else:
                    chip(chips_row, "Status", "Not started", TEXT_MUTED)

                # ── Per-lesson rows ───────────────────────────
                all_lesson_names = lessons_list.get(subject, sorted(done_lessons.keys()))

                lessons_frame = tk.Frame(sc_inner, bg="#0f1622")
                lessons_frame.pack(fill="x", pady=(2, 0))

                # Column headers
                col_hdr = tk.Frame(lessons_frame, bg="#0f1622", padx=8, pady=4)
                col_hdr.pack(fill="x")
                tk.Label(col_hdr, text="Lesson",
                         bg="#0f1622", fg=TEXT_MUTED,
                         font=("Courier", 8), width=28, anchor="w").pack(side="left")
                tk.Label(col_hdr, text="Best Acc",
                         bg="#0f1622", fg=TEXT_MUTED,
                         font=("Courier", 8), width=10, anchor="center").pack(side="left")
                tk.Label(col_hdr, text="Status",
                         bg="#0f1622", fg=TEXT_MUTED,
                         font=("Courier", 8), width=12, anchor="center").pack(side="left")
                tk.Label(col_hdr, text="Last Played",
                         bg="#0f1622", fg=TEXT_MUTED,
                         font=("Courier", 8), width=14, anchor="e").pack(side="right")

                tk.Frame(lessons_frame, bg=CARD_BORDER, height=1).pack(fill="x", padx=4)

                for lname in all_lesson_names:
                    lesson_key = lname + ".txt" if (lname + ".txt") in done_lessons else lname
                    done_data  = done_lessons.get(lesson_key) or done_lessons.get(lname)
                    is_done    = done_data is not None
                    acc_val    = done_data[0] if is_done else 0
                    last_ts    = done_data[1][:10] if is_done else "—"

                    if is_done:
                        status_text  = "Complete" if acc_val >= 100 else "In Progress"
                        status_color = ACCENT_GREEN if acc_val >= 100 else ACCENT_AMBER
                        acc_color2   = (ACCENT_GREEN if acc_val >= 75 else
                                        ACCENT_AMBER if acc_val >= 50 else "#ef4444")
                        row_bg = "#111c2e"
                    else:
                        status_text  = "Not Started"
                        status_color = TEXT_MUTED
                        acc_color2   = TEXT_MUTED
                        row_bg       = "#0d1420"

                    lr = tk.Frame(lessons_frame, bg=row_bg, padx=8, pady=5)
                    lr.pack(fill="x", pady=1)

                    # Status dot
                    dot_color = (ACCENT_GREEN if is_done and acc_val >= 100 else
                                 ACCENT_AMBER if is_done else TEXT_MUTED)
                    tk.Label(lr, text="\u25cf",
                             bg=row_bg, fg=dot_color,
                             font=("Courier", 8)).pack(side="left", padx=(0, 4))

                    # Lesson name
                    tk.Label(lr, text=lname,
                             bg=row_bg, fg=TEXT_PRIMARY if is_done else TEXT_MUTED,
                             font=("Courier", 9), width=26, anchor="w").pack(side="left")

                    # Accuracy
                    tk.Label(lr,
                             text=f"{acc_val:.0f}%" if is_done else "—",
                             bg=row_bg, fg=acc_color2 if is_done else TEXT_MUTED,
                             font=("Georgia", 9, "bold"),
                             width=8, anchor="center").pack(side="left")

                    # Status badge
                    badge_bg = (ACCENT_GREEN if status_text == "Complete" else
                                "#2a2000"    if status_text == "In Progress" else
                                "#1a1a2e")
                    badge_fg = (DARK_BG      if status_text == "Complete" else
                                ACCENT_AMBER if status_text == "In Progress" else
                                TEXT_MUTED)
                    badge = tk.Frame(lr, bg=badge_bg, padx=6, pady=1)
                    badge.pack(side="left", padx=4)
                    tk.Label(badge, text=status_text,
                             bg=badge_bg, fg=badge_fg,
                             font=("Courier", 8)).pack()

                    # Last played date (right-aligned)
                    tk.Label(lr, text=last_ts,
                             bg=row_bg, fg=TEXT_MUTED,
                             font=("Courier", 8)).pack(side="right", padx=(0, 4))

        # ── RECENT LESSONS + QUIZ STATS ──────────────────────
        bottom_row = tk.Frame(content, bg=DARK_BG)
        bottom_row.pack(fill="x", padx=pad, pady=6)

        left_bot = tk.Frame(bottom_row, bg=CARD_BG, padx=16, pady=16)
        left_bot.pack(side="left", fill="both", expand=True, padx=(0, 6))
        tk.Label(left_bot, text="Recent Lessons",
                 bg=CARD_BG, fg=TEXT_PRIMARY, font=FONT_TITLE).pack(anchor="w")
        tk.Label(left_bot, text="Latest completed lessons",
                 bg=CARD_BG, fg=TEXT_MUTED, font=FONT_SMALL).pack(anchor="w", pady=(0, 10))

        recent_entries = []
        if os.path.exists(PERFORMANCE_DB):
            try:
                conn = sqlite3.connect(PERFORMANCE_DB)
                cur  = conn.cursor()
                cur.execute("""
                    SELECT subject, lesson_name, accuracy, timestamp
                    FROM performance WHERE user_id=?
                    ORDER BY timestamp DESC LIMIT 6
                """, (str(user_id),))
                recent_entries = cur.fetchall()
                conn.close()
            except Exception:
                pass

        if not recent_entries:
            tk.Label(left_bot,
                     text="No recent activity.\nComplete a lesson to get started!",
                     bg=CARD_BG, fg=TEXT_MUTED, font=FONT_BODY, justify="center").pack(pady=20)
        else:
            for subj, lesson, acc, ts in recent_entries:
                color_acc = (ACCENT_GREEN if acc >= 75 else
                             ACCENT_AMBER if acc >= 50 else "#ef4444")
                row_f = tk.Frame(left_bot, bg=HOVER_BG, padx=12, pady=8)
                row_f.pack(fill="x", pady=2)
                left_r = tk.Frame(row_f, bg=HOVER_BG)
                left_r.pack(side="left", fill="both", expand=True)
                tk.Label(left_r, text=f"\U0001f4c4 {lesson}",
                         bg=HOVER_BG, fg=TEXT_PRIMARY,
                         font=("Georgia", 10, "bold")).pack(anchor="w")
                tk.Label(left_r, text=f"{subj}  \u00b7  {ts[:10]}",
                         bg=HOVER_BG, fg=TEXT_MUTED, font=FONT_SMALL).pack(anchor="w")
                badge = tk.Frame(row_f, bg=color_acc, padx=8, pady=3)
                badge.pack(side="right", anchor="center")
                tk.Label(badge, text=f"{acc:.0f}%",
                         bg=color_acc, fg="white",
                         font=("Georgia", 9, "bold")).pack()

        right_bot = tk.Frame(bottom_row, bg=CARD_BG, padx=16, pady=16, width=280)
        right_bot.pack(side="left", fill="y", padx=(6, 0))
        right_bot.pack_propagate(False)
        tk.Label(right_bot, text="Quiz Results",
                 bg=CARD_BG, fg=TEXT_PRIMARY, font=FONT_TITLE).pack(anchor="w")
        tk.Label(right_bot, text="Last 10 attempts",
                 bg=CARD_BG, fg=TEXT_MUTED, font=FONT_SMALL).pack(anchor="w", pady=(0, 10))

        if not quiz_data:
            tk.Label(right_bot,
                     text="\U0001f3af  No quizzes taken yet.\nTry the quiz section!",
                     bg=CARD_BG, fg=TEXT_MUTED, font=FONT_BODY, justify="center").pack(pady=20)
        else:
            chart_c = tk.Canvas(right_bot, width=240, height=80,
                                bg=CARD_BG, highlightthickness=0)
            chart_c.pack(pady=(0, 8))
            n     = min(len(quiz_data), 10)
            bar_w = 220 // n
            for i, (acc, ts, level) in enumerate(reversed(quiz_data[:n])):
                bh    = int((acc / 100) * 70)
                x0    = 10 + i * bar_w
                color = (ACCENT_GREEN if acc >= 75 else
                         ACCENT_AMBER if acc >= 50 else "#ef4444")
                chart_c.create_rectangle(x0, 78-bh, x0+bar_w-3, 78,
                                         fill=color, outline="")
            avg_y = 78 - int((quiz_avg / 100) * 70)
            chart_c.create_line(10, avg_y, 230, avg_y,
                                fill=ACCENT_CYAN, width=1, dash=(4, 3))
            chart_c.create_text(232, avg_y, text="avg",
                                fill=ACCENT_CYAN, font=("Courier", 7), anchor="w")

            for acc, ts, level in quiz_data[:5]:
                color = (ACCENT_GREEN if acc >= 75 else
                         ACCENT_AMBER if acc >= 50 else "#ef4444")
                qr = tk.Frame(right_bot, bg=HOVER_BG, padx=10, pady=5)
                qr.pack(fill="x", pady=2)
                tk.Label(qr, text=f"Lvl: {level}",
                         bg=HOVER_BG, fg=TEXT_MUTED, font=FONT_SMALL).pack(side="left")
                tk.Label(qr, text=f"{acc:.0f}%",
                         bg=HOVER_BG, fg=color,
                         font=("Georgia", 10, "bold")).pack(side="right")

            tk.Frame(right_bot, bg=CARD_BORDER, height=1).pack(fill="x", pady=8)
            avg_row = tk.Frame(right_bot, bg=CARD_BG)
            avg_row.pack(fill="x")
            tk.Label(avg_row, text="Quiz Average",
                     bg=CARD_BG, fg=TEXT_MUTED, font=FONT_SMALL).pack(side="left")
            tk.Label(avg_row, text=f"{quiz_avg:.1f}%",
                     bg=CARD_BG, fg=ACCENT_CYAN,
                     font=("Georgia", 13, "bold")).pack(side="right")

        # ── DAILY TIP ─────────────────────────────────────────
        tip_frame = tk.Frame(content, bg="#0d1a2e", pady=14)
        tip_frame.pack(fill="x", padx=pad, pady=(6, 14))
        tip_inner = tk.Frame(tip_frame, bg="#0d1a2e", padx=20)
        tip_inner.pack(fill="x")
        tips = [
            "\U0001f91f  Sign language is a complete, expressive language with its own grammar.",
            "\u270b  Practice each sign slowly at first — accuracy matters more than speed.",
            "\U0001f441  Watch native signers to learn natural rhythm and expression.",
            "\U0001f504  Review past lessons regularly to reinforce memory.",
            "\U0001f3af  Aim for consistency — even 10 minutes a day builds fluency.",
        ]
        tk.Label(tip_inner, text="\U0001f4a1  Daily Tip",
                 bg="#0d1a2e", fg=ACCENT_AMBER, font=FONT_CARD).pack(anchor="w")
        tk.Label(tip_inner, text=random.choice(tips),
                 bg="#0d1a2e", fg=TEXT_SECONDARY,
                 font=FONT_BODY, wraplength=700, justify="left").pack(anchor="w", pady=(4, 0))

    rebuild_content()
    return root


# =====================================================
# STANDALONE RUN
# =====================================================
if __name__ == "__main__":
    win = tk.Tk()
    win.title("EduSign \u2013 Student Dashboard")
    win.geometry("1100x750")
    win.configure(bg=DARK_BG)
    page(win, user_id=1)
    win.mainloop()