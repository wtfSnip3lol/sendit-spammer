# imports and installs
import os
os.system("pip install selenium")
os.system("pip install urllib3")

import tkinter as tk
from tkinter import ttk, scrolledtext
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import threading

class SenditApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sendit Automator Pro")
        self.root.geometry("600x650")
        self.root.minsize(550, 600)
        
        self.is_running = False
        self.threads = []
        self.stop_event = threading.Event()

        # Styling/Theme configuration
        style = ttk.Style()
        style.theme_use('clam')

        # --- UI Layout ---
        title_label = ttk.Label(root, text="Sendit Multi-Instance Automator", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # Input Frame
        input_frame = ttk.LabelFrame(root, text=" Configuration ", padding=15)
        input_frame.pack(fill="x", padx=15, pady=5)

        # URL
        ttk.Label(input_frame, text="Sendit URL:").grid(row=0, column=0, sticky="w", pady=5)
        self.url_entry = ttk.Entry(input_frame, width=45)
        self.url_entry.grid(row=0, column=1, sticky="ew", pady=5)

        # Name
        ttk.Label(input_frame, text="Name to use:").grid(row=1, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(input_frame, width=45)
        self.name_entry.grid(row=1, column=1, sticky="ew", pady=5)

        # Messages
        ttk.Label(input_frame, text="Messages (comma-separated):").grid(row=2, column=0, sticky="w", pady=5)
        self.msg_entry = ttk.Entry(input_frame, width=45)
        self.msg_entry.grid(row=2, column=1, sticky="ew", pady=5)
        self.msg_entry.insert(0, "Hey!, What's up?, Cool page, Hi there")

        # Instances Count
        ttk.Label(input_frame, text="Parallel Instances:").grid(row=3, column=0, sticky="w", pady=5)
        self.instances_spin = ttk.Spinbox(input_frame, from_=1, to=10, width=5)
        self.instances_spin.grid(row=3, column=1, sticky="w", pady=5)
        self.instances_spin.set(2)

        input_frame.columnconfigure(1, weight=1)

        # Control Buttons Frame
        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill="x", padx=15, pady=10)

        self.start_btn = ttk.Button(btn_frame, text="Start Automation", command=self.start_automation)
        self.start_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.stop_btn = ttk.Button(btn_frame, text="Stop Automation", command=self.stop_automation, state="disabled")
        self.stop_btn.pack(side="right", expand=True, fill="x", padx=(5, 0))

        # Log Console Frame
        log_frame = ttk.LabelFrame(root, text=" Live Activity Log ", padding=10)
        log_frame.pack(fill="both", expand=True, padx=15, pady=5)

        self.log_box = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=12, state="disabled", font=("Consolas", 9))
        self.log_box.pack(fill="both", expand=True)

        # Footer status
        self.status_var = tk.StringVar(value="Status: Idle")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief="sunken", anchor="w", padding=5)
        status_bar.pack(fill="x", side="bottom")

    def log(self, message):
        """Thread-safe method to write text to the log box."""
        def append_text():
            self.log_box.config(state="normal")
            self.log_box.insert(tk.END, message + "\n")
            self.log_box.see(tk.END)
            self.log_box.config(state="disabled")
        self.root.after(0, append_text)

    def automation_worker(self, instance_id, target_url, name, msg_list):
        """Background thread running individual browser iterations."""
        index = 0
        while not self.stop_event.is_set():
            index += 1
            driver = None
            try:
                # Open fresh Chrome instance
                driver = webdriver.Chrome()
                driver.get(target_url)
                
                if self.stop_event.is_set():
                    driver.quit()
                    break

                wait = WebDriverWait(driver, 10)
                current_message = random.choice(msg_list)
                
                # 1. Fill message box
                msg_box = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[placeholder='tap to reply...']"))
                )
                msg_box.send_keys(current_message)
                
                # 2. Fill name box
                name_box = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[placeholder='Enter your name']"))
                )
                name_box.send_keys(name)
                
                # 3. Click send button via JS
                send_button = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.send-button"))
                )
                driver.execute_script("arguments[0].click();", send_button)
                
                # Increased to 2.0s delay to ensure the server registers the send request
                time.sleep(2.0)
                driver.quit()
                
                self.log(f"[Instance {instance_id}] Sent #{index} -> '{current_message}'")
                
            except Exception as e:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
                if not self.stop_event.is_set():
                    self.log(f"[Instance {instance_id}] Glitch encountered, retrying...")
                time.sleep(1)

    def start_automation(self):
        url = self.url_entry.get().strip()
        name = self.name_entry.get().strip()
        raw_msgs = self.msg_entry.get().strip()
        
        if not url or not name or not raw_msgs:
            self.log("[!] Error: Please fill in URL, Name, and Messages fields.")
            return

        try:
            num_instances = int(self.instances_spin.get())
        except ValueError:
            num_instances = 2

        messages = [m.strip() for m in raw_msgs.split(',')]

        # Update UI state
        self.is_running = True
        self.stop_event.clear()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set(f"Status: Running ({num_instances} active instances)")
        self.log(f"--- Starting Automation with {num_instances} instances ---")

        # Launch Threads
        self.threads = []
        for i in range(num_instances):
            t = threading.Thread(target=self.automation_worker, args=(i + 1, url, name, messages))
            t.daemon = True
            self.threads.append(t)
            t.start()
            time.sleep(0.3)

    def stop_automation(self):
        self.log("[-] Stopping automation... Please wait for active windows to close.")
        self.stop_event.set()
        self.is_running = False
        
        # Reset UI state
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_var.set("Status: Stopped")
        self.log("--- Automation Stopped ---")

if __name__ == "__main__":
    root = tk.Tk()
    app = SenditApp(root)
    root.mainloop()