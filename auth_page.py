import sys, os
sys.path = [p for p in sys.path if p not in ('', '.', os.getcwd())]
PROJECT = os.path.dirname(os.path.abspath(__file__))
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

import tkinter as tk
from tkinter import messagebox
import sqlite3, re

# ── Theme ──────────────────────────────────────────────────────────────────────
DARK_BG       = "#080d18"
CARD_BG       = "#0f1829"
CARD_BORDER   = "#1a2845"
HOVER_BG      = "#162035"
INPUT_BG      = "#0c1422"
ACCENT_BLUE   = "#1e6fff"
ACCENT_CYAN   = "#00d4ff"
ACCENT_PURPLE = "#7b5ea7"
TEXT_PRIMARY  = "#dce8ff"
TEXT_MUTED    = "#3d5578"
TEXT_SEC      = "#7a9bc4"

FONT_TITLE = ("Georgia", 22, "bold")
FONT_SUB   = ("Georgia", 11)
FONT_LABEL = ("Georgia", 10, "bold")
FONT_BODY  = ("Courier New", 10)
FONT_SMALL = ("Courier New", 9)

# ── Database ───────────────────────────────────────────────────────────────────
DB_FOLDER = os.path.join(PROJECT, "data", "DB")
os.makedirs(DB_FOLDER, exist_ok=True)
DB_PATH = os.path.join(DB_FOLDER, "users.db")


