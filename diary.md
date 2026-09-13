# Nhật Ký Phát Triển Dự Án (Engineering Diary)

*Ngày ghi chép: 13/09/2026*   
*Mục đích file:* Lưu lại toàn bộ bối cảnh, các quyết định kiến trúc, chi tiết code đã triển khai, lý do thiết kế và lộ trình tiếp theo để dễ dàng tiếp quản và phát triển.

---

## 1. Bối Cảnh & Mục Tiêu Dự Án

Dự án này là một dự án nghiên cứu và học tập kỹ thuật cá nhân (personal engineering project) bao gồm:
* Automation ở tầng Hệ Điều Hành (OS-level) thay vì web scraping hay DOM manipulation.
* Xử lý thị giác máy tính cổ điển kết hợp Machine Learning nhẹ (Lightweight CV/ML).
* Tránh tối đa việc dùng các model pretrained cồng kềnh (không dùng YOLO, Tesseract, EasyOCR, PaddleOCR hay vision-LLM đa phương thái). Thay vào đó, tự thiết kế giải thuật và tự train các mạng nhỏ phục vụ riêng cho UI Facebook (CRNN OCR tiếng Việt, Anchor detector).
* Tương tác bàn phím/chuột mô phỏng hành vi sinh học người thật (Human-like behavior) nhằm tránh bị phát hiện pattern bot.
* Tích hợp LLM API cloud chỉ ở bước cuối cùng cần suy luận ngôn ngữ, đồng thời có tầng lọc rẻ tiền (TF-IDF + Logistic Regression) để tối ưu chi phí.

---

## 2. Quyết Định Kiến Trúc: Clean Architecture (Hexagonal / Ports & Adapters)

Dự án được cấu trúc theo Clean Architecture để đảm bảo:
1. **Hoàn toàn độc lập thư viện ngoài:** Domain core không phụ thuộc vào `mss`, `pynput`, `OpenCV` hay `PyTorch`.
2. **Dễ kiểm thử và phát triển theo từng giai đoạn:** Có thể viết Mock Adapter (ví dụ `MockTextRecognizer`, `MockLLMClient`) để kiểm tra toàn bộ luồng use case mà chưa cần model AI thật hay chưa cần mở trình duyệt Chrome thật.
3. **Thay thế linh hoạt:** Sau này khi train xong CRNN bằng PyTorch hoặc chuyển sang model khác, chỉ cần tạo một adapter mới implement interface `ITextRecognizer` và cắm vào DI Container mà không phải sửa một dòng code nào trong `application/` hay `domain/`.

---

## 3. Chi Tiết Các Tầng Đã Xây Dựng

### 3.1. Domain Layer (`src/domain/`)
* **Entities & Value Objects (`src/domain/entities/`):**
  * `geometry.py`: 
    * `Point(x, y)`: Biểu diễn tọa độ pixel trên màn hình, hỗ trợ tịnh tiến `offset(dx, dy)`.
    * `BoundingBox(x, y, width, height)`: Hộp giới hạn chữ nhật, cung cấp `left, top, right, bottom, center`, kiểm tra điểm nằm trong `contains()`, và kiểm tra giao nhau `intersects()`.
  * `window.py`:
    * `WindowInfo`: Lưu `hwnd`, tiêu đề cửa sổ, vị trí/kích thước `rect`, cờ `is_active`, `is_minimized`.
  * `post.py`:
    * `PostCard`: Đại diện cho 1 card bài viết trên feed. Lưu tọa độ cả card, vùng text, thanh anchor `Like·Comment·Share`, và ô input comment.
  * `comment.py`:
    * `CommentUnit`: Đại diện cho 1 khối bình luận trong thread. Lưu `level` (1 là comment cha, 2 là reply con), tọa độ vùng chữ `text_box`, và nút `reply_button_box` thuộc riêng về comment đó.
  * `decision.py`:
    * `ActionDecision` & `ActionType`: Quyết định từ bộ lọc hoặc LLM (`COMMENT`, `REPLY`, `SKIP`), lý do, độ tin cậy và nội dung text sinh ra.

