import sys, os
sys.path = [p for p in sys.path if p not in ('', '.', os.getcwd())]
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import shutil
import sqlite3
import datetime
from collections import defaultdict

# ===================== PORTABLE PATHS =====================
BASE_DIR       = os.path.join(PROJECT, "data")
SUBJECT_DIR    = os.path.join(BASE_DIR, "subjects")
BACKUP_DIR     = os.path.join(BASE_DIR, "backup")
PROGRESS_FILE  = os.path.join(BASE_DIR, "progress.json")
STUDENTS_FILE  = os.path.join(BASE_DIR, "students.json")
PERFORMANCE_DB = os.path.join(BASE_DIR, "DB", "performance.db")
QUIZ_DB        = os.path.join(BASE_DIR, "DB", "quiz.db")
USERS_DB       = os.path.join(BASE_DIR, "DB", "users.db")   # ← added

os.makedirs(SUBJECT_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR,  exist_ok=True)

# ===================== THEME =====================
DARK_BG       = "#080d18"
CARD_BG       = "#0f1829"
CARD_BORDER   = "#1a2845"
SIDEBAR_BG    = "#07111f"
SIDEBAR_BTN   = "#0f1e35"
HOVER_BG      = "#162035"
INPUT_BG      = "#0c1422"
ACCENT_BLUE   = "#1e6fff"
ACCENT_CYAN   = "#00d4ff"
ACCENT_GREEN  = "#00c896"
ACCENT_RED    = "#ff4d6d"
ACCENT_ORANGE = "#f59e0b"
ACCENT_PURPLE = "#7b5ea7"
TEXT_PRIMARY  = "#dce8ff"
TEXT_MUTED    = "#3d5578"
TEXT_SEC      = "#7a9bc4"
TEXT_DIM      = "#4a6580"

FONT_TITLE  = ("Georgia", 20, "bold")
FONT_SUB    = ("Georgia", 11)
FONT_LABEL  = ("Georgia", 10, "bold")
FONT_BODY   = ("Courier New", 10)
FONT_SMALL  = ("Courier New", 9)
FONT_NAV    = ("Segoe UI", 11, "bold")
FONT_CARD_H = ("Georgia", 14, "bold")
FONT_DATA   = ("Courier New", 11)

# ===================== UTILITIES =====================
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


progress = load_json(PROGRESS_FILE, {})
students = load_json(STUDENTS_FILE, {})


# ===================== USERS DB HELPER =====================
def get_students_from_db():
    """
    Returns a dict keyed by str(user_id):
        { "1": {"name": "tejes", "username": "23dx49"}, ... }
    Only rows where role = 'student' are included.
    Falls back to empty dict if users.db doesn't exist.
    """
    result = {}
    if not os.path.exists(USERS_DB):
        return result
    try:
        conn = sqlite3.connect(USERS_DB)
        cur  = conn.cursor()
        cur.execute("""
            SELECT id, name, username
            FROM users
            WHERE role = 'student'
            ORDER BY id ASC
        """)
        for row in cur.fetchall():
            uid, name, username = row
            result[str(uid)] = {"name": name, "username": username}
        conn.close()
    except Exception:
        pass
    return result


# ===================== STYLED WIDGETS =====================
def dark_button(parent, text, command, color=ACCENT_BLUE, width=None):
    kwargs = dict(
        text=text, command=command,
        bg=color, fg=TEXT_PRIMARY,
        activebackground=HOVER_BG, activeforeground=ACCENT_CYAN,
        font=("Segoe UI", 10, "bold"),
        bd=0, padx=14, pady=7,
        cursor="hand2", relief="flat"
    )
    if width:
        kwargs["width"] = width
    btn = tk.Button(parent, **kwargs)

    def _enter(e): btn.config(bg=HOVER_BG, fg=ACCENT_CYAN)
    def _leave(e): btn.config(bg=color, fg=TEXT_PRIMARY)
    btn.bind("<Enter>", _enter)
    btn.bind("<Leave>", _leave)
    return btn


def section_card(parent, title, icon=""):
    outer = tk.Frame(parent, bg=CARD_BORDER, padx=1, pady=1)
    outer.pack(fill="x", padx=18, pady=8)
    inner = tk.Frame(outer, bg=CARD_BG, padx=20, pady=16)
    inner.pack(fill="both", expand=True)
    if title:
        hdr = tk.Frame(inner, bg=CARD_BG)
        hdr.pack(fill="x", pady=(0, 10))
        tk.Label(hdr, text=f"{icon}  {title}" if icon else title,
                 bg=CARD_BG, fg=TEXT_PRIMARY,
                 font=FONT_CARD_H).pack(side="left")
        tk.Frame(inner, bg=CARD_BORDER, height=1).pack(fill="x", pady=(0, 10))
    return inner


def full_card(parent, title, icon=""):
    outer = tk.Frame(parent, bg=CARD_BORDER, padx=1, pady=1)
    outer.pack(fill="both", expand=True, padx=18, pady=8)
    inner = tk.Frame(outer, bg=CARD_BG, padx=20, pady=16)
    inner.pack(fill="both", expand=True)
    if title:
        hdr = tk.Frame(inner, bg=CARD_BG)
        hdr.pack(fill="x", pady=(0, 10))
        tk.Label(hdr, text=f"{icon}  {title}" if icon else title,
                 bg=CARD_BG, fg=TEXT_PRIMARY,
                 font=FONT_CARD_H).pack(side="left")
        tk.Frame(inner, bg=CARD_BORDER, height=1).pack(fill="x", pady=(0, 10))
    return inner


