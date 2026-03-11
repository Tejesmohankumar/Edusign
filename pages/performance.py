import sys, os
sys.path = [p for p in sys.path if p not in ('', '.', os.getcwd())]
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

import tkinter as tk
import sqlite3
from collections import defaultdict
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---- PORTABLE DATABASE PATHS ----
DB_FOLDER          = os.path.join(PROJECT, "data", "DB")
PERFORMANCE_DB     = os.path.join(DB_FOLDER, "performance.db")
QUIZ_DB            = os.path.join(DB_FOLDER, "quiz.db")
LESSON_PROGRESS_DB = os.path.join(DB_FOLDER, "lesson_progress.db")

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
# MATPLOTLIB DARK STYLE
# ============================
PLOT_BG    = "#0f1829"
PLOT_FG    = "#7a9bc4"
PLOT_GRID  = "#1a2845"
PLOT_LINE1 = "#1e6fff"
PLOT_LINE2 = "#00c896"
PLOT_LINE3 = "#f59e0b"
PLOT_DOT   = "#00d4ff"

SUBJ_PALETTE = [
    "#00c896", "#1e6fff", "#f59e0b", "#ff4d6d",
    "#00d4ff", "#7b5ea7", "#ff8c42", "#e879f9",
    "#34d399", "#60a5fa", "#a78bfa", "#fbbf24",
]


def _apply_dark_style(ax, fig):
    fig.patch.set_facecolor(PLOT_BG)
    ax.set_facecolor(PLOT_BG)
    ax.tick_params(colors=PLOT_FG, labelsize=8)
    ax.xaxis.label.set_color(PLOT_FG)
    ax.yaxis.label.set_color(PLOT_FG)
    ax.title.set_color(TEXT_PRIMARY)
    for spine in ax.spines.values():
        spine.set_edgecolor(PLOT_GRID)
    ax.grid(True, color=PLOT_GRID, linestyle="--", linewidth=0.6)


# =====================================================
# SESSION-LEVEL PROGRESS QUERY
# =====================================================
def _load_session_progress(user_id):
    sessions = []
    if not os.path.exists(LESSON_PROGRESS_DB):
        return sessions
    try:
        conn = sqlite3.connect(LESSON_PROGRESS_DB)
        cur  = conn.cursor()
        cur.execute("""
            SELECT subject, lesson_name, progress, timestamp
            FROM   lesson_progress
            WHERE  user_id = ?
            ORDER  BY timestamp ASC
        """, (str(user_id),))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return sessions

        from datetime import datetime as _dt
        FMT = "%Y-%m-%d %H:%M:%S"
        GAP = 30 * 60

        open_session = {}

        # --- CHANGED: record the FINAL (latest) progress of a session,
        #     not the maximum.  This lets a replayed lesson show its
        #     actual mid-session value even when a prior attempt was 100%.
        def _flush(key, final_prog):
            subj, lname = key
            sessions.append((subj, lname, max(0.0, min(100.0, float(final_prog or 0)))))

        for subj, lname, prog, ts_str in rows:
            try:
                ts = _dt.strptime(ts_str[:19], FMT)
            except Exception:
                continue
            val = float(prog or 0)
            key = (subj, lname)

            if key in open_session:
                last_ts, last_prog = open_session[key]
                gap = (ts - last_ts).total_seconds()
                if gap >= GAP:
                    # Session ended — flush with whatever progress it reached
                    _flush(key, last_prog)
                    open_session[key] = (ts, val)
                else:
                    # Still in the same session — keep the latest value
                    open_session[key] = (ts, val)
            else:
                open_session[key] = (ts, val)

        last_ts_map = {}
        for subj, lname, prog, ts_str in rows:
            try:
                ts = _dt.strptime(ts_str[:19], FMT)
            except Exception:
                continue
            last_ts_map[(subj, lname)] = ts

        remaining = sorted(open_session.items(),
                           key=lambda kv: last_ts_map.get(kv[0], _dt.min))
        for key, (_, final_prog) in remaining:
            _flush(key, final_prog)

    except Exception:
        pass
    return sessions


