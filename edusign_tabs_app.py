import sys, os
sys.path = [p for p in sys.path if p not in ('', '.', os.getcwd())]
PROJECT = os.path.dirname(os.path.abspath(__file__))
if PROJECT not in sys.path:
    sys.path.append(PROJECT)

import tkinter as tk
import subprocess
import cv2

PYTHON_311  = r"C:\Users\TEJES.M\AppData\Local\Programs\Python\Python311\python.exe"
REPO_DIR    = os.path.join(PROJECT, "Indian-Sign-Language-Detection")
ISL_SCRIPT  = os.path.join(REPO_DIR, "isl_detection.py")
OUTPUT_FILE = os.path.join(REPO_DIR, "output.txt")
VIDEO_DIR   = os.path.join(PROJECT, "text_to_sign", "videos")

DARK_BG      = "#080d18"
SIDEBAR_BG   = "#050911"
CARD_BG      = "#0f1829"
CARD_BORDER  = "#1a2845"
HOVER_BG     = "#162035"
INPUT_BG     = "#0c1422"
ACCENT_BLUE  = "#1e6fff"
ACCENT_CYAN  = "#00d4ff"
ACCENT_GREEN = "#00c96e"
ACCENT_RED   = "#e53935"
ACCENT_AMBER = "#ffb300"
TEXT_PRIMARY = "#dce8ff"
TEXT_SEC     = "#7a9bc4"
TEXT_MUTED   = "#3d5578"
FONT_TITLE   = ("Georgia", 20, "bold")
FONT_BODY    = ("Courier New", 11)
FONT_SMALL   = ("Courier New", 9)
FONT_DETECT  = ("Georgia", 60, "bold")

_last = ""; _buf = ""
output_var = None; word_var = None

def start_sign_to_text():
    subprocess.Popen([PYTHON_311, ISL_SCRIPT], cwd=REPO_DIR)

def _poll(root):
    global _last, _buf
    try:
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE,"r") as f:
                letter = f.read().strip()
            if letter:
                output_var.set(letter)
                if letter != _last:
                    _buf += letter; word_var.set(_buf); _last = letter
    except Exception:
        pass
    root.after(600, lambda: _poll(root))

def add_space():
    global _buf; _buf += " "; word_var.set(_buf)

def backspace():
    global _buf; _buf = _buf[:-1]; word_var.set(_buf)

def clear_text():
    global _buf, _last
    _buf = ""; _last = ""; output_var.set("—"); word_var.set("")

def play_video(letter):
    vp = os.path.join(VIDEO_DIR, f"{letter}.mp4")
    if not os.path.exists(vp): return
    cap = cv2.VideoCapture(vp)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        cv2.imshow("EduSign – Text to Sign", frame)
        if cv2.waitKey(30) & 0xFF == 27: break
    cap.release(); cv2.destroyAllWindows()

def convert_text_to_sign(tw):
    for ch in tw.get().upper():
        if ch.isalnum(): play_video(ch)

def _draw_hand(canvas, x, y, color, size=1.0):
    s = size
    canvas.create_oval(x+4*s,y+12*s,x+26*s,y+30*s,fill=color,outline="")
    for fx,fy,fw,fh in [(6,4,6,14),(12,2,6,16),(18,3,6,15),(24,6,5,13)]:
        canvas.create_oval(x+fx*s,y+fy*s,x+(fx+fw)*s,y+(fy+fh)*s,fill=color,outline="")
    canvas.create_oval(x-2*s,y+14*s,x+8*s,y+26*s,fill=color,outline="")

def _btn(parent, text, color, cmd, width=16):
    b = tk.Button(parent, text=text, bg=color, fg="white",
                  activebackground=color, activeforeground="white",
                  bd=0, padx=16, pady=9, width=width,
                  font=("Georgia",10,"bold"), cursor="hand2", command=cmd)
    return b