def dark_listbox(parent):
    frame = tk.Frame(parent, bg=INPUT_BG,
                     highlightbackground=CARD_BORDER, highlightthickness=1)
    frame.pack(fill="both", expand=True)
    sb = tk.Scrollbar(frame, bg=CARD_BORDER, troughcolor=DARK_BG)
    sb.pack(side="right", fill="y")
    lb = tk.Listbox(frame, bg=INPUT_BG, fg=TEXT_PRIMARY,
                    selectbackground=ACCENT_BLUE, selectforeground="white",
                    font=FONT_DATA, bd=0, highlightthickness=0,
                    activestyle="none", yscrollcommand=sb.set)
    lb.pack(fill="both", expand=True, padx=4, pady=4)
    sb.config(command=lb.yview)
    return lb


def draw_bar(canvas, pct, bar_width=460, bar_height=22):
    canvas.delete("all")
    clamped = max(0.0, min(100.0, pct))
    fw = (clamped / 100.0) * bar_width
    canvas.create_rectangle(0, 0, bar_width, bar_height,
                             fill=INPUT_BG, width=0)
    color = (ACCENT_GREEN if clamped >= 75 else
             ACCENT_ORANGE if clamped >= 50 else
             ACCENT_RED if clamped > 0 else TEXT_MUTED)
    if fw > 0:
        canvas.create_rectangle(0, 0, fw, bar_height, fill=color, width=0)
    txt_col = TEXT_PRIMARY if fw > bar_width * 0.12 else TEXT_SEC
    canvas.create_text(bar_width // 2, bar_height // 2,
                       text=f"{clamped:.1f}%", fill=txt_col,
                       font=("Segoe UI", 9, "bold"))


