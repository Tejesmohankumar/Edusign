import sys, os
sys.path = [p for p in sys.path if p not in ('', '.', os.getcwd())]
PROJECT = os.path.dirname(os.path.abspath(__file__))
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

import tkinter as tk
from tkinter import messagebox

DARK_BG      = "#080d18"
SIDEBAR_BG   = "#050911"
CARD_BG      = "#0f1829"
CARD_BORDER  = "#1a2845"
HOVER_BG     = "#162035"
ACCENT_BLUE  = "#1e6fff"
ACCENT_CYAN  = "#00d4ff"
TEXT_PRIMARY = "#dce8ff"
TEXT_SEC     = "#7a9bc4"
TEXT_MUTED   = "#3d5578"
FONT_LOGO    = ("Georgia", 18, "bold")
FONT_NAV     = ("Georgia", 11)
FONT_SMALL   = ("Courier New", 9)


def _draw_hand(canvas, x, y, color, size=1.0):
    s = size
    canvas.create_oval(x+4*s, y+12*s, x+26*s, y+30*s, fill=color, outline="")
    for fx, fy, fw, fh in [(6,4,6,14),(12,2,6,16),(18,3,6,15),(24,6,5,13)]:
        canvas.create_oval(x+fx*s, y+fy*s, x+(fx+fw)*s, y+(fy+fh)*s,
                           fill=color, outline="")
    canvas.create_oval(x-2*s, y+14*s, x+8*s, y+26*s, fill=color, outline="")


def _nav_btn(sidebar, icon, label, command):
    row = tk.Frame(sidebar, bg=SIDEBAR_BG, cursor="hand2")
    row.pack(fill="x", padx=8, pady=2)
    lbl = tk.Label(row, text=f"  {icon}  {label}",
                   bg=SIDEBAR_BG, fg=TEXT_SEC,
                   font=FONT_NAV, pady=10, anchor="w")
    lbl.pack(fill="x")
    row._bg = SIDEBAR_BG

    def on_enter(e): row.config(bg=HOVER_BG); lbl.config(bg=HOVER_BG)
    def on_leave(e): row.config(bg=row._bg);  lbl.config(bg=row._bg)

    for w in (row, lbl):
        w.bind("<Enter>",    on_enter)
        w.bind("<Leave>",    on_leave)
        w.bind("<Button-1>", lambda e, cmd=command: cmd())
    return row, lbl


