import tkinter as tk
from tkinter import simpledialog, messagebox
import time
import threading
import csv
from datetime import datetime, date

class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("番茄鐘")
        self.root.geometry("300x250")

        self.is_running = False
        self.is_break = False
        self.total_seconds = 25 * 60
        self.study_time_today = 0  # 單位為秒

        # 顯示時間的Label
        self.time_label = tk.Label(root, text=self.format_time(self.total_seconds), font=("Helvetica", 30))
        self.time_label.pack(expand=True)

        # 累積時間Label
        self.study_label = tk.Label(root, text="今日已讀: 0.0 小時", font=("Helvetica", 12))
        self.study_label.pack()

        # 按鈕區域
        button_frame = tk.Frame(root)
        button_frame.pack()

        self.start_button = tk.Button(button_frame, text="開始", command=self.toggle_timer)
        self.start_button.grid(row=0, column=0, padx=10)

        self.exit_button = tk.Button(button_frame, text="離開", command=self.root.quit)
        self.exit_button.grid(row=0, column=1, padx=10)

        # 背景執行的 Timer
        self.timer_thread = None

    def format_time(self, seconds):
        return f"{seconds // 60:02}:{seconds % 60:02}"

    def toggle_timer(self):
        if self.is_running:
            self.is_running = False
            self.start_button.config(text="開始")
        else:
            self.is_running = True
            self.start_button.config(text="暫停")
            if not self.timer_thread or not self.timer_thread.is_alive():
                self.timer_thread = threading.Thread(target=self.run_timer)
                self.timer_thread.start()

    def run_timer(self):
        while self.total_seconds > 0 and self.is_running:
            time.sleep(1)
            self.total_seconds -= 1
            self.update_ui()
        if self.total_seconds == 0:
            self.is_running = False
            self.handle_end_period()

    def update_ui(self):
        self.time_label.config(text=self.format_time(self.total_seconds))

    def handle_end_period(self):
        if not self.is_break:
            # 累加學習時間
            self.study_time_today += 25 * 60
            self.update_study_time_label()
            self.prompt_and_save_study_record()

            # 進入休息
            self.total_seconds = 5 * 60
            self.is_break = True
            self.start_button.config(text="開始")
            messagebox.showinfo("休息時間", "恭喜你完成一輪，來休息 5 分鐘吧！")
        else:
            # 結束休息，重新開始番茄鐘
            self.total_seconds = 25 * 60
            self.is_break = False
            messagebox.showinfo("重新開始", "休息結束，準備下一輪吧！")

        self.update_ui()

    def update_study_time_label(self):
        hours = round(self.study_time_today / 3600, 2)
        self.study_label.config(text=f"今日已讀: {hours} 小時")

    def prompt_and_save_study_record(self):
        plan = simpledialog.askstring("學習記錄", "請輸入這次讀書的內容或目標：")
        if plan:
            self.save_to_csv(plan)

    def save_to_csv(self, plan):
        filename = "study_log.csv"
        today = date.today().isoformat()
        now = datetime.now().strftime("%H:%M:%S")

        with open(filename, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([today, now, plan, "25分鐘"])

# 啟動主視窗
if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.mainloop()