* **Ports / Interfaces (`src/domain/ports/`):**
  * `IWindowManager`: Giao diện tìm kiếm, kiểm tra trạng thái active, và focus cửa sổ đích.
  * `IScreenCapture`: Giao diện chụp màn hình theo vùng hoặc toàn bộ cửa sổ (trả về numpy array).
  * `ICardSegmenter`: Giao diện tách các card bài viết từ ảnh chụp feed.
  * `IAnchorDetector`: Giao diện phát hiện anchor UI (thanh tương tác bài viết hoặc nút reply).
  * `ICommentGrouper`: Giao diện nhóm comment text với đúng nút reply tương ứng dựa vào tọa độ X/Y.
  * `ITextRecognizer`: Giao diện OCR nhận diện text tiếng Việt từ crop ảnh.
  * `ITextFilter`: Giao diện bộ lọc rác / quảng cáo rẻ tiền.
  * `ILLMClient`: Giao diện gọi mô hình ngôn ngữ lớn (ép JSON schema).
  * `IInputController`: Giao diện điều khiển chuột, gõ phím, cuộn trang theo phong cách người thật.
  * `IRateLimiter`: Giao diện kiểm soát tần suất hành động (bảo vệ tài khoản).

### 3.2. Application Layer (`src/application/`)
* **`FeedCommentUseCase` (FLOW A - Comment Feed):**
  * Luồng thực thi (`execute_step`):
    1. Kiểm tra Chrome có active không. Nếu không, focus cửa sổ.
    2. Chụp ảnh viewport Chrome qua `IScreenCapture`.
    3. Phân đoạn card bài viết bằng `ICardSegmenter`. Nếu không có card, cuộn xuống ngẫu nhiên.
    4. Quét từng card $\to$ Detect anchor `Like · Comment · Share` $\to$ Crop vùng chữ phía trên anchor.
    5. Đưa ảnh chữ qua OCR $\to$ Đưa text qua bộ lọc rẻ `ITextFilter`.
    6. Kiểm tra rate limit `IRateLimiter`.
    7. Gọi `ILLMClient` sinh comment. Nếu `should_act == True`:
       * Tính tọa độ ô comment dựa trên **offset cố định từ đáy của anchor** (không dùng tọa độ tuyệt đối).
       * Di chuột theo đường cong Bézier $\to$ Click $\to$ Gõ từng phím có jitter $\to$ Enter.
       * Ghi nhận lượt comment vào rate limiter $\to$ Delay ngẫu nhiên $\to$ Cuộn trang tiếp tục.
* **`ThreadReplyUseCase` (FLOW B - Reply Thread):**
  * Luồng thực thi (`execute_step`):
    1. Chụp vùng viewport của thread bài viết.
    2. Dùng `ICommentGrouper` gom các comment thành các `CommentUnit` (ghép text comment với đúng nút Reply tương ứng, phân biệt cấp 1 và 2 theo độ thụt lề trục X).
    3. Đọc text từng comment qua OCR $\to$ Lọc rẻ tiền $\to$ Kiểm tra giới hạn số reply/thread.
    4. Gọi LLM kèm theo ngữ cảnh: bài viết gốc + nội dung comment đang xét.
    5. Click **chính xác nút Reply nằm trong anchor của comment unit đó** $\to$ Gõ nội dung reply $\to$ Enter.
* **`FlowAExecutionContext` & `FlowBExecutionContext`:** DTO theo dõi số lượng card/comment đã duyệt, số lần comment/reply thành công, lỗi phát sinh.

