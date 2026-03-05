import sys, os
sys.path = [p for p in sys.path if p not in ('', '.', os.getcwd())]
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

import tkinter as tk
import subprocess

# ============================
# THEME
# ============================
DARK_BG      = "#080d18"
CARD_BG      = "#0f1829"
CARD_BORDER  = "#1a2845"
HOVER_BG     = "#162035"
ACCENT_BLUE  = "#1e6fff"
ACCENT_CYAN  = "#00d4ff"
ACCENT_GREEN = "#00c896"
TEXT_PRIMARY = "#dce8ff"
TEXT_SEC     = "#7a9bc4"
TEXT_MUTED   = "#3d5578"

FONT_TITLE = ("Georgia", 20, "bold")
FONT_BODY  = ("Courier New", 10)
FONT_SMALL = ("Courier New", 9)


def page(parent, user_id):
    frame = tk.Frame(parent, bg=DARK_BG)
    frame.pack(fill="both", expand=True)

    # ── Header ───────────────────────────────────────────────
    hdr = tk.Frame(frame, bg=DARK_BG)
    hdr.pack(fill="x", padx=22, pady=(18, 4))
    tk.Label(hdr, text="\U0001f590  Avatar  \u2013  Text \u2192 Sign",
             bg=DARK_BG, fg=TEXT_PRIMARY, font=FONT_TITLE).pack(anchor="w")
    tk.Label(hdr, text="Convert text into Indian Sign Language animations",
             bg=DARK_BG, fg=TEXT_SEC, font=FONT_SMALL).pack(anchor="w", pady=(2, 0))
    tk.Frame(frame, bg=CARD_BORDER, height=1).pack(fill="x", padx=22, pady=(6, 0))

    # ── Center card ──────────────────────────────────────────
    center = tk.Frame(frame, bg=DARK_BG)
    center.pack(fill="both", expand=True)
    center.place(relx=0.5, rely=0.5, anchor="center")

    outer = tk.Frame(center, bg=CARD_BORDER, padx=1, pady=1)
    outer.pack()
    inner = tk.Frame(outer, bg=CARD_BG, padx=50, pady=40)
    inner.pack()

    # Icon
    icon_c = tk.Canvas(inner, width=80, height=80,
                       bg=CARD_BG, highlightthickness=0)
    icon_c.pack(pady=(0, 16))
    # Draw simplified hand icon
    icon_c.create_oval(10, 30, 60, 70, fill=ACCENT_BLUE, outline="")
    for fx, fy, fw, fh in [(14,10,12,26),(26,6,12,28),(38,8,11,26),(50,14,10,22)]:
        icon_c.create_oval(fx, fy, fx+fw, fy+fh, fill=ACCENT_BLUE, outline="")
    icon_c.create_oval(4, 32, 18, 56, fill=ACCENT_BLUE, outline="")

    tk.Label(inner, text="ISL Avatar",
             bg=CARD_BG, fg=TEXT_PRIMARY,
             font=("Georgia", 18, "bold")).pack()
    tk.Label(inner, text="Launch the avatar to convert text\ninto sign language animations",
             bg=CARD_BG, fg=TEXT_SEC,
             font=FONT_BODY, justify="center").pack(pady=(8, 24))

    tk.Frame(inner, bg=CARD_BORDER, height=1).pack(fill="x", pady=(0, 20))

    def open_avatar():
        script = os.path.join(PROJECT, "edusign_tabs_app.py")
        if os.path.exists(script):
            subprocess.Popen([sys.executable, script])
        else:
            import tkinter.messagebox as mb
            mb.showerror("Not Found",
                         "edusign_tabs_app.py not found in the project folder.")

    btn = tk.Button(inner,
                    text="\u25b6  Open Avatar",
                    bg=ACCENT_BLUE, fg="white",
                    activebackground=HOVER_BG,
                    activeforeground=ACCENT_CYAN,
                    font=("Segoe UI", 12, "bold"),
                    bd=0, padx=30, pady=12, cursor="hand2")
    btn.config(command=open_avatar)
    btn.pack()
    btn.bind("<Enter>", lambda e: btn.config(bg=HOVER_BG, fg=ACCENT_CYAN))
    btn.bind("<Leave>", lambda e: btn.config(bg=ACCENT_BLUE, fg="white"))

    tk.Label(inner,
             text="\u00a9 EduSign \u00b7 Final Year Project",
             bg=CARD_BG, fg=TEXT_MUTED,
             font=("Courier New", 8)).pack(pady=(24, 0))

    return frame