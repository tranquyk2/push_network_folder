# NAS Uploader — MVP

Phần mềm kéo-thả file lên ổ mạng nội bộ (NAS / Windows share), viết bằng Python + PyQt6.

## Cài đặt (trên Windows)

1. Cài Python 3.10+ nếu chưa có: https://www.python.org/downloads/
2. Mở terminal (cmd/PowerShell) tại thư mục chứa `main.py`, chạy:
   ```
   pip install -r requirements.txt
   ```
3. Chạy app:
   ```
   python main.py
   ```

## Cách dùng

1. Mở app, ở ô "Thư mục đích" nhập đường dẫn ổ chung, ví dụ:
   ```
   \\server\share\Uploads
   ```
   hoặc bấm **Chọn...** để duyệt tới ổ đã map (ví dụ `Z:\`).
2. Kéo file (hoặc cả thư mục) từ File Explorer thả vào vùng kéo-thả.
3. App tự động copy sang thư mục đích, hiển thị tiến trình và kết quả từng file.
4. Nếu file trùng tên nhưng **khác nội dung** → tự đổi tên thành `ten_1.ext`, `ten_2.ext`...
5. Nếu file trùng **cả tên lẫn nội dung** (hash giống hệt) → tự động bỏ qua, không copy lại.
6. Lịch sử mọi lần upload được lưu vào `~/.nas_uploader/history.db` (SQLite), có thể mở bằng
   DB Browser for SQLite để xem lại sau này.

## Cấu trúc code (hiện tại gói gọn trong 1 file để dễ đọc)

- `load_config` / `save_config`: nhớ thư mục đích giữa các lần mở app.
- `init_db` / `log_history`: ghi log SQLite (file, nguồn, đích, trạng thái, thời gian).
- `file_hash`: tính SHA-256 để so sánh trùng lặp nội dung.
- `CopyWorker` (QThread): chạy copy ở luồng nền — **không đơ giao diện** khi copy file lớn/nhiều file.
  Có retry tự động (2 lần) nếu copy lỗi (ví dụ rớt mạng tạm thời).
- `DropZone`: vùng kéo-thả, đổi màu khi kéo file vào.
- `MainWindow`: ghép toàn bộ giao diện lại.

## Những gì CHƯA có trong bản MVP này (đúng như lộ trình đã bàn)

Đây là bản **giai đoạn 1**, tập trung vào cốt lõi chạy ổn định trước. Các tính năng sau
sẽ thêm ở bước tiếp theo nếu bạn muốn:

- [ ] System tray icon (thu gọn xuống khay hệ thống)
- [ ] Global hotkey (Ctrl+Shift+V để dán file từ clipboard thẳng vào ổ chung)
- [ ] Watch folder tự động (theo dõi thư mục nguồn, tự đẩy file mới)
- [ ] Đóng gói thành file `.exe` bằng PyInstaller để chạy trên máy không có Python
- [ ] Kiểm tra định kỳ trạng thái kết nối ổ chung (còn mạng hay không)
- [ ] Xem lịch sử ngay trong giao diện (hiện tại phải mở file SQLite riêng)

## Đóng gói thành .exe (khi cần)

```
pip install pyinstaller
pyinstaller --onefile --windowed --name NASUploader main.py
```
File `.exe` sẽ nằm trong thư mục `dist/`.