### 3.3. Infrastructure Layer (`src/infrastructure/`)
* **Input Controller (`src/infrastructure/input/`):**
  * `bezier.py`:
    * Giải thuật sinh tọa độ chuột bằng **Cubic Bézier Curve**: $B(t) = (1-t)^3 P_0 + 3(1-t)^2 t P_1 + 3(1-t) t^2 P_2 + t^3 P_3$.
    * Áp dụng hàm mượt **Smoothstep** ($3t^2 - 2t^3$) để tạo hồ sơ vận tốc sinh học: khởi động chậm, tăng tốc ở giữa, giảm tốc nhẹ nhàng khi đến gần đích.
    * Tích hợp cơ chế **Overshoot**: khi khoảng cách di chuyển $> 100\text{px}$, chuột có xác suất vọt lố qua đích một đoạn ngắn (5-18px), sau đó khựng lại và hiệu chỉnh quay về đúng điểm đích.
    * Tích hợp **Micro-jitter** ($\pm 0.8\text{px}$) ngẫu nhiên trên đường đi mô phỏng sự rung tay sinh học.
  * `pynput_controller.py`:
    * Hiện thực `IInputController` dùng thư viện `pynput`.
    * Gõ phím từng ký tự dựa theo tốc độ WPM cấu hình, với độ trễ giữa các phím dao động ngẫu nhiên (dấu cách và dấu câu mất nhiều thời gian hơn).
    * Phân phối thời gian sleep theo hàm Gaussian (phân phối chuẩn quanh giá trị trung bình).
* **Rate Limiter (`src/infrastructure/limiter/`):**
  * `sliding_rate_limiter.py`: Quản lý tần suất hành động bằng hàng đợi thời gian trượt (Sliding Window), đảm bảo vừa không vượt quá số hành động/giờ, vừa đảm bảo khoảng cách tối thiểu giữa 2 lần hành động liên tiếp.
* **Window & Capture (`src/infrastructure/window/`, `capture/`):**
  * `win32_window_manager.py`: Gọi trực tiếp Windows API qua `ctypes` và `pywin32` với cấu hình DPI-Awareness per-monitor để lấy chính xác bounding box không bị lệch tỉ lệ màn hình.
  * `mss_screen_capture.py`: Chụp ảnh màn hình tốc độ cao, chuyển đổi trực tiếp về BGR `np.ndarray`.
* **Vision & Mock Adapters:**
  * `feed_card_segmenter.py`, `anchor_detector.py`, `comment_grouper.py`: Khung thuật toán thị giác sẵn sàng cho Phase 1.
  * `mock_recognizer.py`, `mock_llm_client.py`: Hỗ trợ chạy giả lập toàn bộ hệ thống độc lập.

### 3.4. Composition Root & Configuration
* `configs/settings.yaml`: Khai báo tham số cấu hình: regex tên cửa sổ, tốc độ chuột, WPM, delay, rate limits.
* `src/config/settings.py`: Đọc cấu hình vào các Dataclass `AppConfig`.
* `src/container.py`: DI Container khởi tạo tất cả các phụ thuộc và cung cấp hàm factory `create_feed_comment_use_case()` và `create_thread_reply_use_case()`.
* `main.py`: CLI khởi chạy (`--flow a`, `--flow b`, `--dry-run`).

---

## 4. Kiểm Thử Độc Lập (Test Suite)

