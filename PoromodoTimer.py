import tkinter as tk
from tkinter import simpledialog, messagebox
import time
import threading
import csv
from datetime import datetime, date
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']  # 微軟正黑體
import numpy as np
import os
import shutil

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
        self.root.title("Pomodoro Timer")
        self.root.geometry("300x300")
        self.root.iconbitmap("pic/tomato_icon.ico")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 設定背景圖片
        self.bg_image_all = ImageTk.PhotoImage(Image.open("pic/tomato_all.png").resize((300, 300)))
        self.bg_image_half = ImageTk.PhotoImage(Image.open("pic/tomato_half.png").resize((300, 300)))
        self.bg_image_little = ImageTk.PhotoImage(Image.open("pic/tomato_little.png").resize((300, 300)))
        self.bg_image_relax = ImageTk.PhotoImage(Image.open("pic/relax.png").resize((300, 300)))
        
        # setting images of buttons
        self.img_start = ImageTk.PhotoImage(Image.open("pic/play-button.png").resize((60, 60)))
        self.img_pause = ImageTk.PhotoImage(Image.open("pic/pause.png").resize((60, 60)))
        self.img_settime = ImageTk.PhotoImage(Image.open("pic/setting_timer.png").resize((60, 60)))
        self.bg_label = tk.Label(self.root, image=self.bg_image_all)
        self.bg_label.place(relwidth=1, relheight=1)

        # 設定上方選單
        menubar = tk.Menu(self.root)
        
        # 檔案選單
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="匯入", command=self.insert_csv)
        file_menu.add_command(label="匯出", command=self.export_csv)
        menubar.add_cascade(label="檔案", menu=file_menu)

        # 功能選單
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
        self.study_time_today = self.get_today_study_seconds()  # 單位為秒

        # 顯示時間的Label
        self.time_label = tk.Label(root, text=self.format_time(self.study_seconds), font=("Helvetica", 30))
        self.time_label.pack(expand=True)

        # 累積時間Label
        self.study_label = tk.Label(root, text=f"今日已讀: {round(self.study_time_today / 3600, 2)} 小時", font=("Helvetica", 12))
        self.study_label.pack()

        # # 按鈕區域
        # button_frame = tk.Frame(root)
        # button_frame.pack(pady=20)

        # self.start_button = tk.Button(button_frame, text="開始", command=self.toggle_timer)
        # self.start_button.grid(row=0, column=0, padx=10)

        # self.setTime_button = tk.Button(button_frame, text="自訂時間", command=self.set_time)
        # self.setTime_button.grid(row=0, column=1, padx=10)

        # 按鈕區域
        button_frame = tk.Frame(root)
        button_frame.pack(pady=20)

        self.start_button = tk.Button(
            button_frame, image=self.img_start, command=self.toggle_timer,
            bd=0, highlightthickness=0, relief="flat", bg="white", activebackground="white"
        )
        self.start_button.grid(row=0, column=0, padx=10)

        self.setTime_button = tk.Button(
            button_frame, image=self.img_settime, command=self.set_time,
            bd=0, highlightthickness=0, relief="flat", bg="white", activebackground="white"
        )
        self.setTime_button.grid(row=0, column=1, padx=10)

        # 背景執行的 Timer
        self.timer_thread = None

    def on_closing(self):
        self.is_running = False  # 停止計時執行緒
        plt.close('all') 
        self.root.destroy()

    def show_timer(self):
        # 目前只有一個主畫面，這裡可擴充切換不同畫面
        messagebox.showinfo("提示", "已在計時畫面。")
    
    def format_time(self, seconds):
        return f"{seconds // 60:02}:{seconds % 60:02}"
    
    def set_time(self):
        # 若正在計時，直接返回，不允許設定
        if self.is_running:
            return
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
            self.start_button.config(image=self.img_start)
            self.setTime_button.config(state="normal")
        else:
            self.is_running = True
            self.start_button.config(image=self.img_pause)
            self.setTime_button.config(state="disabled")
            if not self.timer_thread or not self.timer_thread.is_alive():
                self.timer_thread = threading.Thread(target=self.run_timer)
                self.timer_thread.start()

    def run_timer(self):
        while self.current_seconds > 0 and self.is_running:
            time.sleep(0.1)
            self.current_seconds -= 1
            self.update_ui(self.current_seconds)
        if self.current_seconds == 0:
            self.is_running = False
            self.handle_end_period()

    def update_ui(self, current_seconds):
        # 更改背景圖片
        if self.is_break:
            self.bg_label.config(image=self.bg_image_relax)
        else:
            if current_seconds == 0:
                self.time_label.config(text=self.format_time(current_seconds))
                return
            elif (current_seconds / self.study_seconds) <= 0.6:
                if (current_seconds / self.study_seconds) <= 0.3:
                    self.bg_label.config(image=self.bg_image_little)
                else:
                    self.bg_label.config(image=self.bg_image_half)
        # 更改秒數
        self.time_label.config(text=self.format_time(current_seconds))

    def handle_end_period(self):
        if not self.is_break:
            self.study_time_today += self.study_seconds
            self.update_study_time_label()
            # 用 after 在主執行緒呼叫 GUI 對話框
            self.start_button.config(image=self.img_start)
            self.setTime_button.config(state="normal")
            self.root.after(0, self.prompt_and_save_study_record)
        else:
            self.is_break = False
            self.current_seconds = self.study_seconds  # 學習時倒數學習時間
            messagebox.showinfo("重新開始", "休息結束，準備下一輪吧！")
            self.bg_label.config(image=self.bg_image_all)
            self.start_button.config(image=self.img_start)
            self.setTime_button.config(state="normal")
        self.update_ui(self.current_seconds)
        

    def update_study_time_label(self):
        hours = round(self.study_time_today / 3600, 2)
        self.study_label.config(text=f"今日已讀: {hours} 小時")

    def get_today_study_seconds(self):
        # 讀取csv並加總今天的學習秒數
        today = date.today().isoformat()
        total_seconds = 0
        try:
            with open("study_log.csv", "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 4 and row[0] == today:
                        # row[3] 例：'25分鐘'
                        try:
                            mins = int(row[3].replace("分鐘", ""))
                            total_seconds += mins * 60
                        except:
                            pass
        except FileNotFoundError:
            pass
        return total_seconds

    def prompt_and_save_study_record(self):
        dialog = StudyRecordDialog(self.root, title="學習記錄")
        if hasattr(dialog, 'subject') and dialog.subject:
            self.save_to_csv(
                subject=dialog.subject,
                study_range=dialog.range,
                note=dialog.note,
                img_path=dialog.img_path
            )
        else:
            messagebox.showwarning("警告", "未輸入科目，將不保存紀錄。")
        self.is_break = True
        self.current_seconds = self.relax_seconds
        self.start_button.config(text="開始")
        self.setTime_button.config(state="normal")
        messagebox.showinfo(f"休息時間", f"恭喜你完成一輪，來休{self.relax_seconds // 60}分鐘吧！")
        self.update_ui(self.current_seconds)

    def save_to_csv(self, subject, study_range, note, img_path):
        filename = "study_log.csv"
        today = date.today().isoformat()
        now = datetime.now().strftime("%H:%M:%S")
        with open(filename, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([today, now, subject, f"{self.study_seconds // 60}分鐘", study_range, note, img_path])

    # 匯入CSV，合併到現有csv
    def insert_csv(self):
        filename = filedialog.askopenfilename(
            title="選擇要匯入的CSV檔",
            filetypes=[("CSV Files", "*.csv")]
        )
        if not filename:
            return
        try:
            # 讀取現有資料
            current_data = []
            try:
                with open("study_log.csv", "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    current_data = list(reader)
            except FileNotFoundError:
                pass  # 沒有舊檔案也沒關係

            # 讀取匯入資料
            with open(filename, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                import_data = list(reader)

            # 合併（避免重複可自行加判斷）
            merged_data = current_data + import_data
            merged_data.sort(key=lambda row: row[0] if len(row) > 0 else "")

            # 寫回主csv
            with open("study_log.csv", "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(merged_data)

            messagebox.showinfo("成功", "匯入完成！")
        except Exception as e:
            messagebox.showerror("錯誤", f"匯入失敗：{e}")

    # 匯出CSV，另存新檔
    def export_csv(self):
        filename = filedialog.asksaveasfilename(
            title="另存新檔",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")]
        )
        if not filename:
            return
        try:
            with open("study_log.csv", "r", encoding="utf-8") as src, \
                 open(filename, "w", encoding="utf-8", newline="") as dst:
                dst.write(src.read())
            messagebox.showinfo("成功", "匯出完成！")
        except Exception as e:
            messagebox.showerror("錯誤", f"匯出失敗：{e}")
            
    def show_records(self):
        try:
            with open("study_log.csv", "r", encoding="utf-8") as file:
                records = list(csv.reader(file))
            if not records:
                messagebox.showinfo("提示", "尚無學習紀錄。")
                return

            # 取得所有不重複的日期
            dates = sorted({row[0] for row in records if len(row) > 0})
            dates.insert(0, "全部日期")

            records_window = tk.Toplevel(self.root)
            records_window.title("學習紀錄")

            notebook = ttk.Notebook(records_window)
            notebook.pack(expand=True, fill="both")

            # --- 純文字分頁 ---
            text_frame = tk.Frame(notebook)
            notebook.add(text_frame, text="純文字紀錄")

            selected_date_text = tk.StringVar(text_frame)
            selected_date_text.set("全部日期")

            tk.Label(text_frame, text="選擇日期:").pack(pady=5)
            date_menu_text = tk.OptionMenu(text_frame, selected_date_text, *dates, command=lambda _: update_tree())
            date_menu_text.pack(pady=5)

            columns = ("日期", "時間", "科目", "時長")
            tree = ttk.Treeview(text_frame, columns=columns, show="headings")
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100, anchor="center")
            tree.pack(expand=True, fill="both")
            
            def show_detail(event):
                selected = tree.focus()
                if not selected:
                    return
                item = tree.item(selected)
                values = item['values']
                # 找到原始 row
                for row in records:
                    # 比對前四欄（日期、時間、科目、時長）
                    if row and row[0] == values[0] and row[1] == values[1] and row[2] == values[2] and row[3] == values[3]:
                        detail = (
                            f"日期：{row[0]}\n"
                            f"時間：{row[1]}\n"
                            f"科目：{row[2]}\n"
                            f"讀書時間：{row[3]}\n"
                            f"範圍：{row[4] if len(row)>4 else ''}\n"
                            f"註記：{row[5] if len(row)>5 else ''}\n"
                            f"圖片：{'有' if len(row)>6 and row[6]!='NULL' else '無'}"
                        )
                        detail_win = tk.Toplevel(tree)
                        detail_win.title("詳細資料")
                        tk.Label(detail_win, text=detail, justify="left", font=("Helvetica", 12)).pack(padx=10, pady=10)
                        # 顯示圖片（如果有）
                        if len(row) > 6 and row[6] != "NULL":
                            img_path = row[6]
                            if not os.path.isabs(img_path):
                                img_path = os.path.join(os.getcwd(), img_path)
                            if os.path.exists(img_path):
                                img = Image.open(img_path)
                                img = img.resize((200, 200))
                                img_tk = ImageTk.PhotoImage(img)
                                img_label = tk.Label(detail_win, image=img_tk)
                                img_label.image = img_tk  # 防止被回收
                                img_label.pack(pady=5)
                        break

            tree.bind("<Double-1>", show_detail)

            def update_tree(*args):
                for i in tree.get_children():
                    tree.delete(i)
                # 預設全部日期
                if selected_date_text.get() == "全部日期":
                    for row in records:
                        if row:
                            tree.insert("", tk.END, values=row)
                else:
                    for row in records:
                        if row and row[0] == selected_date_text.get():
                            tree.insert("", tk.END, values=row)

            update_tree()

            # --- 分析分頁 ---
            analysis_frame = tk.Frame(notebook)
            notebook.add(analysis_frame, text="圖片分析與評語")

            dashboard_label = tk.Label(analysis_frame, text="", font=("Helvetica", 14))
            dashboard_label.pack(pady=10)
            comment_label = tk.Label(analysis_frame, text="", fg="blue", font=("Helvetica", 12))
            comment_label.pack(pady=10)

            # 圖片分析自己的 OptionMenu
            selected_date_analysis = tk.StringVar(analysis_frame)
            selected_date_analysis.set("全部日期")
            tk.Label(analysis_frame, text="選擇日期:").pack(pady=5)
            date_menu_analysis = tk.OptionMenu(analysis_frame, selected_date_analysis, *dates, command=lambda _: update_dashboard())
            date_menu_analysis.pack(pady=5)

            # matplotlib
            fig, ax = plt.subplots(figsize=(6, 3))
            canvas = FigureCanvasTkAgg(fig, master=analysis_frame)
            canvas.get_tk_widget().pack()

            def update_dashboard(*args):
                if selected_date_analysis.get() == "全部日期":
                    # x軸為日期，y軸為每天總讀書小時
                    date_to_minutes = {}
                    for row in records:
                        if row:
                            date = row[0]
                            try:
                                mins = int(row[3].replace("分鐘", ""))
                                date_to_minutes[date] = date_to_minutes.get(date, 0) + mins
                            except:
                                pass
                    x_dates = sorted(date_to_minutes.keys())
                    y_hours = [date_to_minutes[d]/60 for d in x_dates]
                    ax.clear()
                    ax.bar(x_dates, y_hours, color="#4A90E2")
                    ax.set_xticks(np.arange(len(x_dates)))
                    ax.set_xticklabels(x_dates, rotation=45, fontsize=10)
                    ax.set_xlabel("日期")
                    ax.set_ylabel("讀書小時數")
                    ax.set_title("各日期讀書總時數")
                    fig.tight_layout(rect=[0, 0.15, 1, 1])
                    dashboard_label.config(text="全部日期讀書總時數")
                    comment_label.config(text="")
                    canvas.draw()
                else:
                    # 單一天，x軸為小時
                    hour_bins = [0]*24
                    total_minutes = 0
                    for row in records:
                        if row and row[0] == selected_date_analysis.get():
                            try:
                                mins = int(row[3].replace("分鐘", ""))
                                hour = int(row[1].split(":")[0])
                                hour_bins[hour] += mins
                                total_minutes += mins
                            except:
                                pass
                    dashboard_label.config(text=f"{selected_date_analysis.get()} 讀書總時數：{round(total_minutes/60,2)} 小時")
                    hour_bins_in_hours = [m/60 for m in hour_bins]
                    ax.clear()
                    x = np.arange(24)
                    ax.bar(x, hour_bins_in_hours, color="#4A90E2")
                    ax.set_xticks(x)
                    ax.set_xticklabels([str(h) for h in x], rotation=0, fontsize=10)
                    ax.set_xlabel("小時")
                    ax.set_ylabel("讀書小時數")
                    ax.set_ylim(0, 24)
                    ax.set_title("每小時讀書時間分布")
                    fig.tight_layout(rect=[0, 0.05, 1, 1])
                    # 評語
                    if total_minutes >= 6*60:
                        comment = "非常棒！你今天的學習效率很高，繼續保持！"
                    elif total_minutes >= 3*60:
                        comment = "不錯哦，今天有穩定學習，建議再多安排一點時間！"
                    elif total_minutes > 0:
                        comment = "今天學習時間較少，可以檢視時間規劃並加強專注！"
                    else:
                        comment = "今天還沒有學習紀錄，快開始學習吧！"
                    comment_label.config(text=comment)
                    canvas.draw()

            update_dashboard()

        except FileNotFoundError:
            messagebox.showinfo("提示", "尚無學習紀錄。")
        
class StudyRecordDialog(simpledialog.Dialog):
    subjects_history = set()

    def body(self, master):
        tk.Label(master, text="科目:").grid(row=0, column=0)
        tk.Label(master, text="範圍:").grid(row=1, column=0)
        tk.Label(master, text="註記:").grid(row=2, column=0)
        tk.Label(master, text="圖片:").grid(row=3, column=0)

        self.subject_var = tk.StringVar()
        self.subject_box = ttk.Combobox(master, textvariable=self.subject_var)
        self.subject_box['values'] = list(StudyRecordDialog.subjects_history)
        self.subject_box.grid(row=0, column=1)

        self.range_entry = tk.Entry(master)
        self.range_entry.grid(row=1, column=1)

        self.note_entry = tk.Entry(master)
        self.note_entry.grid(row=2, column=1)

        self.img_path_var = tk.StringVar()
        self.img_entry = tk.Entry(master, textvariable=self.img_path_var, state="readonly")
        self.img_entry.grid(row=3, column=1)
        self.img_btn = tk.Button(master, text="選擇圖片", command=self.choose_img)
        self.img_btn.grid(row=3, column=2)

        return self.subject_box

    def choose_img(self):
        path = filedialog.askopenfilename(title="選擇圖片", filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
        if path:
            folder = os.path.join(os.getcwd(), "study_pic")
            os.makedirs(folder, exist_ok=True)
            filename = os.path.basename(path)
            # 防止重名覆蓋
            base, ext = os.path.splitext(filename)
            i = 1
            new_filename = filename
            while os.path.exists(os.path.join(folder, new_filename)):
                new_filename = f"{base}_{i}{ext}"
                i += 1
            new_path = os.path.join(folder, new_filename)
            shutil.copy(path, new_path)
            # 儲存相對路徑
            rel_path = os.path.relpath(new_path, os.getcwd())
            self.img_path_var.set(rel_path)

    def apply(self):
        self.subject = self.subject_var.get()
        self.range = self.range_entry.get()
        self.note = self.note_entry.get()
        self.img_path = self.img_path_var.get() if self.img_path_var.get() else "NULL"
        if self.subject:
            StudyRecordDialog.subjects_history.add(self.subject)
        else:
            messagebox.showwarning("警告", "科目為必填欄位！")
            
            
            
# 啟動主視窗
if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.mainloop()
