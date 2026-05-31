#!/usr/bin/env python3
"""
전기실 제품 유통기한 스케줄러
Electrical Room Product Expiry Date Scheduler
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ui.main_window import MainWindow
import tkinter as tk


def main():
    root = tk.Tk()
    root.title("전기실 제품 유통기한 스케줄러")
    root.geometry("420x820")
    root.minsize(380, 700)
    root.configure(bg="#0D0D0D")
    
    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (420 // 2)
    y = (root.winfo_screenheight() // 2) - (820 // 2)
    root.geometry(f"420x820+{x}+{y}")

    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