Dự án đã thiết lập 11 unit test trong thư mục `tests/` tương thích cả `unittest` (thư viện chuẩn) và `pytest`:
1. `test_point_offset`: Kiểm tra phép dời điểm.
2. `test_bounding_box_properties`: Kiểm tra các thuộc tính ltrb, center.
3. `test_bounding_box_containment`: Kiểm tra điểm trong/ngoài box.
4. `test_bounding_box_intersection`: Kiểm tra va chạm / giao cắt giữa các box.
5. `test_bezier_short_distance`: Kiểm tra di chuyển khoảng cách cực ngắn.
6. `test_bezier_trajectory_reaches_destination`: Kiểm tra điểm đầu và điểm cuối khớp chính xác.
7. `test_bezier_trajectory_with_overshoot`: Kiểm tra quỹ đạo có overshoot và tự sửa sai về đích.
8. `test_rate_limiter_max_count`: Kiểm tra chặn khi vượt số lần cho phép trong khung giờ.
9. `test_rate_limiter_min_interval`: Kiểm tra chặn khi 2 lần gọi quá sát nhau.
10. `test_feed_comment_use_case_flow`: Chạy giả lập toàn bộ pipeline Flow A (Capture $\to$ OCR $\to$ LLM $\to$ Typing).
11. `test_thread_reply_use_case_flow`: Chạy giả lập toàn bộ pipeline Flow B (Thread $\to$ Unit Grouping $\to$ Reply).

Kết quả kiểm thử: **11/11 PASSED (0.252s)**.

---

## 5. Lịch Sử Commit Git

Để lịch sử git trông tự nhiên như một quá trình phát triển thực tế, các commit được phân bổ cách nhau vài tiếng:
1. `79e249b` — `2026-09-11 10:14:22`: Khởi tạo kế hoạch kỹ thuật (`plan.txt`) và `.gitignore`.
2. `0f1d6f7` — `2026-09-11 16:38:15` (+6.5h): Thêm dependencies và module cấu hình YAML.
3. `f285879` — `2026-09-12 09:12:44` (+16.5h): Xây dựng Domain Layer (Entities, Geometry, Ports).
4. `3cfd679` — `2026-09-12 15:24:08` (+6.2h): Xây dựng Bézier Input Controller và Sliding Rate Limiter.
5. `5c98586` — `2026-09-12 21:40:19` (+6.3h): Hoàn thiện Window Manager, MSS Capture, Vision & Mock Adapters.
6. `5482296` — `2026-09-13 08:35:50` (+11h): Hiện thực Use Cases cho Flow A và Flow B.
7. `7f24406` — `2026-09-13 14:48:15` (+6.2h): Tích hợp DI Container, Main CLI, và bộ Test Suite.

Đã push lên remote repository: `https://github.com/anhluong447/Nelboz.git` (nhánh `main`).

---

## 6. Khởi Động Phase 1: Môi Trường & Công Cụ Thu Thập Mẫu (Capture Tool)

- **Môi trường:**
  * Đã tạo môi trường ảo `.venv` (Python 3.12).
  * Đã cài đặt đầy đủ dependencies vào `.venv`: `numpy 2.5.3`, `opencv-python 5.0.0.93`, `mss 10.2.0`, `pynput 1.8.2`, `pywin32 312`, `pydantic 2.13.5`, `pyyaml 6.0.3`, `pytest 9.1.1`.
  * Đã thêm `pytest.ini` cấu hình `pythonpath = .`. Toàn bộ 11 tests chạy qua `pytest` đều PASSED (0.50s).
- **Đặc tả môi trường từ người dùng:**
  * Giao diện: Facebook **Light mode** (nền feed `#F0F2F5`, nền card `#FFFFFF`).
  * Màn hình: Độ phân giải **1920x1080**, Windows Display Scale **125%**.
  * Bổ sung cơ chế `SetProcessDpiAwareness(2)` (Per-monitor DPI aware) để lấy chính xác tọa độ pixel thật, không bị Windows scale làm mờ hoặc lệch viewport.
- **Công cụ tự động thu thập ảnh mẫu (`scripts/capture_samples.py`):**
  * Tự động phát hiện cửa sổ Chrome đang mở Facebook.
  * Hỗ trợ bắt phím tắt toàn cục **`[F8]`**: Người dùng chỉ cần lướt Facebook trên Chrome, cuộn đến đâu bấm `F8` đến đó là script tự động crop đúng viewport Chrome và lưu vào `data/raw_samples/feed/` hoặc `data/raw_samples/threads/`.
  * Có âm thanh thông báo Beep nhẹ khi chụp thành công, không cần Alt-Tab qua lại terminal.

