# 🕒 Pomodoro Timer with Study Logger

這是一個基於 Python 的番茄鐘學習計時器，使用 `tkinter` 製作圖形化介面，結合學習紀錄、CSV 儲存與資料視覺化功能，幫助你更有效地安排與追蹤學習進度。

## 🧠 功能特色

- ⏱️ 番茄鐘計時：25 分鐘學習 + 5 分鐘休息（可自訂時間）
- 🗂️ 學習紀錄輸入：每輪結束可記錄「科目 / 範圍 / 備註 / 圖片」
- 📊 資料視覺化：顯示每日學習時數柱狀圖，並給予回饋建議
- 📁 CSV 檔案儲存：學習資料儲存在 `study_log.csv`
- 🔁 匯入 / 匯出 CSV：支援學習紀錄整合與備份
- 🖼️ 圖像上傳：可上傳學習筆記或圖片，輔助回顧

## 🖥️ 畫面預覽

> ✅ 建議搭配以下圖片檔案：
- `pic/tomato_all.png`
- `pic/tomato_half.png`
- `pic/tomato_little.png`
- `pic/relax.png`
- `pic/play-button.png`
- `pic/pause.png`
- `pic/setting_timer.png`
- `pic/tomato_icon.ico`

（請將上述圖片放在 `pic/` 資料夾中）

## 📦 安裝與執行方式

### 1️⃣ 安裝套件

請先安裝 Python 所需套件：

```bash
pip install matplotlib pillow