def _build_sign_tab(parent, root):
    outer = tk.Frame(parent, bg=DARK_BG)
    outer.pack(fill="both", expand=True, padx=30, pady=20)
    tk.Label(outer, text="Sign Language  →  Text",
             bg=DARK_BG, fg=TEXT_PRIMARY, font=FONT_TITLE).pack(anchor="w")
    tk.Label(outer, text="Show a hand sign to the camera · letters captured automatically",
             bg=DARK_BG, fg=TEXT_MUTED, font=FONT_SMALL).pack(anchor="w", pady=(2,16))
    row = tk.Frame(outer, bg=DARK_BG)
    row.pack(fill="both", expand=True)

    left = tk.Frame(row, bg=CARD_BG,
                    highlightbackground=CARD_BORDER,
                    highlightthickness=1, padx=24, pady=20)
    left.pack(side="left", fill="y", padx=(0,12))
    tk.Label(left, text="Detected Letter", bg=CARD_BG, fg=TEXT_SEC,
             font=("Georgia",10,"bold")).pack(anchor="w")
    det = tk.Frame(left, bg=HOVER_BG, width=160, height=160)
    det.pack(pady=12); det.pack_propagate(False)
    tk.Label(det, textvariable=output_var, bg=HOVER_BG,
             fg=ACCENT_CYAN, font=FONT_DETECT).place(relx=0.5,rely=0.5,anchor="center")
    _btn(left,"▶  Start Camera",ACCENT_BLUE,start_sign_to_text,18).pack(fill="x",pady=(0,10))
    tk.Frame(left, bg=CARD_BORDER, height=1).pack(fill="x", pady=8)
    tk.Label(left, text="Word Controls", bg=CARD_BG, fg=TEXT_SEC,
             font=("Georgia",10,"bold")).pack(anchor="w")
    for txt,color,cmd in [("⎵  Space",ACCENT_BLUE,add_space),
                           ("⌫  Backspace",ACCENT_AMBER,backspace),
                           ("✕  Clear",ACCENT_RED,clear_text)]:
        _btn(left,txt,color,cmd,18).pack(fill="x",pady=3)

    right = tk.Frame(row, bg=DARK_BG)
    right.pack(side="left", fill="both", expand=True)
    tk.Label(right, text="Formed Sentence", bg=DARK_BG, fg=TEXT_SEC,
             font=("Georgia",10,"bold")).pack(anchor="w")
    sf = tk.Frame(right, bg=CARD_BG,
                  highlightbackground=CARD_BORDER, highlightthickness=1)
    sf.pack(fill="both", expand=True, pady=8)
    tk.Label(sf, textvariable=word_var, bg=CARD_BG, fg=TEXT_PRIMARY,
             font=("Georgia",18), wraplength=520, justify="left",
             anchor="nw", padx=16, pady=14).pack(fill="both", expand=True)
    tip = tk.Frame(right, bg=HOVER_BG, padx=14, pady=10)
    tip.pack(fill="x", pady=(4,0))
    tk.Label(tip, text="💡  Start camera · sign each letter · words appear above",
             bg=HOVER_BG, fg=TEXT_SEC, font=FONT_SMALL).pack(anchor="w")

def _build_text_tab(parent):
    outer = tk.Frame(parent, bg=DARK_BG)
    outer.pack(fill="both", expand=True, padx=30, pady=20)
    tk.Label(outer, text="Text  →  Sign Language",
             bg=DARK_BG, fg=TEXT_PRIMARY, font=FONT_TITLE).pack(anchor="w")
    tk.Label(outer, text="Type a word or sentence · videos play letter by letter",
             bg=DARK_BG, fg=TEXT_MUTED, font=FONT_SMALL).pack(anchor="w", pady=(2,20))

    ic = tk.Frame(outer, bg=CARD_BG,
                  highlightbackground=CARD_BORDER, highlightthickness=1,
                  padx=24, pady=20)
    ic.pack(fill="x")
    tk.Label(ic, text="Enter text to convert:", bg=CARD_BG, fg=TEXT_SEC,
             font=("Georgia",10,"bold")).pack(anchor="w")
    ir = tk.Frame(ic, bg=CARD_BG)
    ir.pack(fill="x", pady=10)
    ti = tk.Entry(ir, bd=0, bg=INPUT_BG, fg=TEXT_PRIMARY,
                  insertbackground=ACCENT_CYAN, font=("Georgia",14),
                  highlightbackground=CARD_BORDER, highlightthickness=1)
    ti.pack(side="left", fill="x", expand=True, ipady=10, padx=(0,12))
    _btn(ir,"▶  Play Signs",ACCENT_GREEN,lambda:convert_text_to_sign(ti),14).pack(side="left")
    ti.bind("<Return>", lambda e: convert_text_to_sign(ti))
    tk.Label(ic, text="Signs play in a separate window  ·  Press ESC to stop",
             bg=CARD_BG, fg=TEXT_MUTED, font=FONT_SMALL).pack(anchor="w")

    hw = tk.Frame(outer, bg=HOVER_BG, padx=20, pady=16)
    hw.pack(fill="x", pady=16)
    tk.Label(hw, text="How it works", bg=HOVER_BG,
             fg=TEXT_PRIMARY, font=("Georgia",11,"bold")).pack(anchor="w")
    for num, step in [("1","Type any word or sentence above"),
                      ("2","Click  ▶ Play Signs  or press Enter"),
                      ("3","Each letter's sign video plays in order"),
                      ("4","Press  ESC  to stop the video early")]:
        r = tk.Frame(hw, bg=HOVER_BG); r.pack(fill="x", pady=3)
        tk.Label(r, text=num, bg=ACCENT_BLUE, fg="white",
                 font=("Georgia",9,"bold"), width=2, pady=2).pack(side="left", padx=(0,10))
        tk.Label(r, text=step, bg=HOVER_BG, fg=TEXT_SEC,
                 font=FONT_BODY).pack(side="left")

    cc = tk.Frame(outer, bg=CARD_BG,
                  highlightbackground=CARD_BORDER, highlightthickness=1,
                  padx=20, pady=14)
    cc.pack(fill="x")
    tk.Label(cc, text="Supported Characters", bg=CARD_BG, fg=TEXT_SEC,
             font=("Georgia",10,"bold")).pack(anchor="w", pady=(0,8))
    cr = tk.Frame(cc, bg=CARD_BG); cr.pack(fill="x")
    for label, color in [("A – Z",ACCENT_CYAN),("0 – 9",ACCENT_BLUE)]:
        pill = tk.Frame(cr, bg=HOVER_BG, padx=12, pady=5)
        pill.pack(side="left", padx=4)
        tk.Label(pill, text=label, bg=HOVER_BG, fg=color,
                 font=("Georgia",10,"bold")).pack()