def page(parent, user_id):
    main_frame = tk.Frame(parent, bg=DARK_BG)
    main_frame.pack(fill="both", expand=True)

    # ── Header ───────────────────────────────────────────────
    hdr = tk.Frame(main_frame, bg=DARK_BG)
    hdr.pack(fill="x", padx=22, pady=(18, 4))

    hdr_left = tk.Frame(hdr, bg=DARK_BG)
    hdr_left.pack(side="left", fill="both", expand=True)
    tk.Label(hdr_left, text="\U0001f4ca  Performance Dashboard",
             bg=DARK_BG, fg=TEXT_PRIMARY, font=FONT_TITLE).pack(anchor="w")
    tk.Label(hdr_left, text="Track your lesson completion and quiz scores over time",
             bg=DARK_BG, fg=TEXT_SEC, font=FONT_SMALL).pack(anchor="w", pady=(2, 0))

    hdr_right = tk.Frame(hdr, bg=DARK_BG)
    hdr_right.pack(side="right", anchor="center")
    ref_btn = tk.Label(hdr_right, text="\u21bb  Refresh",
                       bg=CARD_BG, fg=ACCENT_CYAN,
                       font=FONT_BODY, padx=12, pady=6, cursor="hand2")
    ref_btn.pack()
    ref_btn.bind("<Enter>", lambda e: ref_btn.config(bg=HOVER_BG))
    ref_btn.bind("<Leave>", lambda e: ref_btn.config(bg=CARD_BG))

    tk.Frame(main_frame, bg=CARD_BORDER, height=1).pack(fill="x", padx=22, pady=(6, 0))

    # ── Scrollable content ────────────────────────────────────
    outer_scroll = tk.Frame(main_frame, bg=DARK_BG)
    outer_scroll.pack(fill="both", expand=True)

    scroll_canvas = tk.Canvas(outer_scroll, bg=DARK_BG, highlightthickness=0)
    scrollbar = tk.Scrollbar(outer_scroll, orient="vertical",
                             command=scroll_canvas.yview,
                             bg=CARD_BG, troughcolor=DARK_BG)
    scroll_canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    scroll_canvas.pack(side="left", fill="both", expand=True)

    content = tk.Frame(scroll_canvas, bg=DARK_BG)
    scroll_canvas.create_window((0, 0), window=content, anchor="nw")
    content.bind("<Configure>",
                 lambda e: scroll_canvas.configure(
                     scrollregion=scroll_canvas.bbox("all")))

    # ── Smooth scrolling (mouse wheel + trackpad) ─────────────
    def _on_mousewheel(event):
        scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_trackpad(event):
        if event.num == 4:
            scroll_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            scroll_canvas.yview_scroll(1, "units")

    def _bind_scroll(widget):
        widget.bind("<MouseWheel>",  _on_mousewheel, add="+")
        widget.bind("<Button-4>",    _on_trackpad,   add="+")
        widget.bind("<Button-5>",    _on_trackpad,   add="+")

    _bind_scroll(scroll_canvas)
    _bind_scroll(content)
    content.bind("<Configure>", lambda e: (
        scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")),
        [_bind_scroll(w) for w in content.winfo_children()]
    ), add="+")

    def _card(title="", icon=""):
        outer = tk.Frame(content, bg=CARD_BORDER, padx=1, pady=1)
        outer.pack(fill="x", padx=18, pady=8)
        inner = tk.Frame(outer, bg=CARD_BG, padx=18, pady=14)
        inner.pack(fill="both", expand=True)
        if title:
            h = tk.Frame(inner, bg=CARD_BG)
            h.pack(fill="x", pady=(0, 8))
            tk.Label(h, text=f"{icon}  {title}" if icon else title,
                     bg=CARD_BG, fg=TEXT_PRIMARY, font=FONT_LABEL).pack(side="left")
            tk.Frame(inner, bg=CARD_BORDER, height=1).pack(fill="x", pady=(0, 8))
        return inner

    # =====================================================
    # BUILD CONTENT
    # =====================================================
    def _bind_all_children(widget):
        _bind_scroll(widget)
        for child in widget.winfo_children():
            _bind_all_children(child)


    # =====================================================
    # BUILD CONTENT — deferred/chained for smooth loading
    # =====================================================
    def _bind_all_children(widget):
        _bind_scroll(widget)
        for child in widget.winfo_children():
            _bind_all_children(child)

    def build_content():
        plt.close("all")
        for w in content.winfo_children():
            w.destroy()
        content.update_idletasks()
        scroll_canvas.yview_moveto(0)

        # Show skeleton immediately so window feels responsive
        loading = _card()
        tk.Label(loading, text="⏳  Loading dashboard...",
                 bg=CARD_BG, fg=TEXT_SEC, font=FONT_BODY).pack(pady=20)

        def _do_load():
            for w in content.winfo_children():
                w.destroy()

            if not os.path.exists(PERFORMANCE_DB):
                c = _card()
                tk.Label(c,
                         text="\u26a0   Performance database not found.\nComplete a lesson first.",
                         bg=CARD_BG, fg=ACCENT_ORANGE,
                         font=FONT_BODY, justify="center").pack(pady=20)
                return

            try:
                conn   = sqlite3.connect(PERFORMANCE_DB)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT subject, lesson_name, MAX(accuracy) as best
                    FROM performance WHERE user_id=?
                    GROUP BY subject, lesson_name
                    ORDER BY subject, lesson_name ASC
                """, (str(user_id),))
                lesson_data = cursor.fetchall()
                cursor.execute("""
                    SELECT subject, lesson_name, COUNT(*) as plays
                    FROM performance WHERE user_id=?
                    GROUP BY subject, lesson_name
                """, (str(user_id),))
                play_count_rows = cursor.fetchall()
                conn.close()
            except Exception as e:
                c = _card()
                tk.Label(c, text=f"Database error: {e}",
                         bg=CARD_BG, fg=ACCENT_RED, font=FONT_BODY).pack(pady=10)
                return

            if not lesson_data:
                c = _card()
                tk.Label(c,
                         text="No lesson data yet.\nComplete a lesson to see your progress!",
                         bg=CARD_BG, fg=TEXT_SEC,
                         font=FONT_BODY, justify="center").pack(pady=20)
                return

            subject_data = defaultdict(dict)
            for subject, lesson, score in lesson_data:
                subject_data[subject][lesson] = max(0.0, min(100.0, score))

            play_counts = {(s, l): cnt for s, l, cnt in play_count_rows}
            latest_scores = [s for subj in subject_data.values() for s in subj.values()]
            overall_avg   = (sum(latest_scores) / len(latest_scores)) if latest_scores else 0.0

            all_sessions = _load_session_progress(user_id)
            sessions_by_subj = defaultdict(list)
            for subj, lname, pct in all_sessions:
                sessions_by_subj[subj].append((lname, pct))

            # ── STEP 1: Overall progress card (immediate) ─────
            prog_inner = _card("Overall Lesson Progress", "\U0001f4c8")
            pbar_row = tk.Frame(prog_inner, bg=CARD_BG)
            pbar_row.pack(fill="x")
            tk.Label(pbar_row, text="Average Completion",
                     bg=CARD_BG, fg=TEXT_SEC, font=FONT_LABEL).pack(side="left")
            tk.Label(pbar_row, text=f"{overall_avg:.2f}%",
                     bg=CARD_BG, fg=ACCENT_CYAN, font=FONT_LABEL).pack(side="right")

            pbar_c = tk.Canvas(prog_inner, height=14, bg=INPUT_BG, highlightthickness=0)
            pbar_c.pack(fill="x", pady=(8, 14))

            def _draw_prog(canvas=pbar_c, pct=overall_avg, color=ACCENT_BLUE):
                canvas.update_idletasks()
                w = canvas.winfo_width()
                if w <= 1:
                    # Not laid out yet — retry in 50ms
                    main_frame.after(50, _draw_prog)
                    return
                canvas.delete("all")
                canvas.create_rectangle(0, 0, w, 14, fill=INPUT_BG, width=0)
                fw = (min(pct, 100) / 100) * w
                if fw > 0:
                    canvas.create_rectangle(0, 0, fw, 14, fill=color, width=0)

            # Draw on first layout and on every resize
            pbar_c.bind("<Configure>", lambda e: _draw_prog())
            main_frame.after(150, _draw_prog)

            for subject, lessons in sorted(subject_data.items()):
                avg = sum(lessons.values()) / len(lessons)
                color = (ACCENT_GREEN if avg >= 75 else
                         ACCENT_ORANGE if avg >= 50 else ACCENT_RED)
                row = tk.Frame(prog_inner, bg=HOVER_BG)
                row.pack(fill="x", pady=3)
                tk.Label(row, text=f"  \U0001f4d6  {subject}",
                         bg=HOVER_BG, fg=TEXT_PRIMARY,
                         font=FONT_BODY, width=28, anchor="w").pack(side="left", padx=4, pady=6)
                tk.Label(row, text=f"{avg:.1f}%  ({len(lessons)} lessons)",
                         bg=HOVER_BG, fg=color,
                         font=FONT_LABEL).pack(side="right", padx=12)

            # Charts row frame — placeholders shown while charts load
            charts_row = tk.Frame(content, bg=DARK_BG)
            charts_row.pack(fill="x", padx=18, pady=8)
            charts_row.grid_columnconfigure(0, weight=1)
            charts_row.grid_columnconfigure(1, weight=1)

            for col in (0, 1):
                ph = tk.Frame(charts_row, bg=CARD_BORDER, padx=1, pady=1)
                ph.grid(row=0, column=col, sticky="nsew",
                        padx=(0, 6) if col == 0 else (6, 0))
                ph_in = tk.Frame(ph, bg=CARD_BG, padx=14, pady=14, height=320)
                ph_in.pack(fill="both", expand=True)
                ph_in.pack_propagate(False)
                tk.Label(ph_in, text="📊  Rendering chart...",
                         bg=CARD_BG, fg=TEXT_MUTED,
                         font=FONT_SMALL).pack(expand=True)

            content.update_idletasks()

            # ── STEP 2: Lesson chart (deferred 80ms) ──────────
            def _build_lesson_chart():
                for w in charts_row.grid_slaves(row=0, column=0):
                    w.destroy()
                outer = tk.Frame(charts_row, bg=CARD_BORDER, padx=1, pady=1)
                outer.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
                inner = tk.Frame(outer, bg=CARD_BG, padx=14, pady=14)
                inner.pack(fill="both", expand=True)
                tk.Label(inner, text="\U0001f4c9  Lesson Progress",
                         bg=CARD_BG, fg=TEXT_PRIMARY, font=FONT_LABEL).pack(anchor="w")
                tk.Frame(inner, bg=CARD_BORDER, height=1).pack(fill="x", pady=(4, 8))

                x_labels, y_vals = [], []
                attempt_ctr = defaultdict(int)
                for _, lname, pct in all_sessions:
                    attempt_ctr[lname] += 1
                    cnt = attempt_ctr[lname]
                    x_labels.append(lname if cnt == 1 else f"{lname} ({cnt})")
                    y_vals.append(pct)
                x_labels = x_labels[-10:]
                y_vals   = y_vals[-10:]

                if not x_labels:
                    tk.Label(inner,
                             text="No lesson progress data yet.\nComplete a lesson to see progress.",
                             bg=CARD_BG, fg=TEXT_SEC,
                             font=FONT_BODY, justify="center").pack(pady=20)
                else:
                    x_pos = list(range(len(x_labels)))
                    fig, ax = plt.subplots(figsize=(5, 3.2))
                    _apply_dark_style(ax, fig)
                    ax.plot(x_pos, y_vals, marker="o", linewidth=2,
                            color=PLOT_LINE2, markerfacecolor=PLOT_LINE2,
                            markersize=6, zorder=3)
                    ax.fill_between(x_pos, y_vals, alpha=0.25, color=PLOT_LINE2)
                    ax.set_xticks(x_pos)
                    ax.set_xticklabels(x_labels, rotation=40, ha="right", fontsize=7)
                    ax.set_ylim(0, 115)
                    ax.set_yticks([0, 25, 50, 75, 100])
                    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=8)
                    ax.set_ylabel("Progress (%)", fontsize=8)
                    ax.axhline(y=100, color=ACCENT_GREEN, linewidth=0.8,
                               linestyle="--", alpha=0.5)
                    fig.tight_layout()
                    cv = FigureCanvasTkAgg(fig, master=inner)
                    cv.draw()
                    cv.get_tk_widget().pack(fill="both", expand=True)
                    plt.close(fig)

                content.update_idletasks()
                main_frame.after(60, _build_quiz_chart)

            # ── STEP 3: Quiz chart (chained after lesson chart) ─
            def _build_quiz_chart():
                for w in charts_row.grid_slaves(row=0, column=1):
                    w.destroy()
                outer = tk.Frame(charts_row, bg=CARD_BORDER, padx=1, pady=1)
                outer.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
                inner = tk.Frame(outer, bg=CARD_BG, padx=14, pady=14)
                inner.pack(fill="both", expand=True)
                tk.Label(inner, text="\U0001f9ea  Quiz Performance",
                         bg=CARD_BG, fg=TEXT_PRIMARY, font=FONT_LABEL).pack(anchor="w")
                tk.Frame(inner, bg=CARD_BORDER, height=1).pack(fill="x", pady=(4, 8))

                quiz_data = []
                if os.path.exists(QUIZ_DB):
                    try:
                        conn = sqlite3.connect(QUIZ_DB)
                        cur  = conn.cursor()
                        cur.execute("""
                            SELECT accuracy FROM quiz_performance
                            WHERE user_id=? ORDER BY timestamp ASC
                        """, (str(user_id),))
                        quiz_data = cur.fetchall()
                        conn.close()
                    except Exception:
                        pass

                if quiz_data:
                    attempts = list(range(1, len(quiz_data) + 1))
                    q_acc    = [max(0, min(100, r[0])) for r in quiz_data]
                    quiz_avg = sum(q_acc) / len(q_acc)
                    qcolor   = (ACCENT_GREEN if quiz_avg >= 75 else
                                ACCENT_ORANGE if quiz_avg >= 50 else ACCENT_RED)

                    sr = tk.Frame(inner, bg=HOVER_BG)
                    sr.pack(fill="x", pady=(0, 8))
                    tk.Label(sr,
                             text=f"  Average: {quiz_avg:.1f}%  \u00b7  {len(q_acc)} attempts",
                             bg=HOVER_BG, fg=qcolor, font=FONT_LABEL,
                             pady=6).pack(side="left", padx=8)

                    PX = 55; PH = 240; YW = 58; XTH = 40; XTI = 20
                    PT = 8;  PB = 6
                    N  = len(attempts); SW = N * PX

                    wrap = tk.Frame(inner, bg=CARD_BG)
                    wrap.pack(fill="both", expand=True)

                    row_a = tk.Frame(wrap, bg=CARD_BG)
                    row_a.pack(fill="both", expand=True)

                    yax = tk.Canvas(row_a, bg=CARD_BG, width=YW,
                                    height=PH, highlightthickness=0)
                    yax.pack(side="left", fill="y")

                    def _yax(c=yax, h=PH, w=YW, pt=PT, pb=PB):
                        c.delete("all")
                        c.create_text(10, h//2, text="Accuracy (%)",
                                      fill=PLOT_FG, font=("Courier New", 8),
                                      angle=90, anchor="center")
                        for pct in [0, 25, 50, 75, 100]:
                            y = pt + (1 - pct/100) * (h - pt - pb)
                            c.create_line(w-8, y, w-2, y, fill=PLOT_FG, width=1)
                            c.create_text(w-11, y, text=f"{pct}%",
                                          fill=PLOT_FG, font=("Courier New", 8),
                                          anchor="e")
                        c.create_line(w-2, pt, w-2, h-pb, fill=PLOT_GRID, width=1)
                    yax.after(40, _yax)

                    plot_cv = tk.Canvas(row_a, bg=PLOT_BG, height=PH,
                                        highlightthickness=0)
                    plot_cv.pack(side="left", fill="both", expand=True)

                    def _plot(c=plot_cv, h=PH, acc=q_acc,
                              sw=SW, pppt=PX, n=N, pt=PT, pb=PB):
                        c.delete("all")
                        def _xy(i):
                            return (i+0.5)*pppt, pt+(1-acc[i]/100)*(h-pt-pb)
                        for pct in [25, 50, 75, 100]:
                            gy = pt+(1-pct/100)*(h-pt-pb)
                            c.create_line(0,gy,sw,gy,fill=PLOT_GRID,dash=(4,4),width=1)
                        poly = []
                        for i in range(n): poly += list(_xy(i))
                        poly += [_xy(n-1)[0], h-pb, _xy(0)[0], h-pb]
                        c.create_polygon(poly, fill=PLOT_LINE2,
                                         stipple="gray25", outline="")
                        for i in range(n-1):
                            x1,y1=_xy(i); x2,y2=_xy(i+1)
                            c.create_line(x1,y1,x2,y2,fill=PLOT_LINE2,
                                          width=2,smooth=True)
                        R = 4
                        for i in range(n):
                            px,py=_xy(i)
                            c.create_oval(px-R,py-R,px+R,py+R,
                                          fill=PLOT_DOT,outline="white",width=1)
                        c.configure(scrollregion=(0,0,sw,h))
                        c.xview_moveto(1.0)
                    plot_cv.after(40, _plot)

                    row_b = tk.Frame(wrap, bg=CARD_BG)
                    row_b.pack(fill="x")
                    tk.Canvas(row_b, bg=CARD_BG, width=YW, height=XTH,
                              highlightthickness=0).pack(side="left")
                    xtick_cv = tk.Canvas(row_b, bg=CARD_BG, height=XTH,
                                         highlightthickness=0)
                    xtick_cv.pack(side="left", fill="x", expand=True)

                    def _xticks(c=xtick_cv, sw=SW, pppt=PX,
                                atts=attempts, th=XTH):
                        c.delete("all")
                        for i,a in enumerate(atts):
                            c.create_text((i+0.5)*pppt, 2, text=f"#{a}",
                                          fill=PLOT_FG, font=("Courier New", 7),
                                          angle=40, anchor="sw")
                        c.configure(scrollregion=(0,0,sw,th))
                        c.xview_moveto(1.0)
                    xtick_cv.after(40, _xticks)

                    row_c = tk.Frame(wrap, bg=CARD_BG, height=XTI)
                    row_c.pack(fill="x")
                    row_c.pack_propagate(False)
                    tk.Frame(row_c, bg=CARD_BG, width=YW).pack(side="left")
                    tk.Label(row_c, text="Quiz Attempt", bg=CARD_BG, fg=PLOT_FG,
                             font=("Courier New", 8),
                             anchor="center").pack(side="left", fill="both",
                                                   expand=True)

                    def _xv(*args):
                        plot_cv.xview(*args); xtick_cv.xview(*args)
                    h_bar = tk.Scrollbar(wrap, orient="horizontal",
                                         command=_xv, bg=INPUT_BG,
                                         troughcolor=DARK_BG)
                    h_bar.pack(fill="x")
                    plot_cv.configure(xscrollcommand=h_bar.set)

                    def _hs(event, pc=plot_cv, xc=xtick_cv):
                        delta = getattr(event, "delta", 0)
                        units = int(-1*(delta/40)) if delta else 0
                        if units:
                            pc.xview_scroll(units, "units")
                            xc.xview_scroll(units, "units")
                        return "break"
                    for w in (plot_cv, xtick_cv, yax, h_bar):
                        w.bind("<MouseWheel>",       _hs, add="+")
                        w.bind("<Shift-MouseWheel>", _hs, add="+")

                elif not os.path.exists(QUIZ_DB):
                    tk.Label(inner, text="Quiz database not found.\nTake a quiz first.",
                             bg=CARD_BG, fg=TEXT_SEC,
                             font=FONT_BODY, justify="center").pack(pady=20)
                else:
                    tk.Label(inner, text="No quiz attempts yet.",
                             bg=CARD_BG, fg=TEXT_SEC, font=FONT_BODY).pack(pady=20)

                content.update_idletasks()
                main_frame.after(60, _build_subject_charts)

            # ── STEP 4: Per-subject charts (one per frame) ────
            def _build_subject_charts():
                sorted_subjects = sorted(
                    set(list(subject_data.keys()) + list(sessions_by_subj.keys())))

                subj_hdr = _card("Per-Subject Lesson Progress", "\U0001f4d0")
                tk.Label(subj_hdr,
                         text="Each point = one lesson attempt  \u00b7  (N) = Nth time replaying that lesson",
                         bg=CARD_BG, fg=TEXT_SEC,
                         font=FONT_SMALL).pack(anchor="w", pady=(0, 8))

                subj_grid = tk.Frame(content, bg=DARK_BG)
                subj_grid.pack(fill="x", padx=18, pady=(0, 8))
                subj_grid.grid_columnconfigure(0, weight=1)
                subj_grid.grid_columnconfigure(1, weight=1)

                def _one(idx):
                    if idx >= len(sorted_subjects):
                        if len(sorted_subjects) % 2 != 0:
                            tk.Frame(subj_grid, bg=DARK_BG).grid(
                                row=len(sorted_subjects)//2, column=1,
                                sticky="nsew", padx=(6, 0), pady=6)
                        content.update_idletasks()
                        main_frame.after(40, _build_table)
                        return

                    subject = sorted_subjects[idx]
                    col_idx = idx % 2
                    s_outer = tk.Frame(subj_grid, bg=CARD_BORDER, padx=1, pady=1)
                    s_outer.grid(row=idx//2, column=col_idx, sticky="nsew",
                                 padx=(0,6) if col_idx==0 else (6,0), pady=6)
                    s_inner = tk.Frame(s_outer, bg=CARD_BG, padx=14, pady=14)
                    s_inner.pack(fill="both", expand=True)
                    tk.Label(s_inner, text=f"\U0001f4d6  {subject}",
                             bg=CARD_BG, fg=TEXT_PRIMARY,
                             font=FONT_LABEL).pack(anchor="w")
                    tk.Frame(s_inner, bg=CARD_BORDER, height=1).pack(fill="x", pady=(4,8))

                    xl, yv = [], []
                    ctr = defaultdict(int)
                    for lname, pct in sessions_by_subj.get(subject, []):
                        ctr[lname] += 1
                        xl.append(lname if ctr[lname]==1 else f"{lname} ({ctr[lname]})")
                        yv.append(pct)
                    xl = xl[-10:]; yv = yv[-10:]

                    avg_s  = sum(yv)/len(yv) if yv else 0
                    sc     = (ACCENT_GREEN if avg_s>=75 else
                              ACCENT_ORANGE if avg_s>=50 else ACCENT_RED)
                    sr = tk.Frame(s_inner, bg=HOVER_BG)
                    sr.pack(fill="x", pady=(0,8))
                    tk.Label(sr,
                             text=f"  Avg Progress: {avg_s:.1f}%  \u00b7  {len(yv)} session(s)",
                             bg=HOVER_BG, fg=sc, font=FONT_LABEL,
                             pady=5).pack(side="left", padx=8)

                    if xl:
                        xp = list(range(len(xl)))
                        sc2 = SUBJ_PALETTE[idx % len(SUBJ_PALETTE)]
                        fig, ax = plt.subplots(figsize=(5, 2.8))
                        _apply_dark_style(ax, fig)
                        ax.plot(xp, yv, marker="o", linewidth=2,
                                color=sc2, markerfacecolor=sc2,
                                markersize=6, zorder=3)
                        ax.fill_between(xp, yv, alpha=0.25, color=sc2)
                        ax.set_xticks(xp)
                        ax.set_xticklabels(xl, rotation=40, ha="right", fontsize=7)
                        ax.set_ylim(0, 115)
                        ax.set_yticks([0,25,50,75,100])
                        ax.set_yticklabels(["0%","25%","50%","75%","100%"], fontsize=8)
                        ax.set_ylabel("Progress (%)", fontsize=8)
                        ax.axhline(y=100, color=ACCENT_GREEN,
                                   linewidth=0.8, linestyle="--", alpha=0.4)
                        fig.tight_layout()
                        cv = FigureCanvasTkAgg(fig, master=s_inner)
                        cv.draw()
                        cv.get_tk_widget().pack(fill="both", expand=True)
                        plt.close(fig)
                    else:
                        tk.Label(s_inner, text="No lesson progress data yet.",
                                 bg=CARD_BG, fg=TEXT_SEC, font=FONT_BODY).pack(pady=10)

                    content.update_idletasks()
                    main_frame.after(30, lambda i=idx+1: _one(i))

                _one(0)

            # ── STEP 5: Lesson detail table ───────────────────
            def _build_table():
                tbl_inner = _card("Lesson Detail", "\U0001f4cb")
                hdr_row = tk.Frame(tbl_inner, bg=INPUT_BG)
                hdr_row.pack(fill="x", pady=(0, 4))
                for ct, w, anc in [("Subject",20,"w"),("Lesson",22,"w"),
                                    ("Best",14,"center"),("Played",12,"center")]:
                    tk.Label(hdr_row, text=ct, bg=INPUT_BG, fg=TEXT_SEC,
                             font=FONT_LABEL, width=w, anchor=anc,
                             padx=8, pady=5).pack(side="left")

                for subject, lessons in sorted(subject_data.items()):
                    for lesson, score in sorted(lessons.items()):
                        score  = max(0, min(100, score))
                        color  = (ACCENT_GREEN if score>=75 else
                                  ACCENT_ORANGE if score>=50 else ACCENT_RED)
                        status = "Complete" if score>=100.0 else f"{score:.1f}%"
                        plays  = play_counts.get((subject, lesson), 1)
                        p_col  = ACCENT_CYAN if plays>1 else TEXT_SEC
                        row = tk.Frame(tbl_inner, bg=HOVER_BG)
                        row.pack(fill="x", pady=2)
                        tk.Label(row, text=subject, bg=HOVER_BG, fg=TEXT_SEC,
                                 font=FONT_BODY, width=20, anchor="w",
                                 padx=8, pady=6).pack(side="left")
                        tk.Label(row, text=lesson, bg=HOVER_BG, fg=TEXT_PRIMARY,
                                 font=FONT_BODY, width=28, anchor="w").pack(side="left")
                        tk.Label(row, text=status, bg=HOVER_BG, fg=color,
                                 font=FONT_LABEL, width=14, anchor="center",
                                 padx=8).pack(side="left")
                        tk.Label(row, text=f"\u00d7{plays}", bg=HOVER_BG, fg=p_col,
                                 font=FONT_LABEL, width=12, anchor="center",
                                 padx=8).pack(side="left")

                content.update_idletasks()
                main_frame.after(100, lambda: _bind_all_children(content))

            # Kick off chain after data load
            main_frame.after(80, _build_lesson_chart)

        # Defer entire load so window renders the skeleton first
        main_frame.after(60, _do_load)


    ref_btn.bind("<Button-1>", lambda e: build_content())
    build_content()
    main_frame.after(200, lambda: _bind_all_children(content))
    return main_frame