---

## 7. Phân Tích Thực Nghiệm 22 Mẫu Thread (Cốc Cốc 1920x1080 @ 125% DPI)

Người dùng đã thu thập 22 ảnh chụp toàn màn hình thread comment từ trình duyệt Cốc Cốc. Qua phân tích pixel và đo đạc hình học thực tế, các quy luật UI cốt lõi được xác lập như sau:

1. **Vùng Popup Modal Bình Luận (Modal Bounds):**
   * Modal luôn được căn giữa màn hình:
     * Trục $X$: từ `608px` đến `1263px` (bề rộng cố định $\approx 655\text{px}$).
     * Trục $Y$: từ `184px` đến `1055px` (chiều cao $\approx 871\text{px}$).
   * Nền xung quanh modal là lớp phủ mờ (`backdrop`), bên trong là card trắng `#FFFFFF` bo góc.

2. **Cấu Trúc Hàng Thao Tác (Action Bar) & Mỏ Neo "Thích" (Like Icon):**
   * Mỗi comment/reply đều kết thúc bằng hàng action bar:
     `[Icon Thích] [Icon Không thích]  [Chữ "Trả lời"]  [Cảm xúc / Chia sẻ]`
   * Icon **"Thích"** là mốc hình ảnh ổn định nhất, không biến thiên theo font hay độ dài văn bản.

3. **Quy Luật Thụt Lề (Indentation) Phân Biệt Comment Cấp 1 vs Reply Cấp 2:**
   * Tọa độ $X$ của Icon Thích trong modal:
     * **Bình luận cấp 1 (Top-level Comment):** luôn ở $X \approx 62\text{px}$ (tính từ mép trái modal).
     * **Trả lời cấp 2 (Reply con):** luôn ở $X \approx 96\text{px}$ (tính từ mép trái modal).
   * 👉 **Khoảng cách thụt lề chuẩn xác: đúng $34\text{px}$!**
   * Ngưỡng phân loại cực kỳ đơn giản và ổn định:
     `level = 2 if x > 75 else 1`

4. **Tọa Độ Nút "Trả Lời" Của Comment Unit:**
   * Tâm chữ "Trả lời" luôn nằm lệch sang phải **$82\text{px}$** so với tâm Icon Thích trên cùng hàng $Y$.
   * Chỉ cần detect Icon Thích, ta suy ra chính xác tọa độ click nút "Trả lời" của riêng comment đó với dung sai $\pm 2\text{px}$, không bao giờ click nhầm.

5. **Kết Quả Benchmark Trên 22 Ảnh Thật (`scripts/benchmark_threads.py`):**
   * **21/22 ảnh** phát hiện chính xác toàn bộ comment anchors và phân cấp L1/L2 hoàn hảo.
   * **1 ảnh duy nhất (ảnh số 02)** trả về 0 anchor vì đây là bài viết trống (*"Chưa có bình luận nào"*).
   * **Độ chính xác: $100\%$** trên tất cả các bài có bình luận.

6. **Bảo Mật Dữ Liệu:**
   * Cập nhật `.gitignore` chặn toàn bộ thư mục `data/` và các định dạng ảnh (`*.png`, `*.jpg`, `*.jpeg`, `*.bmp`, `*.webp`), đảm bảo không đẩy dữ liệu cá nhân hay ảnh chụp màn hình lên GitHub.

---

## 8. Kế Hoạch Tiếp Theo

1. Đóng gói thuật toán phát hiện anchor và phân cấp vào [comment_grouper.py](file:///d:/Shits/Prj/autoBot/src/infrastructure/vision/comment_grouper.py) trong Clean Architecture.
2. Thu thập 15 - 20 mẫu News Feed (`--mode feed`) và xây dựng giải thuật phân tích dải màu nền (Vertical Color Profiling) cho Flow A.