def run_app(user_id, name, role):
    # Import pages from the pages sub-package
    from pages.dashboard         import page as dashboard_page
    from pages.lessons           import page as lessons_page
    from pages.quiz              import page as quiz_page
    from pages.performance       import page as performance_page
    from pages.teacher_dashboard import page as teacher_page

    try:
        from pages.avatar import page as avatar_page
        has_avatar = True
    except ImportError:
        has_avatar = False

    root = tk.Tk()
    root.title("EduSign \u2013 Indian Sign Language Learning")
    root.geometry("1280x760")
    root.configure(bg=DARK_BG)
    root.minsize(900, 600)

    # Title bar
    tb = tk.Frame(root, bg=SIDEBAR_BG, height=46)
    tb.pack(fill="x")
    tb.pack_propagate(False)
    lc = tk.Canvas(tb, width=32, height=32, bg=SIDEBAR_BG, highlightthickness=0)
    lc.pack(side="left", padx=(14, 0), pady=7)
    _draw_hand(lc, 0, 0, ACCENT_BLUE, size=0.9)
    tk.Label(tb, text="EduSign", bg=SIDEBAR_BG,
             fg=TEXT_PRIMARY, font=FONT_LOGO).pack(side="left", padx=8)
    tk.Label(tb, text="Indian Sign Language Platform",
             bg=SIDEBAR_BG, fg=TEXT_MUTED,
             font=FONT_SMALL).pack(side="left", padx=4)
    chip = tk.Frame(tb, bg=CARD_BG, padx=12, pady=4)
    chip.pack(side="right", padx=14, pady=8)
    avc = tk.Canvas(chip, width=24, height=24, bg=CARD_BG, highlightthickness=0)
    avc.pack(side="left")
    avc.create_oval(2, 2, 22, 22, fill=ACCENT_BLUE, outline="")
    avc.create_text(12, 12, text=(name[0].upper() if name else "?"),
                    fill="white", font=("Georgia", 10, "bold"))
    tk.Label(chip, text=f"  {name}  \u00b7  {role.capitalize()}",
             bg=CARD_BG, fg=TEXT_SEC, font=FONT_SMALL).pack(side="left")

    body = tk.Frame(root, bg=DARK_BG)
    body.pack(fill="both", expand=True)
    sidebar = tk.Frame(body, bg=SIDEBAR_BG, width=210)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)
    content_area = tk.Frame(body, bg=DARK_BG)
    content_area.pack(side="left", fill="both", expand=True)

    pages    = {}
    active   = {"name": None}
    nav_refs = {}

    def show_page(pname):
        if pname not in pages:
            if pname == "dashboard":
                pages[pname] = dashboard_page(content_area, user_id)
            elif pname == "lessons":
                pages[pname] = lessons_page(content_area, user_id)
            elif pname == "quiz":
                pages[pname] = quiz_page(content_area, user_id)
            elif pname == "performance":
                pages[pname] = performance_page(content_area, user_id)
            elif pname == "avatar" and has_avatar:
                pages[pname] = avatar_page(content_area, user_id)
            elif pname == "teacher":
                pages[pname] = teacher_page(content_area, user_id)
        for pg in pages.values():
            pg.pack_forget()
        if pname in pages:
            pages[pname].pack(fill="both", expand=True)
        active["name"] = pname
        for k, (r, l) in nav_refs.items():
            if k == pname:
                r.config(bg=ACCENT_BLUE); l.config(bg=ACCENT_BLUE, fg="white")
                r._bg = ACCENT_BLUE
            else:
                r.config(bg=SIDEBAR_BG); l.config(bg=SIDEBAR_BG, fg=TEXT_SEC)
                r._bg = SIDEBAR_BG

    def _sec(txt):
        tk.Label(sidebar, text=txt, bg=SIDEBAR_BG, fg=TEXT_MUTED,
                 font=("Courier New", 8)).pack(anchor="w", padx=18, pady=(12, 2))

    tk.Frame(sidebar, bg=SIDEBAR_BG, height=8).pack()

    if role == "student":
        _sec("STUDENT")
        items = [("\U0001f3e0", "Dashboard", "dashboard"),
                 ("\U0001f4da", "Lessons",   "lessons"),
                 ("\U0001f3af", "Quiz",       "quiz"),
                 ("\U0001f4ca", "Performance","performance")]
        if has_avatar:
            items.append(("\U0001f916", "Avatar", "avatar"))
        for icon, label, key in items:
            r, l = _nav_btn(sidebar, icon, label, lambda k=key: show_page(k))
            nav_refs[key] = (r, l)
        show_page("dashboard")
    else:
        _sec("TEACHER")
        r, l = _nav_btn(sidebar, "\U0001f4ca", "Dashboard", lambda: show_page("teacher"))
        nav_refs["teacher"] = (r, l)
        show_page("teacher")

    tk.Frame(sidebar, bg=SIDEBAR_BG).pack(fill="both", expand=True)
    tk.Frame(sidebar, bg=CARD_BORDER, height=1).pack(fill="x", padx=10, pady=6)

    def logout():
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            root.destroy()
            # Re-import here so the new Tk window works cleanly
            import auth_page as ap
            import importlib
            importlib.reload(ap)
            nr = tk.Tk()
            nr.title("EduSign")
            nr.geometry("1000x650")
            nr.configure(bg=DARK_BG)
            ap.auth_page(nr, start_app)
            nr.mainloop()

    lo = tk.Frame(sidebar, bg=SIDEBAR_BG, cursor="hand2")
    lo.pack(fill="x", padx=8, pady=(0, 14))
    ll = tk.Label(lo, text="  \U0001f6aa  Logout",
                  bg=SIDEBAR_BG, fg="#e57373",
                  font=FONT_NAV, pady=10, anchor="w")
    ll.pack(fill="x")
    lo._bg = SIDEBAR_BG
    for w in (lo, ll):
        w.bind("<Enter>",    lambda e: [lo.config(bg="#1a0a0a"), ll.config(bg="#1a0a0a")])
        w.bind("<Leave>",    lambda e: [lo.config(bg=SIDEBAR_BG), ll.config(bg=SIDEBAR_BG)])
        w.bind("<Button-1>", lambda e: logout())

    root.mainloop()


def start_app(user_id, name, role):
    run_app(user_id, name, role)


if __name__ == "__main__":
    start_app(1, "Demo", "student")