import tkinter as tk
from tkinter import simpledialog, messagebox
import time
import threading
import csv
from datetime import datetime, date
from tkinter import ttk

class TimeSettingDialog(simpledialog.Dialog):
    def body(self, master):
        tk.Label(master, text="學習時間 (分鐘):").grid(row=0)
        tk.Label(master, text="休息時間 (分鐘):").grid(row=1)

        self.study_entry = tk.Entry(master)
        self.relax_entry = tk.Entry(master)

        self.study_entry.grid(row=0, column=1)
        self.relax_entry.grid(row=1, column=1)
        return self.study_entry  # 初始 focus

    def apply(self):
        self.study_time = self.study_entry.get()
        self.relax_time = self.relax_entry.get()

class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("Poromodo Timer")
        self.root.geometry("300x300")

        # 新增上方選單
        menubar = tk.Menu(self.root)
        mode_menu = tk.Menu(menubar, tearoff=0)
        mode_menu.add_command(label="計時", command=self.show_timer)
        mode_menu.add_command(label="查看紀錄", command=self.show_records)
        menubar.add_cascade(label="功能", menu=mode_menu)
        self.root.config(menu=menubar)

        self.is_running = False
        self.is_break = False
        self.study_seconds = 25 * 60
        self.relax_seconds = 5 * 60
        self.current_seconds = self.study_seconds
        self.study_time_today = 0  # 單位為秒

        # 顯示時間的Label
        self.time_label = tk.Label(root, text=self.format_time(self.study_seconds), font=("Helvetica", 30))
        self.time_label.pack(expand=True)

        # 累積時間Label
        self.study_label = tk.Label(root, text="今日已讀: 0.0 小時", font=("Times", 12))
        self.study_label.pack()

        # 按鈕區域
        button_frame = tk.Frame(root)
        button_frame.pack(pady=20)

        self.start_button = tk.Button(button_frame, text="開始", command=self.toggle_timer)
        self.start_button.grid(row=0, column=0, padx=10)

        self.setTime_button = tk.Button(button_frame, text="自訂時間", command=self.set_time)
        self.setTime_button.grid(row=0, column=1, padx=10)

        # 背景執行的 Timer
        self.timer_thread = None

    def show_timer(self):
        # 目前只有一個主畫面，這裡可擴充切換不同畫面
        messagebox.showinfo("提示", "已在計時畫面。")

    def show_records(self):
        try:
            with open("study_log.csv", "r", encoding="utf-8") as file:
                records = list(csv.reader(file))
            record_window = tk.Toplevel(self.root)
            record_window.title("學習紀錄")
            columns = ("日期", "時間", "內容", "時長")
            tree = ttk.Treeview(record_window, columns=columns, show="headings")
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100, anchor="center")
            for row in records:
                tree.insert("", tk.END, values=row)
            tree.pack(expand=True, fill="both")
        except FileNotFoundError:
            messagebox.showinfo("提示", "尚無學習紀錄。")
    
    def format_time(self, seconds):
        return f"{seconds // 60:02}:{seconds % 60:02}"
    
    def set_time(self):
        dialog = TimeSettingDialog(self.root, title="自訂時間")
        try:
            study_time = int(dialog.study_time)
            relax_time = int(dialog.relax_time)
            if study_time > 0 and relax_time > 0:
                self.study_seconds = study_time * 60
                self.relax_seconds = relax_time * 60
                if not self.is_running:  # 只有在未計時時才重設剩餘秒數
                    self.current_seconds = self.study_seconds
                    self.update_ui(self.current_seconds)
            else:
                messagebox.showerror("錯誤", "請輸入有效的正整數！")
        except Exception:
            messagebox.showerror("錯誤", "請輸入有效的數字！")

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
        while self.current_seconds > 0 and self.is_running:
            time.sleep(1)
            self.current_seconds -= 1
            self.update_ui(self.current_seconds)
        if self.current_seconds == 0:
            self.is_running = False
            self.handle_end_period()

    def update_ui(self, current_seconds):
        self.time_label.config(text=self.format_time(current_seconds))

    def handle_end_period(self):
        if not self.is_break:
            self.study_time_today += self.study_seconds
            self.update_study_time_label()
            # 用 after 在主執行緒呼叫 GUI 對話框
            self.root.after(0, self.prompt_and_save_study_record)
            self.is_break = True
            self.current_seconds = self.relax_seconds  # 休息時倒數休息時間
            self.start_button.config(text="開始")
            messagebox.showinfo(f"休息時間", f"恭喜你完成一輪，來休{self.relax_seconds // 60}分鐘吧！")
        else:
            self.is_break = False
            self.current_seconds = self.study_seconds  # 學習時倒數學習時間
            messagebox.showinfo("重新開始", "休息結束，準備下一輪吧！")
            self.start_button.config(text="開始")
        self.update_ui(self.current_seconds)
        

    def update_study_time_label(self):
        hours = round(self.study_time_today / 3600, 2)
        self.study_label.config(text=f"今日已讀: {hours} 小時")

    def prompt_and_save_study_record(self):
        plan = simpledialog.askstring("學習記錄", "請輸入這次讀書的內容：")
        if plan:
            self.save_to_csv(plan)

    def save_to_csv(self, plan):
        filename = "study_log.csv"
        today = date.today().isoformat()
        now = datetime.now().strftime("%H:%M:%S")

        with open(filename, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([today, now, plan, f"{self.study_seconds // 60}分鐘"])

# 啟動主視窗
if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.mainloop()
