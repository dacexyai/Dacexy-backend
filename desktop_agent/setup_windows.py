

"""
Dacexy Desktop Agent — Windows Setup
Run this script to install and start the Dacexy Desktop Agent.
Double-click to run, or: python setup_windows.py
"""

import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import urllib.request

SERVER_URL = "https://dacexy-backend-v7ku.onrender.com"

def install_dependencies(progress_label, progress_bar, root):
    packages = [
        "requests", "pyautogui", "pillow", "websockets",
        "SpeechRecognition", "pyttsx3", "keyboard", "mouse", "psutil"
    ]
    progress_label.config(text="Installing dependencies...")
    for i, pkg in enumerate(packages):
        progress_label.config(text=f"Installing {pkg}...")
        progress_bar["value"] = (i / len(packages)) * 70
        root.update()
        subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg, "--quiet"],
            capture_output=True
        )
    progress_bar["value"] = 80
    root.update()

def download_agent(progress_label, progress_bar, root):
    progress_label.config(text="Downloading Dacexy Agent...")
    root.update()
    url = "https://raw.githubusercontent.com/dacexyai/Dacexy-backend/main/desktop_agent/dacexy_agent.py"
    agent_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dacexy_agent.py")
    urllib.request.urlretrieve(url, agent_path)
    progress_bar["value"] = 90
    root.update()
    return agent_path

def save_config(token):
    config = {"token": token, "server": SERVER_URL}
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    with open(config_path, "w") as f:
        json.dump(config, f)
    return config_path

def start_agent():
    agent_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dacexy_agent.py")
    subprocess.Popen([sys.executable, agent_path], creationflags=subprocess.CREATE_NEW_CONSOLE)

class InstallerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dacexy Desktop Agent — Installer")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        self.root.configure(bg="#F9F7F2")

        # Center window
        self.root.eval('tk::PlaceWindow . center')

        self.build_ui()

    def build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#4F46E5", height=80)
        header.pack(fill="x")
        tk.Label(header, text="⚡ Dacexy Desktop Agent", font=("Arial", 18, "bold"),
                 bg="#4F46E5", fg="white").pack(pady=20)

        # Content
        content = tk.Frame(self.root, bg="#F9F7F2", padx=30, pady=20)
        content.pack(fill="both", expand=True)

        tk.Label(content, text="Enter your Agent Token", font=("Arial", 12, "bold"),
                 bg="#F9F7F2", fg="#0F0F0F").pack(anchor="w")
        tk.Label(content, text="Get this from dacexy.vercel.app → Settings → Desktop Agent",
                 font=("Arial", 9), bg="#F9F7F2", fg="#9E9E9E").pack(anchor="w", pady=(0, 10))

        self.token_entry = tk.Entry(content, font=("Arial", 11), width=45,
                                    relief="flat", bg="white",
                                    highlightthickness=1, highlightbackground="#E5E7EB")
        self.token_entry.pack(fill="x", ipady=8)

        # Progress
        self.progress_label = tk.Label(content, text="", font=("Arial", 9),
                                        bg="#F9F7F2", fg="#6B7280")
        self.progress_label.pack(anchor="w", pady=(15, 5))

        self.progress_bar = ttk.Progressbar(content, length=440, mode="determinate")
        self.progress_bar.pack(fill="x")

        # Install button
        self.install_btn = tk.Button(content, text="Install & Start Dacexy Agent",
                                      font=("Arial", 12, "bold"), bg="#4F46E5", fg="white",
                                      relief="flat", cursor="hand2", padx=20, pady=10,
                                      command=self.start_install)
        self.install_btn.pack(pady=20, fill="x")

        # Footer
        tk.Label(self.root, text="© 2026 Dacexy — Enterprise AI Platform",
                 font=("Arial", 8), bg="#F9F7F2", fg="#D1D5DB").pack(pady=5)

    def start_install(self):
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showerror("Error", "Please enter your Agent Token first.\n\nGet it from: dacexy.vercel.app → Settings → Desktop Agent")
            return

        self.install_btn.config(state="disabled", text="Installing...")
        threading.Thread(target=self.run_install, args=(token,), daemon=True).start()

    def run_install(self, token):
        try:
            self.progress_bar["value"] = 10
            self.root.update()

            install_dependencies(self.progress_label, self.progress_bar, self.root)
            download_agent(self.progress_label, self.progress_bar, self.root)
            save_config(token)

            self.progress_bar["value"] = 100
            self.progress_label.config(text="Installation complete!")
            self.root.update()

            messagebox.showinfo(
                "Success! 🎉",
                "Dacexy Desktop Agent installed successfully!\n\n"
                "The agent is now starting.\n\n"
                "Say 'Hey Dacexy' to give voice commands.\n"
                "Or commands will come from the Dacexy chat."
            )
            start_agent()
            self.root.destroy()

        except Exception as e:
            messagebox.showerror("Installation Failed", f"Error: {str(e)}\n\nPlease try again or contact support.")
            self.install_btn.config(state="normal", text="Install & Start Dacexy Agent")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = InstallerApp()
    app.run()