# ===================== MAIN PAGE =====================
def page(parent, user_id=None):
    root = tk.Frame(parent, bg=DARK_BG)
    root.pack(fill="both", expand=True)

    # ===================== SIDEBAR =====================
    sidebar = tk.Frame(root, bg=SIDEBAR_BG, width=230)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    logo_area = tk.Frame(sidebar, bg=SIDEBAR_BG)
    logo_area.pack(fill="x", pady=(28, 0))

    lc = tk.Canvas(logo_area, width=44, height=44,
                   bg=SIDEBAR_BG, highlightthickness=0)
    lc.pack()
    lc.create_oval(6, 14, 30, 34, fill=ACCENT_BLUE, outline="")
    for fx, fy, fw2, fh2 in [(8,6,6,12),(14,4,6,14),(20,5,5,13),(26,8,5,11)]:
        lc.create_oval(fx, fy, fx+fw2, fy+fh2, fill=ACCENT_BLUE, outline="")
    lc.create_oval(2, 16, 10, 28, fill=ACCENT_BLUE, outline="")

    tk.Label(logo_area, text="EduSign",
             bg=SIDEBAR_BG, fg=TEXT_PRIMARY,
             font=("Georgia", 18, "bold")).pack(pady=(6, 0))
    tk.Label(logo_area, text="Teacher Dashboard",
             bg=SIDEBAR_BG, fg=TEXT_SEC,
             font=("Georgia", 9)).pack(pady=(2, 0))

    tk.Frame(sidebar, bg=CARD_BORDER, height=1).pack(fill="x", padx=18, pady=16)

    nav_frame = tk.Frame(sidebar, bg=SIDEBAR_BG)
    nav_frame.pack(fill="x", padx=10)

    active_btn = {"ref": None}

    def nav_button(text, icon, cmd):
        btn = tk.Button(nav_frame, text=f"  {icon}  {text}",
                        font=FONT_NAV, bg=SIDEBAR_BTN, fg=TEXT_SEC,
                        activebackground=ACCENT_BLUE, activeforeground="white",
                        bd=0, pady=11, anchor="w",
                        cursor="hand2", relief="flat")

        def _click():
            for child in nav_frame.winfo_children():
                child.config(bg=SIDEBAR_BTN, fg=TEXT_SEC)
            btn.config(bg=ACCENT_BLUE, fg="white")
            active_btn["ref"] = btn
            cmd()

        btn.config(command=_click)
        btn.bind("<Enter>", lambda e: btn.config(bg=HOVER_BG, fg=TEXT_PRIMARY)
                 if btn != active_btn["ref"] else None)
        btn.bind("<Leave>", lambda e: btn.config(bg=SIDEBAR_BTN, fg=TEXT_SEC)
                 if btn != active_btn["ref"] else None)
        btn.pack(fill="x", pady=3)
        return btn

    # ===================== CONTENT AREA =====================
    content = tk.Frame(root, bg=DARK_BG)
    content.pack(side="right", fill="both", expand=True)

    def clear_content():
        for w in content.winfo_children():
            w.destroy()

    def page_header(title, subtitle=""):
        hdr = tk.Frame(content, bg=DARK_BG)
        hdr.pack(fill="x", padx=20, pady=(18, 4))
        tk.Label(hdr, text=title, bg=DARK_BG, fg=TEXT_PRIMARY,
                 font=FONT_TITLE).pack(anchor="w")
        if subtitle:
            tk.Label(hdr, text=subtitle, bg=DARK_BG, fg=TEXT_SEC,
                     font=FONT_SMALL).pack(anchor="w", pady=(2, 0))
        tk.Frame(content, bg=CARD_BORDER, height=1).pack(fill="x", padx=20, pady=(6, 0))

    # ===================== SUBJECTS PAGE =====================
    def subjects_page():
        clear_content()
        page_header("\U0001f4da  Subjects", "Manage your subject folders and lessons")

        body = tk.Frame(content, bg=DARK_BG)
        body.pack(fill="both", expand=True)

        c = full_card(body, "All Subjects", "\U0001f4da")

        lb = dark_listbox(c)
        lb.config(height=12)

        def refresh():
            lb.delete(0, tk.END)
            if os.path.exists(SUBJECT_DIR):
                for s in sorted(os.listdir(SUBJECT_DIR)):
                    if os.path.isdir(os.path.join(SUBJECT_DIR, s)):
                        count = len([f for f in os.listdir(os.path.join(SUBJECT_DIR, s))
                                     if f.endswith(".txt")])
                        lb.insert(tk.END, f"  {s}   ({count} lessons)")

        refresh()

        btn_row = tk.Frame(c, bg=CARD_BG)
        btn_row.pack(fill="x", pady=(14, 0))

        def add_subject():
            name = simpledialog.askstring("Add Subject", "Subject name:")
            if name:
                os.makedirs(os.path.join(SUBJECT_DIR, name), exist_ok=True)
                refresh()

        def delete_subject():
            sel = lb.get(tk.ACTIVE)
            if sel:
                name = sel.strip().split("   ")[0]
                if messagebox.askyesno("Confirm", f"Delete '{name}' and all its lessons?"):
                    shutil.rmtree(os.path.join(SUBJECT_DIR, name), ignore_errors=True)
                    refresh()

        def open_lessons():
            sel = lb.get(tk.ACTIVE)
            if sel:
                name = sel.strip().split("   ")[0]
                lessons_page(name)

        dark_button(btn_row, "\u2795  Add Subject", add_subject, ACCENT_BLUE).pack(side="left", padx=(0, 8))
        dark_button(btn_row, "\U0001f5d1  Delete",   delete_subject, ACCENT_RED).pack(side="left", padx=(0, 8))
        dark_button(btn_row, "\U0001f4d6  Open Lessons", open_lessons, ACCENT_PURPLE).pack(side="left")

    # ===================== LESSONS PAGE =====================
    def lessons_page(subject):
        clear_content()
        page_header(f"\U0001f4d6  {subject}", "View and edit lesson content")

        body = tk.Frame(content, bg=DARK_BG)
        body.pack(fill="both", expand=True, padx=18, pady=8)

        path = os.path.join(SUBJECT_DIR, subject)
        os.makedirs(path, exist_ok=True)

        left_border = tk.Frame(body, bg=CARD_BORDER, padx=1, pady=1, width=240)
        left_border.pack(side="left", fill="y", padx=(0, 8))
        left_border.pack_propagate(False)
        left = tk.Frame(left_border, bg=CARD_BG, padx=10, pady=12)
        left.pack(fill="both", expand=True)

        tk.Label(left, text="Lessons", bg=CARD_BG, fg=TEXT_SEC,
                 font=FONT_LABEL).pack(anchor="w", pady=(0, 6))

        lb = dark_listbox(left)

        def refresh_list():
            lb.delete(0, tk.END)
            if os.path.exists(path):
                for f in sorted(os.listdir(path)):
                    if f.endswith(".txt"):
                        lb.insert(tk.END, f"  {f[:-4]}")

        refresh_list()

        list_btns = tk.Frame(left, bg=CARD_BG)
        list_btns.pack(fill="x", pady=(10, 0))

        right_border = tk.Frame(body, bg=CARD_BORDER, padx=1, pady=1)
        right_border.pack(side="left", fill="both", expand=True)
        right = tk.Frame(right_border, bg=CARD_BG)
        right.pack(fill="both", expand=True)

        ed_hdr = tk.Frame(right, bg=SIDEBAR_BG, pady=10)
        ed_hdr.pack(fill="x")
        editing_label = tk.Label(ed_hdr, text="\U0001f4dd  Select a lesson to edit",
                                  bg=SIDEBAR_BG, fg=TEXT_SEC,
                                  font=("Segoe UI", 11, "bold"))
        editing_label.pack(side="left", padx=16)
        status_var   = tk.StringVar(value="")
        status_label = tk.Label(ed_hdr, textvariable=status_var,
                                 bg=SIDEBAR_BG, fg=TEXT_SEC,
                                 font=FONT_SMALL)
        status_label.pack(side="right", padx=16)

        ed_body = tk.Frame(right, bg=INPUT_BG)
        ed_body.pack(fill="both", expand=True)
        txt_sb = tk.Scrollbar(ed_body, bg=CARD_BG, troughcolor=DARK_BG)
        txt_sb.pack(side="right", fill="y")
        text_area = tk.Text(ed_body, wrap="word",
                            font=FONT_BODY,
                            yscrollcommand=txt_sb.set,
                            relief="flat", padx=16, pady=12, undo=True,
                            state="disabled",
                            bg=INPUT_BG, fg=TEXT_PRIMARY,
                            insertbackground=ACCENT_CYAN,
                            selectbackground=ACCENT_BLUE)
        text_area.pack(fill="both", expand=True)
        txt_sb.config(command=text_area.yview)

        save_bar = tk.Frame(right, bg=SIDEBAR_BG, pady=8)
        save_bar.pack(fill="x", padx=12)

        editor_state = {"file": None, "modified": False}

        def mark_modified(event=None):
            if text_area.edit_modified():
                editor_state["modified"] = True
                status_var.set("\u25cf Unsaved changes")
                status_label.config(fg=ACCENT_ORANGE)
                text_area.edit_modified(False)

        text_area.bind("<<Modified>>", mark_modified)

        def save_lesson(event=None):
            if not editor_state["file"]:
                return
            data = text_area.get("1.0", tk.END).strip()
            with open(editor_state["file"], "w", encoding="utf-8") as f:
                f.write(data)
            editor_state["modified"] = False
            status_var.set("\u2714  Saved")
            status_label.config(fg=ACCENT_GREEN)

        save_btn = tk.Button(save_bar, text="\U0001f4be  Save  (Ctrl+S)",
                             font=("Segoe UI", 10, "bold"),
                             bg=ACCENT_BLUE, fg="white",
                             activebackground=HOVER_BG, activeforeground=ACCENT_CYAN,
                             bd=0, padx=16, pady=7, cursor="hand2",
                             command=save_lesson, state="disabled")
        save_btn.pack(side="left", padx=(0, 10))

        word_count_var = tk.StringVar(value="")
        tk.Label(save_bar, textvariable=word_count_var,
                 bg=SIDEBAR_BG, fg=TEXT_DIM,
                 font=FONT_SMALL).pack(side="right", padx=10)

        def update_word_count(event=None):
            txt   = text_area.get("1.0", tk.END).strip()
            words = len(txt.split()) if txt else 0
            word_count_var.set(f"{words} words  \u00b7  {len(txt)} chars")

        text_area.bind("<KeyRelease>", update_word_count)

        def clear_editor():
            text_area.config(state="normal")
            text_area.delete("1.0", tk.END)
            text_area.config(state="disabled")
            save_btn.config(state="disabled")
            editing_label.config(text="\U0001f4dd  Select a lesson to edit", fg=TEXT_SEC)
            status_var.set("")
            word_count_var.set("")
            editor_state["file"]     = None
            editor_state["modified"] = False

        def open_editor(filename):
            if editor_state["modified"]:
                answer = messagebox.askyesnocancel(
                    "Unsaved Changes",
                    "Save changes before switching?")
                if answer is None:
                    return
                elif answer:
                    save_lesson()
            fp = os.path.join(path, filename)
            with open(fp, "r", encoding="utf-8") as f:
                content_read = f.read()
            editor_state["file"]     = fp
            editor_state["modified"] = False
            text_area.config(state="normal")
            text_area.delete("1.0", tk.END)
            text_area.insert("1.0", content_read)
            text_area.edit_reset()
            text_area.edit_modified(False)
            save_btn.config(state="normal")
            editing_label.config(text=f"\U0001f4dd  {filename[:-4]}", fg=TEXT_PRIMARY)
            status_var.set("No changes")
            status_label.config(fg=TEXT_SEC)
            update_word_count()
            text_area.focus_set()
            content.bind_all("<Control-s>", save_lesson)

        def on_lesson_select(event):
            sel = lb.curselection()
            if sel:
                name = lb.get(sel[0]).strip() + ".txt"
                open_editor(name)

        lb.bind("<<ListboxSelect>>", on_lesson_select)

        def add_lesson():
            title = simpledialog.askstring("Add Lesson", "Lesson title:")
            if title:
                fp = os.path.join(path, f"{title}.txt")
                with open(fp, "w", encoding="utf-8") as f:
                    f.write("")
                refresh_list()
                for i in range(lb.size()):
                    if lb.get(i).strip() == title:
                        lb.selection_clear(0, tk.END)
                        lb.selection_set(i)
                        lb.activate(i)
                        break
                open_editor(f"{title}.txt")

        def delete_lesson():
            sel = lb.curselection()
            if not sel:
                return
            name = lb.get(sel[0]).strip() + ".txt"
            if messagebox.askyesno("Confirm", f"Delete '{name}'?"):
                fp = os.path.join(path, name)
                if os.path.exists(fp):
                    os.remove(fp)
                refresh_list()
                clear_editor()

        dark_button(list_btns, "\u2795  Add Lesson",    add_lesson, ACCENT_BLUE).pack(side="left", padx=(0, 6))
        dark_button(list_btns, "\U0001f5d1  Delete",    delete_lesson, ACCENT_RED).pack(side="left", padx=(0, 8))
        dark_button(list_btns, "\u2b05 Back to Subjects", subjects_page, TEXT_MUTED).pack(side="right")

    # ===================== ANALYTICS PAGE =====================
    def analytics_page():
        clear_content()
        page_header("\U0001f4ca  Analytics", "Monitor student progress and quiz performance")

        outer = tk.Frame(content, bg=DARK_BG)
        outer.pack(fill="both", expand=True)

        scroll_canvas = tk.Canvas(outer, bg=DARK_BG, highlightthickness=0)
        scrollbar     = tk.Scrollbar(outer, orient="vertical",
                                     command=scroll_canvas.yview,
                                     bg=CARD_BG, troughcolor=DARK_BG)
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        scroll_canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(scroll_canvas, bg=DARK_BG)
        _cw = scroll_canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner_configure(e):
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))

        def _on_canvas_configure(e):
            scroll_canvas.itemconfig(_cw, width=e.width)

        inner.bind("<Configure>", _on_inner_configure)
        scroll_canvas.bind("<Configure>", _on_canvas_configure)

        # ── Smooth web-like momentum scroll (Windows / macOS / Linux) ──────
        # Mimics browser inertia: each wheel event adds velocity, which
        # decays smoothly over time via an animation loop (~60 fps).
        _sv  = {"vel": 0.0, "job": None}

        def _get_content_height():
            try:
                bb = scroll_canvas.bbox("all")
                return max((bb[3] - bb[1]) if bb else 1, 1)
            except Exception:
                return 1

        def _tick():
            v = _sv["vel"]
            if abs(v) < 0.5:
                _sv["vel"] = 0.0
                _sv["job"] = None
                return
            ch = _get_content_height()
            vh = max(scroll_canvas.winfo_height(), 1)
            if ch > vh:
                cur = scroll_canvas.yview()[0]
                scroll_canvas.yview_moveto(cur + v / ch)
            _sv["vel"] *= 0.86          # friction — higher = glides longer
            _sv["job"]  = scroll_canvas.after(16, _tick)

        def _impulse(px):
            """Add px pixels of velocity and start/continue the animation."""
            if _sv["job"]:
                scroll_canvas.after_cancel(_sv["job"])
                _sv["job"] = None
            _sv["vel"] += px
            _sv["job"]  = scroll_canvas.after(16, _tick)

        def _on_mousewheel(event):
            # Windows: delta = ±120/notch; macOS trackpad: delta = ±1..±10
            d = event.delta
            if abs(d) >= 30:
                _impulse(-d * 0.25)          # Windows mouse / coarse trackpad
            else:
                _impulse(-d * 2.5)           # macOS trackpad fine steps

        def _on_trackpad(event):
            if event.num == 4:
                _impulse(-45)                # Linux scroll up
            elif event.num == 5:
                _impulse(45)                 # Linux scroll down

        def _bind_scroll_recursive(widget):
            widget.bind("<MouseWheel>", _on_mousewheel, add="+")
            widget.bind("<Button-4>",   _on_trackpad,   add="+")
            widget.bind("<Button-5>",   _on_trackpad,   add="+")
            for child in widget.winfo_children():
                _bind_scroll_recursive(child)

        # Initial bind
        _bind_scroll_recursive(scroll_canvas)
        _bind_scroll_recursive(inner)

        # Re-bind whenever new child widgets are added inside inner
        inner.bind("<Configure>", lambda e: (
            _on_inner_configure(e),
            _bind_scroll_recursive(inner)
        ), add="+")

        # Subject summary card
        subj_card_inner = section_card(inner, "Subject Overview", "\U0001f4da")

        summary = ""
        if os.path.exists(SUBJECT_DIR):
            for s in sorted(os.listdir(SUBJECT_DIR)):
                sp = os.path.join(SUBJECT_DIR, s)
                if os.path.isdir(sp):
                    count = len([f for f in os.listdir(sp) if f.endswith(".txt")])
                    summary += f"  \u2022  {s}: {count} lessons\n"

        tk.Label(subj_card_inner,
                 text=summary or "No subjects found.",
                 bg=CARD_BG, fg=TEXT_SEC,
                 font=FONT_BODY, justify="left").pack(anchor="w", pady=4)

        def export_report():
            file = filedialog.asksaveasfilename(defaultextension=".txt")
            if file:
                with open(file, "w") as f:
                    f.write(summary)
                messagebox.showinfo("Saved", "Report saved.")

        dark_button(subj_card_inner, "\U0001f4e5  Download Subject Report",
                    export_report, ACCENT_BLUE).pack(anchor="w", pady=6)

        if not os.path.exists(PERFORMANCE_DB):
            warn = section_card(inner, "", "")
            tk.Label(warn,
                     text="\u26a0   Performance database not found.\nStudents need to complete lessons first.",
                     bg=CARD_BG, fg=ACCENT_ORANGE,
                     font=FONT_BODY, justify="center").pack(pady=10)
            return

        # ── Load student info from users.db (role='student') ──────────
        # Also cross-reference with performance DB so we only show
        # students who actually have data.
        db_students = get_students_from_db()   # {str(id): {name, username}}

        try:
            conn   = sqlite3.connect(PERFORMANCE_DB)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT user_id FROM performance")
            perf_user_ids = {str(row[0]) for row in cursor.fetchall()}
            conn.close()
        except Exception as e:
            tk.Label(inner, text=f"DB error: {e}",
                     bg=DARK_BG, fg=ACCENT_RED).pack(pady=10)
            return

        if not perf_user_ids:
            tk.Label(inner, text="No student performance data available.",
                     bg=DARK_BG, fg=TEXT_SEC,
                     font=FONT_BODY).pack(pady=20)
            return

        # Build ordered list: students in users.db who have performance data.
        # If a user_id has performance data but isn't in users.db, still show them.
        known_ids   = sorted(db_students.keys(), key=lambda x: int(x))
        unknown_ids = sorted(perf_user_ids - set(known_ids), key=lambda x: int(x))
        all_ids     = [uid for uid in known_ids if uid in perf_user_ids] + unknown_ids

        if not all_ids:
            tk.Label(inner, text="No student performance data available.",
                     bg=DARK_BG, fg=TEXT_SEC,
                     font=FONT_BODY).pack(pady=20)
            return

        # label->uid reverse map built while generating labels
        _label_to_uid = {}

        def student_label(uid):
            """tejes (23dx49)"""
            if uid in db_students:
                info  = db_students[uid]
                label = f"{info['name']} ({info['username']})"
            else:
                label = f"Unknown ({uid})"
            _label_to_uid[label] = uid
            return label

        # ── Student selector card ──────────────────────────────────────────────
        sel_outer = tk.Frame(inner, bg=CARD_BORDER, padx=1, pady=1)
        sel_outer.pack(fill="x", padx=18, pady=8)
        sel_inner = tk.Frame(sel_outer, bg=CARD_BG, padx=20, pady=16)
        sel_inner.pack(fill="both", expand=True)

        # Card title row
        sel_card_hdr = tk.Frame(sel_inner, bg=CARD_BG)
        sel_card_hdr.pack(fill="x", pady=(0, 8))
        tk.Label(sel_card_hdr, text="👤  Select Student",
                 bg=CARD_BG, fg=TEXT_PRIMARY,
                 font=FONT_CARD_H).pack(side="left")
        tk.Label(sel_card_hdr,
                 text=f"👥  {len(all_ids)} student{'s' if len(all_ids) != 1 else ''}",
                 bg=CARD_BG, fg=TEXT_SEC, font=FONT_SMALL).pack(side="right")
        tk.Frame(sel_inner, bg=CARD_BORDER, height=1).pack(fill="x", pady=(0, 12))

        # Dropdown row with blue accent border
        sel_row_wrap = tk.Frame(sel_inner, bg=ACCENT_BLUE, padx=1, pady=1)
        sel_row_wrap.pack(fill="x")
        sel_row = tk.Frame(sel_row_wrap, bg=INPUT_BG, padx=8, pady=6)
        sel_row.pack(fill="x")

        tk.Label(sel_row, text="👤",
                 bg=INPUT_BG, fg=ACCENT_CYAN,
                 font=("Segoe UI Emoji", 13)).pack(side="left", padx=(4, 8))

        student_var     = tk.StringVar()
        student_options = [student_label(uid) for uid in all_ids]
        student_var.set(student_options[0])

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.TCombobox",
                        fieldbackground=INPUT_BG,
                        background=INPUT_BG,
                        foreground=TEXT_PRIMARY,
                        selectbackground=ACCENT_BLUE,
                        selectforeground="white",
                        arrowcolor=ACCENT_CYAN,
                        borderwidth=0,
                        relief="flat")
        style.map("Dark.TCombobox",
                  fieldbackground=[("readonly", INPUT_BG)],
                  foreground=[("readonly", TEXT_PRIMARY)],
                  background=[("readonly", INPUT_BG)])

        student_dropdown = ttk.Combobox(sel_row, textvariable=student_var,
                                         values=student_options,
                                         state="readonly", width=32,
                                         style="Dark.TCombobox",
                                         font=("Georgia", 11, "bold"))
        student_dropdown.pack(side="left", pady=2)

        def _uid_from_label(label_str):
            """Reverse-lookup uid from label 'tejes (23dx49)'"""
            return _label_to_uid.get(label_str.strip(), label_str.strip())

        # =====================================================
        # DOWNLOAD STUDENT REPORT
        # =====================================================
        def download_student_report():
            selected = student_var.get()
            uid      = _uid_from_label(selected)

            info     = db_students.get(uid, {})
            name     = info.get("name",     "N/A")
            username = info.get("username", uid)
            email    = info.get("email",    "N/A")

            # Fetch best lesson score per lesson
            lesson_rows = []
            try:
                conn   = sqlite3.connect(PERFORMANCE_DB)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT subject, lesson_name, MAX(accuracy) as best, timestamp
                    FROM performance WHERE user_id=?
                    GROUP BY subject, lesson_name
                    ORDER BY subject, lesson_name ASC
                """, (str(uid),))
                lesson_rows = cursor.fetchall()
                conn.close()
            except Exception:
                pass

            # Fetch quiz performance
            quiz_rows = []
            if os.path.exists(QUIZ_DB):
                try:
                    conn   = sqlite3.connect(QUIZ_DB)
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT accuracy, timestamp FROM quiz_performance
                        WHERE user_id=? ORDER BY timestamp ASC
                    """, (str(uid),))
                    quiz_rows = cursor.fetchall()
                    conn.close()
                except Exception:
                    pass

            now  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sep  = "=" * 62
            thin = "-" * 62

            lines = [
                sep,
                "    EDUSIGN  —  STUDENT PERFORMANCE REPORT",
                sep,
                f"  Generated   : {now}",
                f"  Student     : {name} ({username})",
                f"  Email       : {email}",
                sep,
                "",
                "  LESSON PROGRESS",
                thin,
            ]

            if lesson_rows:
                subject_data = defaultdict(list)
                for subject, lesson, best, ts in lesson_rows:
                    subject_data[subject].append((lesson, best, ts))

                all_scores = []
                for subject, lessons in sorted(subject_data.items()):
                    avg = sum(s for _, s, _ in lessons) / len(lessons)
                    lines.append(f"\n  Subject : {subject}   (avg: {avg:.1f}%)")
                    lines.append("  " + thin)
                    for lesson, best, ts in sorted(lessons):
                        status = "Complete" if best >= 100.0 else f"{best:.1f}% done"
                        lines.append(f"    {lesson:<36} {status:<18} last saved: {ts}")
                        all_scores.append(best)

                overall_avg = sum(all_scores) / len(all_scores)
                lines += [
                    "",
                    thin,
                    f"  Overall Lesson Average   : {overall_avg:.1f}%",
                    f"  Total Lessons Attempted  : {len(lesson_rows)}",
                ]
            else:
                lines.append("  No lesson data found for this student.")

            lines += ["", sep, "  QUIZ PERFORMANCE", thin]

            if quiz_rows:
                for i, (acc, ts) in enumerate(quiz_rows, 1):
                    grade = ("Excellent"        if acc >= 90 else
                             "Good"             if acc >= 75 else
                             "Average"          if acc >= 50 else
                             "Needs Improvement")
                    lines.append(f"    Attempt #{i:<4}  {acc:>6.1f}%   {grade:<22}  {ts}")
                quiz_avg = sum(r[0] for r in quiz_rows) / len(quiz_rows)
                lines += [
                    "",
                    thin,
                    f"  Quiz Average Score   : {quiz_avg:.1f}%",
                    f"  Total Quiz Attempts  : {len(quiz_rows)}",
                ]
            else:
                lines.append("  No quiz data found for this student.")

            lines += ["", sep, "  END OF REPORT", sep]

            report_text  = "\n".join(lines)
            default_name = (
                f"report_{name.replace(' ','_')}_roll{uid}_"
                f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            save_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                initialfile=default_name,
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
                title="Save Student Report"
            )
            if save_path:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(report_text)
                messagebox.showinfo(
                    "Report Saved",
                    f"Report for '{name} ({username})' saved to:\n{save_path}"
                )

        dark_button(sel_row, "\U0001f4e5  Download Report",
                    download_student_report, ACCENT_GREEN).pack(side="left", padx=(12, 0), pady=4)

        perf_panel = tk.Frame(inner, bg=DARK_BG)
        perf_panel.pack(fill="both", expand=True)

        def get_total_lessons_per_subject():
            totals = {}
            if os.path.exists(SUBJECT_DIR):
                for subj in os.listdir(SUBJECT_DIR):
                    sp = os.path.join(SUBJECT_DIR, subj)
                    if os.path.isdir(sp):
                        totals[subj] = len([f for f in os.listdir(sp)
                                            if f.endswith(".txt")])
            return totals

        def fetch_student_data(uid):
            try:
                conn   = sqlite3.connect(PERFORMANCE_DB)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT subject, lesson_name, accuracy, timestamp
                    FROM performance WHERE user_id=?
                    ORDER BY timestamp ASC
                """, (str(uid),))
                rows = cursor.fetchall()
                conn.close()
            except Exception:
                return defaultdict(dict)
            subject_data = defaultdict(dict)
            for subject, lesson, score, timestamp in rows:
                subject_data[subject][lesson] = max(0.0, min(100.0, float(score)))
            return subject_data

        def fetch_quiz_data(uid):
            if not os.path.exists(QUIZ_DB):
                return []
            try:
                conn   = sqlite3.connect(QUIZ_DB)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT accuracy, timestamp FROM quiz_performance
                    WHERE user_id=? ORDER BY timestamp ASC
                """, (str(uid),))
                rows = cursor.fetchall()
                conn.close()
                return [(max(0.0, min(100.0, float(acc))), ts) for acc, ts in rows]
            except Exception:
                return []

        live_refs = {
            "overall_bar":    None,
            "overall_label":  None,
            "subj_bars":      {},
            "subj_labels":    {},
            "lesson_bars":    {},
            "quiz_rows_frame":None,
            "quiz_avg_label": None,
            "refresh_ts":     None,
            "current_uid":    None,
        }

        def build_performance_ui(uid):
            for w in perf_panel.winfo_children():
                w.destroy()
            live_refs["subj_bars"].clear()
            live_refs["subj_labels"].clear()
            live_refs["lesson_bars"].clear()
            live_refs["overall_bar"]     = None
            live_refs["overall_label"]   = None
            live_refs["quiz_rows_frame"] = None
            live_refs["quiz_avg_label"]  = None
            live_refs["refresh_ts"]      = None
            live_refs["current_uid"]     = uid

            subject_data   = fetch_student_data(uid)
            total_per_subj = get_total_lessons_per_subject()

            if not subject_data:
                tk.Label(perf_panel, text="No lesson data for this student.",
                         bg=DARK_BG, fg=TEXT_SEC,
                         font=FONT_BODY).pack(pady=20)
                return

            prog_inner = section_card(perf_panel, "Overall Lesson Progress", "\U0001f4c8")

            top_row = tk.Frame(prog_inner, bg=CARD_BG)
            top_row.pack(fill="x", pady=(0, 4))

            overall_lbl_var = tk.StringVar()
            tk.Label(top_row, textvariable=overall_lbl_var,
                     font=("Segoe UI", 11, "bold"),
                     bg=CARD_BG, fg=ACCENT_CYAN).pack(side="left")
            live_refs["overall_label"] = overall_lbl_var

            def on_manual_refresh():
                current_uid = live_refs.get("current_uid")
                if current_uid:
                    refresh_performance_data(current_uid)

            refresh_btn = tk.Button(
                top_row,
                text="\u21bb  Refresh",
                command=on_manual_refresh,
                bg=SIDEBAR_BTN, fg=ACCENT_CYAN,
                activebackground=HOVER_BG, activeforeground=ACCENT_CYAN,
                font=("Segoe UI", 9, "bold"),
                bd=0, padx=10, pady=4,
                cursor="hand2", relief="flat"
            )
            refresh_btn.pack(side="right")
            refresh_btn.bind("<Enter>", lambda e: refresh_btn.config(bg=HOVER_BG))
            refresh_btn.bind("<Leave>", lambda e: refresh_btn.config(bg=SIDEBAR_BTN))

            overall_bar = tk.Canvas(prog_inner, width=460, height=26,
                                    bg=INPUT_BG, highlightthickness=0)
            overall_bar.pack(anchor="w", pady=8)
            live_refs["overall_bar"] = overall_bar

            refresh_lbl_var = tk.StringVar(value="")
            tk.Label(prog_inner, textvariable=refresh_lbl_var,
                     bg=CARD_BG, fg=TEXT_MUTED,
                     font=FONT_SMALL).pack(anchor="e")
            live_refs["refresh_ts"] = refresh_lbl_var

            for subject in sorted(subject_data.keys()):
                lessons = subject_data[subject]
                total   = max(total_per_subj.get(subject, len(lessons)), 1)

                subj_inner = section_card(perf_panel, subject, "\U0001f4d6")

                subj_hdr = tk.Frame(subj_inner, bg=CARD_BG)
                subj_hdr.pack(fill="x")
                subj_var = tk.StringVar()
                tk.Label(subj_hdr, textvariable=subj_var,
                         font=FONT_SMALL, bg=CARD_BG,
                         fg=TEXT_SEC).pack(side="right")
                live_refs["subj_labels"][subject] = subj_var

                subj_bar = tk.Canvas(subj_inner, width=460, height=20,
                                     bg=INPUT_BG, highlightthickness=0)
                subj_bar.pack(anchor="w", pady=(4, 10))
                live_refs["subj_bars"][subject] = subj_bar

                for lesson in sorted(lessons.keys()):
                    row = tk.Frame(subj_inner, bg=CARD_BG)
                    row.pack(fill="x", pady=2)
                    tk.Label(row, text=f"  {lesson}",
                             font=FONT_BODY, bg=CARD_BG, fg=TEXT_SEC,
                             width=30, anchor="w").pack(side="left")
                    mini_c = tk.Canvas(row, width=200, height=14,
                                       bg=INPUT_BG, highlightthickness=0)
                    mini_c.pack(side="left", padx=8)
                    live_refs["lesson_bars"][(subject, lesson)] = mini_c

            quiz_inner = section_card(perf_panel, "Quiz Performance", "\U0001f9ea")

            quiz_rows_frame = tk.Frame(quiz_inner, bg=CARD_BG)
            quiz_rows_frame.pack(fill="x", pady=(4, 0))
            live_refs["quiz_rows_frame"] = quiz_rows_frame

            quiz_avg_var = tk.StringVar()
            tk.Label(quiz_inner, textvariable=quiz_avg_var,
                     font=("Segoe UI", 11, "bold"),
                     bg=CARD_BG, fg=ACCENT_CYAN).pack(anchor="w", pady=(8, 0))
            live_refs["quiz_avg_label"] = quiz_avg_var

            # Re-bind scroll to all newly built performance widgets
            _bind_scroll_recursive(perf_panel)

        def refresh_performance_data(uid):
            if not live_refs["overall_bar"]:
                return

            subject_data   = fetch_student_data(uid)
            total_per_subj = get_total_lessons_per_subject()

            if not subject_data:
                return

            total_lessons_all = sum(max(total_per_subj.get(s, len(ls)), 1)
                                    for s, ls in subject_data.items())
            completed_all     = sum(len(ls) for ls in subject_data.values())
            overall_pct       = (min(100.0, (completed_all / total_lessons_all) * 100)
                                 if total_lessons_all > 0 else 0.0)

            draw_bar(live_refs["overall_bar"], overall_pct, bar_width=460, bar_height=26)
            if live_refs["overall_label"]:
                live_refs["overall_label"].set(
                    f"{completed_all} / {total_lessons_all} lessons  ({overall_pct:.1f}%)")

            if live_refs["refresh_ts"]:
                live_refs["refresh_ts"].set(
                    f"Last updated: {datetime.datetime.now().strftime('%H:%M:%S')}")

            for subject, lessons in subject_data.items():
                total     = max(total_per_subj.get(subject, len(lessons)), 1)
                completed = len(lessons)
                subj_pct  = min(100.0, (completed / total) * 100)

                if subject in live_refs["subj_bars"]:
                    draw_bar(live_refs["subj_bars"][subject],
                             subj_pct, bar_width=460, bar_height=20)

                if subject in live_refs["subj_labels"]:
                    avg_acc = sum(lessons.values()) / len(lessons) if lessons else 0
                    live_refs["subj_labels"][subject].set(
                        f"{completed}/{total} lessons  |  Avg: {avg_acc:.1f}%")

                for lesson, score in lessons.items():
                    key = (subject, lesson)
                    if key in live_refs["lesson_bars"]:
                        draw_bar(live_refs["lesson_bars"][key],
                                 score, bar_width=200, bar_height=14)

            quiz_rows = fetch_quiz_data(uid)
            qf = live_refs["quiz_rows_frame"]
            if qf:
                for w in qf.winfo_children():
                    w.destroy()
                if not quiz_rows:
                    tk.Label(qf, text="No quiz attempts found.",
                             bg=CARD_BG, fg=TEXT_SEC,
                             font=FONT_BODY).pack(anchor="w")
                else:
                    hdr = tk.Frame(qf, bg=INPUT_BG)
                    hdr.pack(fill="x", pady=(0, 4))
                    for col_text, w2 in [("Attempt", 10), ("Accuracy", 12), ("Timestamp", 0)]:
                        tk.Label(hdr, text=col_text,
                                 font=FONT_LABEL, bg=INPUT_BG, fg=TEXT_SEC,
                                 width=w2 if w2 else None,
                                 padx=6, pady=4).pack(side="left")
                    for i, (acc, ts) in enumerate(quiz_rows, 1):
                        clr = (ACCENT_GREEN if acc >= 75 else
                               ACCENT_ORANGE if acc >= 50 else ACCENT_RED)
                        r = tk.Frame(qf, bg=CARD_BG)
                        r.pack(fill="x", pady=1)
                        tk.Label(r, text=f"#{i}",
                                 font=FONT_BODY, bg=CARD_BG,
                                 fg=TEXT_SEC, width=10).pack(side="left")
                        tk.Label(r, text=f"{acc:.1f}%",
                                 font=("Segoe UI", 10, "bold"),
                                 fg=clr, bg=CARD_BG, width=12).pack(side="left")
                        tk.Label(r, text=ts,
                                 font=FONT_BODY, fg=TEXT_DIM, bg=CARD_BG).pack(side="left")
                    qa = sum(r[0] for r in quiz_rows) / len(quiz_rows)
                    if live_refs["quiz_avg_label"]:
                        live_refs["quiz_avg_label"].set(f"Average Quiz Score: {qa:.1f}%")

            # Re-bind scroll after quiz rows are rebuilt
            _bind_scroll_recursive(perf_panel)

        def load_student_performance(event=None):
            selected = student_var.get()
            uid      = _uid_from_label(selected)
            build_performance_ui(uid)
            refresh_performance_data(uid)

        student_dropdown.bind("<<ComboboxSelected>>", load_student_performance)
        load_student_performance()

    # ===================== STORAGE PAGE =====================
    def storage_page():
        clear_content()
        page_header("\U0001f5c2  Storage", "Backup and manage lesson data")

        body = tk.Frame(content, bg=DARK_BG)
        body.pack(fill="both", expand=True)

        c = section_card(body, "Backup", "\U0001f4be")

        tk.Label(c, text="Create a .zip backup of all subjects and lessons.",
                 bg=CARD_BG, fg=TEXT_SEC, font=FONT_BODY).pack(anchor="w", pady=(0, 12))

        def backup():
            shutil.make_archive(os.path.join(BACKUP_DIR, "backup"), "zip", BASE_DIR)
            messagebox.showinfo("Backup", "Backup created in data/backup/")

        dark_button(c, "\U0001f4be  Create Backup Now", backup, ACCENT_BLUE).pack(anchor="w")

    # ===================== BUILD NAV =====================
    nav_button("Subjects",  "\U0001f4da", subjects_page)
    nav_button("Analytics", "\U0001f4ca", analytics_page)
    nav_button("Storage",   "\U0001f5c2", storage_page)

    tk.Frame(sidebar, bg=SIDEBAR_BG).pack(fill="both", expand=True)
    tk.Frame(sidebar, bg=CARD_BORDER, height=1).pack(fill="x", padx=14, pady=(0, 8))

    tk.Label(sidebar,
             text="\u00a9 EduSign \u00b7 Final Year Project",
             bg=SIDEBAR_BG, fg=TEXT_MUTED,
             font=("Courier New", 8)).pack(side="bottom", pady=(0, 10))

    subjects_page()
    return root


# ===================== RUN =====================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("EduSign \u2013 Teacher Dashboard")
    root.geometry("1200x700")
    root.configure(bg="#080d18")
    page(root)
    root.mainloop()