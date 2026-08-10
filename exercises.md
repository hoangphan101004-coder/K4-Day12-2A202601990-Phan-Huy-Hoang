# Phiếu Phản Ánh — K4 Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: thay dòng câu trả lời mẫu bằng câu trả lời thực tế của bạn.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Phan Huy Hoàng  Mã học viên: 2A202601990

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `api_token` không có giá trị mặc định nên app chết ngay khi
khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà việc
"chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

Khi deploy ứng dụng lên môi trường Cloud mà kỹ sư quên cấu hình biến môi trường `API_TOKEN` trên Dashboard. Nếu có giá trị mặc định là `"changeme"`, ứng dụng vẫn sẽ khởi động thành công và chấp nhận các request dùng token mặc định này. Kẻ tấn công hoặc các bot quét trên internet có thể tìm thấy endpoint và gọi free làm tiêu tốn toàn bộ chi phí API/LLM. Việc không set default token giúp app "chết sớm" (Fail Fast) ngay lúc vừa deploy, ném ra lỗi `ValidationError` rõ ràng trong log giúp nhận ra và bổ sung secret trước khi có traffic thực tế.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/chat` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

Dòng log JSON mẫu thu được:
`{"event": "chat_completed", "severity": "INFO", "ts": "2026-08-10T15:05:00+00:00", "client_id": "sv01", "prompt_tokens": 10, "completion_tokens": 25, "usd_cost": 0.00005}`

Hai việc làm được với log JSON:
1. **Lọc và truy vấn tự động bằng máy (Parsing/Querying)**: Các hệ thống gom log (Google Cloud Logging, Datadog) có thể bóc tách các trường JSON để lọc theo `severity`, theo `client_id` cụ thể, hoặc tính tổng `usd_cost` phát sinh trong ngày.
2. **Cảnh báo tự động (Alerting & Metrics)**: Dễ dàng thiết lập rule cảnh báo tự động (ví dụ: gửi thông báo qua Slack/PagerDuty khi `usd_cost` của một client tăng đột biến hoặc khi xuất hiện log có `severity: ERROR`).

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t chat:single .
docker build -t chat:multi .
docker images | grep chat
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | 1.45 GB |
| Multi-stage | 280 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

Phần dung lượng chênh lệch (~1.17 GB) bao gồm: các trình biên dịch mã nguồn (gcc, g++, make), header files phát triển, các công cụ build C-extensions, cache của pip và toàn bộ công cụ phát triển không cần thiết ở môi trường runtime. Stage runtime chỉ giữ lại python binaries đã biên dịch và các package cài đặt thực tế.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

Khi sửa 1 ký tự trong `app/main.py`, các layer từ `FROM`, `WORKDIR`, `COPY requirements.txt` và `RUN pip install` đều được Docker giữ lại từ cache. Chỉ có layer `COPY app ./app` và các lệnh phía sau phải chạy lại. Nếu đặt `COPY . .` lên trước `RUN pip install`, mỗi lần thay đổi 1 dòng code Python thì Docker sẽ hủy cache toàn bộ layer phía sau và phải thực thi lại lệnh `RUN pip install` từ đầu, làm thời gian build kéo dài đáng kể.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

Kẻ tấn công khai thác lỗi Remote Code Execution (RCE) trong code Python để chạy lệnh hệ thống trong container. Do container chia sẻ chung Linux kernel với máy host, nếu container chạy với quyền root (UID 0), kẻ tấn công sử dụng lỗ hổng container breakout để thoát khỏi container và có ngay quyền root quản trị trên máy host. Lệnh `USER appuser` cắt đứt chuỗi tấn công ngay từ bước đầu bằng cách ép container chạy dưới dạng user thường (non-root, UID 10001), khiến các lệnh do kẻ tấn công chèn vào không có đủ đặc quyền hệ thống để thực hiện các thao tác nguy hại hay breakout.

---

### Câu 6 — Bearer token (CP3)

Vì sao 401 phải kèm header `WWW-Authenticate: Bearer`? Và vì sao ta trả **cùng
một** thông báo lỗi cho cả ba trường hợp (thiếu header, sai scheme, sai token)
thay vì nói rõ sai ở đâu cho người dùng dễ sửa?

- Header `WWW-Authenticate: Bearer` là bắt buộc theo RFC 6750 để chỉ dẫn chuẩn xác cho client biết cơ chế xác thực mà server yêu cầu là Bearer token scheme.
- Trả cùng một thông báo lỗi chung nhằm đảm bảo nguyên tắc an toàn thông tin: không tiết lộ chi tiết lý do thất bại cho kẻ tấn công (tránh leak thông tin dò quét từng thành phần như phát hiện đúng format header hay đúng scheme).

---

### Câu 7 — Token bucket (CP3)

Với `capacity=10`, `refill_per_minute=10`: một client im lặng 10 phút rồi gửi
liên tiếp. Nó gửi được bao nhiêu request trước khi bị 429? Nếu bỏ đoạn
`min(capacity, ...)` trong `available()` thì con số đó thành bao nhiêu, và tại sao?

- Với `capacity=10`, client im lặng 10 phút vẫn chỉ gửi được tối đa 10 request liên tiếp trước khi nhận lỗi 429.
- Nếu bỏ `min(capacity, ...)`, xô sẽ tích lũy 10 (ban đầu) + 10 * 10 = 110 token. Con số đó sẽ thành 110 request liên tiếp, cho phép client gửi bùng nổ 110 request trong 1 giây gây nghẽn hệ thống.

---

### Câu 8 — Ngân sách theo ngày (CP3)

So sánh hạn mức $30/tháng với hạn mức $1/ngày cho cùng một client. Giả sử có sự
cố khiến một client gọi liên tục từ 2h sáng. Với mỗi cách, thiệt hại tối đa là
bao nhiêu và service tự hồi phục khi nào?

- Hạn mức $30/tháng: Thiệt hại tối đa là $30 (bị đốt sạch ngân sách cả tháng chỉ sau vài giờ sự cố). Service phải chờ tới đầu tháng sau (hoặc cần con người can thiệp reset) mới hoạt động lại.
- Hạn mức $1/ngày: Thiệt hại tối đa chỉ là $1.0. Khi đạt mốc $1.0, client bị chặn với lỗi 402. Sáng hôm sau (khi sang ngày UTC mới), key ngân sách ngày tự reset và service tự động phục hồi phục vụ bình thường mà không cần ai can thiệp.

---

### Câu 9 — /healthz khác /readyz (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

Thứ tự sự kiện khi gộp endpoint kiểm tra Redis:
1. Redis mất kết nối 30 giây -> Endpoint chung trả về 503 Unhealthy.
2. Orchestrator (K8s/Docker) tưởng ứng dụng bị chết process nên lập tức tiêu diệt (kill) và khởi động lại (restart) cả 3 container.
3. Cả 3 container cùng rơi vào vòng lặp restart làm sập toàn bộ hệ thống (downtime).
4. Sau 30s Redis khôi phục, các container vẫn đang bận khởi động lại làm kéo dài sự cố gián đoạn dịch vụ.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

Lỗi gặp phải: Health check timeout khi deploy lên Cloud (`Container failed to respond on port 8000 within timeout`).
Nguyên nhân: Môi trường Cloud tự cấp phát cổng ngẫu nhiên qua biến môi trường `$PORT`, trong khi uvicorn đang cố định chạy trên cổng 8000.
Cách sửa: Đổi lệnh chạy uvicorn trong Dockerfile và script khởi chạy thành `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}` để ứng dụng tự động đọc cổng do Cloud cấp phát.
