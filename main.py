"""
EduSign - Main entry point
Usage: python -B main.py
"""
import sys, os

sys.path = [p for p in sys.path if p not in ('', '.', os.getcwd())]
PROJECT = os.path.dirname(os.path.abspath(__file__))
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

import tkinter as tk
from auth_page import auth_page
from app_shell import start_app

root = tk.Tk()
root.title("EduSign \u2013 Indian Sign Language Platform")
root.geometry("1000x650")
root.configure(bg="#080d18")
auth_page(root, start_app)
root.mainloop()