def build_app():
    global output_var, word_var
    root = tk.Tk()
    root.title("EduSign – Indian Sign Language Application")
    root.geometry("960x680")
    root.configure(bg=DARK_BG)
    output_var = tk.StringVar(value="—")
    word_var   = tk.StringVar(value="")

    hdr = tk.Frame(root, bg=SIDEBAR_BG, height=50)
    hdr.pack(fill="x"); hdr.pack_propagate(False)
    lc = tk.Canvas(hdr, width=30, height=30, bg=SIDEBAR_BG, highlightthickness=0)
    lc.pack(side="left", padx=(14,0), pady=10)
    _draw_hand(lc, 0, 0, ACCENT_BLUE, size=0.85)
    tk.Label(hdr, text="EduSign", bg=SIDEBAR_BG, fg=TEXT_PRIMARY,
             font=("Georgia",16,"bold")).pack(side="left", padx=8)
    tk.Label(hdr, text="Indian Sign Language Recognition System",
             bg=SIDEBAR_BG, fg=TEXT_MUTED, font=FONT_SMALL).pack(side="left")

    tab_bar = tk.Frame(root, bg=CARD_BG, height=44)
    tab_bar.pack(fill="x"); tab_bar.pack_propagate(False)
    host = tk.Frame(root, bg=DARK_BG)
    host.pack(fill="both", expand=True)

    tab_s = tk.Frame(host, bg=DARK_BG)
    tab_t = tk.Frame(host, bg=DARK_BG)
    active_tab = {"v": None}
    tab_btns   = {}

    def show_tab(name):
        tab_s.pack_forget(); tab_t.pack_forget()
        (tab_s if name=="sign" else tab_t).pack(fill="both", expand=True)
        active_tab["v"] = name
        for k,(b,ul) in tab_btns.items():
            if k==name: b.config(fg=ACCENT_CYAN); ul.config(bg=ACCENT_CYAN)
            else:       b.config(fg=TEXT_MUTED);  ul.config(bg=CARD_BG)

    for key, lbl in [("sign","🖐  Sign → Text"),("text","📝  Text → Sign")]:
        col = tk.Frame(tab_bar, bg=CARD_BG); col.pack(side="left")
        b = tk.Button(col, text=lbl, bg=CARD_BG, fg=TEXT_MUTED,
                      activebackground=HOVER_BG, activeforeground=ACCENT_CYAN,
                      bd=0, padx=24, pady=10, font=("Georgia",11,"bold"),
                      cursor="hand2", command=lambda k=key: show_tab(k))
        b.pack()
        ul = tk.Frame(col, bg=CARD_BG, height=2); ul.pack(fill="x")
        tab_btns[key] = (b, ul)

    _build_sign_tab(tab_s, root)
    _build_text_tab(tab_t)
    tk.Label(root, text="Final Year Project  ·  EduSign  ·  Indian Sign Language",
             bg=DARK_BG, fg=TEXT_MUTED, font=FONT_SMALL).pack(side="bottom", pady=6)

    show_tab("sign")
    _poll(root)
    root.mainloop()

if __name__ == "__main__":
    build_app()