def _get_db():
    """Return a fresh connection + cursor each time (thread/reuse safe)."""
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, username TEXT UNIQUE, password TEXT, role TEXT)""")
    conn.commit()
    return conn, cur


# ── Helpers ────────────────────────────────────────────────────────────────────
def _draw_hand(canvas, x, y, color, size=1.0):
    s = size
    canvas.create_oval(x+4*s, y+12*s, x+26*s, y+30*s, fill=color, outline="")
    for fx,fy,fw,fh in [(6,4,6,14),(12,2,6,16),(18,3,6,15),(24,6,5,13)]:
        canvas.create_oval(x+fx*s, y+fy*s,
                           x+(fx+fw)*s, y+(fy+fh)*s, fill=color, outline="")
    canvas.create_oval(x-2*s, y+14*s, x+8*s, y+26*s, fill=color, outline="")


def _entry(parent, placeholder):
    frame = tk.Frame(parent, bg=INPUT_BG,
                     highlightbackground=CARD_BORDER, highlightthickness=1)
    frame.pack(fill="x", pady=5)
    ent = tk.Entry(frame, bd=0, bg=INPUT_BG, fg=TEXT_MUTED,
                   insertbackground=ACCENT_CYAN, font=FONT_BODY)
    ent.pack(ipady=10, padx=12, fill="x")
    ent.insert(0, placeholder)
    ent._ph = placeholder

    def fi(e):
        if ent.get() == ent._ph:
            ent.delete(0, "end"); ent.config(fg=TEXT_PRIMARY)
            frame.config(highlightbackground=ACCENT_BLUE)

    def fo(e):
        if ent.get() == "":
            ent.insert(0, ent._ph); ent.config(fg=TEXT_MUTED)
            frame.config(highlightbackground=CARD_BORDER)

    ent.bind("<FocusIn>", fi); ent.bind("<FocusOut>", fo)
    return frame, ent


def _pwd_entry(parent):
    frame = tk.Frame(parent, bg=INPUT_BG,
                     highlightbackground=CARD_BORDER, highlightthickness=1)
    frame.pack(fill="x", pady=5)
    pv = tk.StringVar()

    def _lim(*_):
        if len(pv.get()) > 8:
            pv.set(pv.get()[:8])

    pv.trace_add("write", _lim)
    ent = tk.Entry(frame, textvariable=pv, bd=0,
                   bg=INPUT_BG, fg=TEXT_MUTED,
                   insertbackground=ACCENT_CYAN, font=FONT_BODY)
    ent.pack(ipady=10, padx=12, fill="x")
    ent.insert(0, "Password")

    def fi(e):
        if ent.get() == "Password":
            ent.delete(0, "end"); ent.config(fg=TEXT_PRIMARY, show="\u25cf")
            frame.config(highlightbackground=ACCENT_BLUE)

    def fo(e):
        if ent.get() == "":
            ent.insert(0, "Password"); ent.config(fg=TEXT_MUTED, show="")
            frame.config(highlightbackground=CARD_BORDER)

    ent.bind("<FocusIn>", fi); ent.bind("<FocusOut>", fo)
    return frame, ent, pv


# ── auth_page ──────────────────────────────────────────────────────────────────
def auth_page(root, on_success):
    root.configure(bg=DARK_BG)
    outer = tk.Frame(root, bg=DARK_BG)
    outer.pack(fill="both", expand=True)

    # ── LEFT panel ─────────────────────────────────────────────────────────────
    left = tk.Frame(outer, bg="#050911", width=400)
    left.pack(side="left", fill="y")
    left.pack_propagate(False)
    tk.Frame(left, bg="#050911").pack(expand=True, fill="both")
    mid = tk.Frame(left, bg="#050911")
    mid.pack()

    lc = tk.Canvas(mid, width=90, height=90,
                   bg="#050911", highlightthickness=0)
    lc.pack()
    _draw_hand(lc, 12, 10, ACCENT_BLUE, size=2.2)

    tk.Label(mid, text="EduSign",
             bg="#050911", fg=TEXT_PRIMARY,
             font=("Georgia", 30, "bold")).pack(pady=(10, 4))
    tk.Label(mid, text="Indian Sign Language\nLearning Platform",
             bg="#050911", fg=TEXT_SEC,
             font=FONT_SUB, justify="center").pack()
    tk.Frame(mid, bg=CARD_BORDER, height=1).pack(fill="x", pady=14)

    for icon, label in [("\U0001f590", "Sign Recognition"),
                        ("\U0001f4da", "Interactive Lessons"),
                        ("\U0001f3af", "Quiz & Practice"),
                        ("\U0001f4ca", "Performance Tracking")]:
        r = tk.Frame(mid, bg="#050911")
        r.pack(pady=5, anchor="w")
        b = tk.Frame(r, bg=CARD_BG, padx=8, pady=6)
        b.pack(side="left")
        tk.Label(b, text=icon, bg=CARD_BG,
                 font=("Segoe UI Emoji", 13)).pack()
        tk.Label(r, text=f"  {label}", bg="#050911",
                 fg=TEXT_SEC, font=FONT_BODY).pack(side="left")

    dc = tk.Canvas(mid, width=220, height=66,
                   bg="#050911", highlightthickness=0)
    dc.pack(pady=18)
    for ri in range(3):
        for ci in range(11):
            xd = 8 + ci * 20; yd = 8 + ri * 20
            col = [ACCENT_BLUE, ACCENT_CYAN, ACCENT_PURPLE][(ri + ci) % 3]
            dc.create_oval(xd, yd, xd + 6, yd + 6, fill=col, outline="")
    tk.Frame(left, bg="#050911").pack(expand=True, fill="both")

    # ── RIGHT panel ────────────────────────────────────────────────────────────
    right = tk.Frame(outer, bg=DARK_BG)
    right.pack(side="left", fill="both", expand=True)
    tk.Label(right, text="\u00a9 EduSign \u00b7 Final Year Project",
             bg=DARK_BG, fg=TEXT_MUTED,
             font=FONT_SMALL).pack(side="bottom", pady=10)

    # Center the card vertically and horizontally
    center = tk.Frame(right, bg=DARK_BG)
    center.place(relx=0.5, rely=0.5, anchor="center")

    cb = tk.Frame(center, bg=CARD_BORDER, padx=1, pady=1)
    cb.pack()
    card = tk.Frame(cb, bg=CARD_BG, padx=36, pady=28)
    card.pack(fill="both")

    tv = tk.StringVar(value="Welcome back")
    sv = tk.StringVar(value="Sign in to your account")
    tk.Label(card, textvariable=tv,
             bg=CARD_BG, fg=TEXT_PRIMARY, font=FONT_TITLE).pack(anchor="w")
    tk.Label(card, textvariable=sv,
             bg=CARD_BG, fg=TEXT_SEC, font=FONT_SMALL).pack(anchor="w", pady=(2, 10))
    tk.Frame(card, bg=ACCENT_BLUE, height=2).pack(fill="x", pady=(0, 14))

    is_signup = tk.BooleanVar(value=False)
    name_frame, name_entry = _entry(card, "Full name")
    name_frame.pack_forget()
    _, uentry = _entry(card, "Username  (e.g. 12ab34)")
    _, pentry, pwd_var = _pwd_entry(card)

    tk.Label(card, text="\u26a0  8 chars \u00b7 at least one uppercase",
             bg=CARD_BG, fg=TEXT_MUTED, font=FONT_SMALL).pack(anchor="w", pady=(0, 6))

    role = tk.StringVar(value="student")
    rf = tk.Frame(card, bg=CARD_BG)
    rf.pack(fill="x", pady=(0, 12))
    tk.Label(rf, text="Role:", bg=CARD_BG, fg=TEXT_SEC,
             font=FONT_LABEL).pack(side="left")
    for val, lbl in [("student", "Student"), ("teacher", "Teacher")]:
        tk.Radiobutton(rf, text=lbl, variable=role, value=val,
                       bg=CARD_BG, fg=TEXT_PRIMARY,
                       selectcolor=CARD_BG,
                       activebackground=CARD_BG,
                       activeforeground=TEXT_PRIMARY,
                       font=FONT_BODY).pack(side="left", padx=10)

    def submit():
        username = uentry.get().strip()
        pwd      = pwd_var.get().strip()
        name     = name_entry.get().strip()
        if username == "Username  (e.g. 12ab34)":
            username = ""
        if not re.match(r"^\d{2}[A-Za-z]{2}\d{2}$", username):
            messagebox.showerror("Error", "Username must be like 12ab34"); return
        if len(pwd) != 8:
            messagebox.showerror("Error", "Password must be exactly 8 characters"); return
        if not any(c.isupper() for c in pwd):
            messagebox.showerror("Error", "Password needs at least one uppercase"); return

        conn, cursor = _get_db()
        if is_signup.get():
            if not name or name == "Full name":
                conn.close()
                messagebox.showerror("Error", "Full name required"); return
            try:
                cursor.execute(
                    "INSERT INTO users (name,username,password,role) VALUES (?,?,?,?)",
                    (name, username, pwd, role.get()))
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "Account created! Please log in.")
                toggle()
            except sqlite3.IntegrityError:
                conn.close()
                messagebox.showerror("Error", "Username already exists")
        else:
            cursor.execute(
                "SELECT id,name,role FROM users WHERE username=? AND password=?",
                (username, pwd))
            user = cursor.fetchone()
            conn.close()
            if not user:
                messagebox.showerror("Error", "Invalid credentials"); return
            uid, uname, urole = user
            root.destroy()
            on_success(uid, uname, urole)

    ab = tk.Button(card, text="Sign In",
                   bg=ACCENT_BLUE, fg="white",
                   activebackground="#155bcc", activeforeground="white",
                   bd=0, pady=11,
                   font=("Georgia", 11, "bold"),
                   cursor="hand2", command=submit)
    ab.pack(fill="x")
    ab.bind("<Enter>", lambda e: ab.config(bg="#155bcc"))
    ab.bind("<Leave>", lambda e: ab.config(bg=ACCENT_BLUE))
    root.bind("<Return>", lambda e: submit())

    sl = tk.Label(card, bg=CARD_BG, fg=ACCENT_CYAN,
                  font=FONT_SMALL, cursor="hand2")
    sl.pack(pady=(12, 0))

    def toggle(e=None):
        if is_signup.get():
            is_signup.set(False)
            name_frame.pack_forget()
            tv.set("Welcome back"); sv.set("Sign in to your account")
            ab.config(text="Sign In")
            sl.config(text="Don't have an account?  Sign up \u2192")
        else:
            is_signup.set(True)
            name_frame.pack(fill="x", pady=5, before=uentry.master)
            tv.set("Create account"); sv.set("Join EduSign today")
            ab.config(text="Sign Up")
            sl.config(text="Already have an account?  Sign in \u2192")

    sl.config(text="Don't have an account?  Sign up \u2192")
    sl.bind("<Button-1>", toggle)


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x650")
    root.title("EduSign – Auth")
    auth_page(root, lambda u, n, r: print(f"{u} {n} {r}"))
    root.mainloop()