#!/usr/bin/env python3
"""
File Organizer with GUI + Auto-Watch
Author: ChatGPT (2025)
"""

import os
import shutil
import time
import threading
from pathlib import Path
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog, messagebox
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --------------------------------------------------
# Categories
# --------------------------------------------------
CATEGORIES = {
    "images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"},
    "videos": {".mp4", ".mkv", ".mov", ".avi", ".flv", ".wmv"},
    "documents": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".rtf"},
    "audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"},
    "archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
    "code": {".py", ".js", ".java", ".c", ".cpp", ".html", ".css", ".php"},
}

def category_for_extension(ext: str) -> str:
    ext = ext.lower()
    for cat, exts in CATEGORIES.items():
        if ext in exts:
            return cat
    return "others"

# --------------------------------------------------
# Core logic
# --------------------------------------------------
def safe_move(src: Path, dest_dir: Path):
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if dest.exists():
        stem, suffix = src.stem, src.suffix
        counter = 1
        while (dest_dir / f"{stem}_{counter}{suffix}").exists():
            counter += 1
        dest = dest_dir / f"{stem}_{counter}{suffix}"
    shutil.move(str(src), str(dest))
    print(f"Moved: {src.name} -> {dest}")

def organize_folder(folder: Path):
    moved = defaultdict(int)
    for path in folder.glob("*"):
        if path.is_file():
            cat = category_for_extension(path.suffix)
            safe_move(path, folder / cat)
            moved[cat] += 1
    return moved

# --------------------------------------------------
# Watchdog handler
# --------------------------------------------------
class WatchHandler(FileSystemEventHandler):
    def __init__(self, folder, log_callback):
        super().__init__()
        self.folder = Path(folder)
        self.log_callback = log_callback

    def on_created(self, event):
        if not event.is_directory:
            path = Path(event.src_path)
            cat = category_for_extension(path.suffix)
            dest_dir = self.folder / cat
            time.sleep(1)  # wait a bit for file to finish copying
            try:
                safe_move(path, dest_dir)
                self.log_callback(f"Auto-moved: {path.name} → {cat}/")
            except Exception as e:
                self.log_callback(f"Error moving {path.name}: {e}")

# --------------------------------------------------
# GUI
# --------------------------------------------------
class OrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📂 File Organizer")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        self.folder = tk.StringVar()
        self.observer = None

        tk.Label(root, text="Dossier à organiser :", font=("Segoe UI", 12)).pack(pady=10)
        frame = tk.Frame(root)
        frame.pack()
        tk.Entry(frame, textvariable=self.folder, width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Parcourir...", command=self.browse_folder).pack(side=tk.LEFT)

        self.log_box = tk.Text(root, height=12, width=70, state="disabled", bg="#f5f5f5")
        self.log_box.pack(pady=10)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="📁 Organiser maintenant", command=self.organize_now).pack(side=tk.LEFT, padx=10)
        self.watch_btn = tk.Button(btn_frame, text="🔁 Activer la surveillance", command=self.toggle_watch)
        self.watch_btn.pack(side=tk.LEFT, padx=10)

        self.log("Prêt à organiser tes fichiers 💪")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder.set(folder)

    def log(self, msg):
        self.log_box.config(state="normal")
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.config(state="disabled")
        self.log_box.see(tk.END)

    def organize_now(self):
        folder = Path(self.folder.get())
        if not folder or not folder.exists():
            messagebox.showerror("Erreur", "Sélectionne un dossier valide !")
            return
        moved = organize_folder(folder)
        summary = ", ".join(f"{cat}: {n}" for cat, n in moved.items())
        self.log(f"✅ Organisation terminée → {summary if summary else 'Aucun fichier déplacé'}")

    def toggle_watch(self):
        if self.observer and self.observer.is_alive():
            self.stop_watch()
        else:
            self.start_watch()

    def start_watch(self):
        folder = Path(self.folder.get())
        if not folder.exists():
            messagebox.showerror("Erreur", "Sélectionne un dossier valide avant d’activer la surveillance.")
            return
        self.observer = Observer()
        handler = WatchHandler(folder, self.log)
        self.observer.schedule(handler, str(folder), recursive=False)
        self.observer.start()
        self.watch_btn.config(text="🛑 Arrêter la surveillance")
        self.log("🔁 Surveillance activée (le dossier sera organisé automatiquement).")

    def stop_watch(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.observer = None
        self.watch_btn.config(text="🔁 Activer la surveillance")
        self.log("🛑 Surveillance arrêtée.")

# --------------------------------------------------
# Run
# --------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = OrganizerApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_watch(), root.destroy()))
    root.mainloop()
