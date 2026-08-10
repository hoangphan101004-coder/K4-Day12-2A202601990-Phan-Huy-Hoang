# Thông Tin Deploy — Checkpoint 5

> Điền file này sau khi deploy xong. `pytest tests/test_cp5.py` đọc file này
> để tìm địa chỉ service của bạn và gọi thử.
>
> **Chỉ ghi TÊN biến môi trường, tuyệt đối không dán giá trị token vào đây.**
> Repo này công khai — dán token vào là mất token.

## Thông Tin Học Viên

| Mục | Nội dung |
|-----|----------|
| Họ và tên | Phan Huy Hoàng |
| Mã học viên | 2A202601990 |
| Repo | https://github.com/hoangphan101004-coder/K4-Day12-2A202601990-Phan-Huy-Hoang |

## Service

| Mục | Nội dung |
|-----|----------|
| Public URL | https://k4-day12-2a202601990-phan-huy-hoang.up.railway.app |
| Platform | Railway |
| Ngày deploy | 2026-08-10 |

## Biến Môi Trường Đã Set Trên Cloud

Ghi tên biến và **nguồn giá trị**, không ghi giá trị:

| Biến | Đã set | Ghi chú |
|------|--------|---------|
| `PORT` | ✅ | platform tự gán |
| `API_TOKEN` | ✅ | đặt trong dashboard, không nằm trong repo |
| `REDIS_URL` | ✅ | Redis add-on của Railway |
| `BUCKET_CAPACITY` | ✅ | 10 |
| `REFILL_PER_MINUTE` | ✅ | 10 |
| `DAILY_BUDGET_USD` | ✅ | 1.0 |
| `LOG_LEVEL` | ✅ | INFO |

## Lệnh Kiểm Tra

Thay `<URL>` bằng Public URL ở trên:

```bash
# 1. Liveness — mong đợi 200 {"status":"ok"}
curl -i https://k4-day12-2a202601990-phan-huy-hoang.up.railway.app/healthz

# 2. Readiness — mong đợi 200 {"status":"ready"} (đã nối được Redis)
curl -i https://k4-day12-2a202601990-phan-huy-hoang.up.railway.app/readyz

# 3. Không có token — mong đợi 401 kèm header WWW-Authenticate
curl -i -X POST https://k4-day12-2a202601990-phan-huy-hoang.up.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello"}'

# 4. Có token — mong đợi 200 kèm câu trả lời
curl -i -X POST https://k4-day12-2a202601990-phan-huy-hoang.up.railway.app/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "X-Client-Id: sv-test" \
  -d '{"message":"Deploy là gì?"}'

# 5. Rate limit — gọi 15 lần, những lần cuối phải trả 429
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code} " -X POST https://k4-day12-2a202601990-phan-huy-hoang.up.railway.app/chat \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "X-Client-Id: sv-test" \
    -d '{"message":"test"}'
done; echo
```

## Kết Quả Đã Ghi Nhận Trước Đây

> Kiểm tra lại ngày 2026-08-10 cho thấy Public URL hiện trả `404 Not Found`
> ở `/healthz`, `/readyz` và `/chat`. Khối output bên dưới là kết quả đã ghi
> trước đó, chưa phải trạng thái live hiện tại. Cần deploy lại, kiểm tra domain
> Railway rồi thay khối này bằng output mới trước khi nộp.

Dán output của các lệnh trên vào đây:

```
HTTP/1.1 200 OK
{"status":"ok","service":"day12-chat-service","version":"1.0.0"}

HTTP/1.1 200 OK
{"status":"ready","redis":true}

HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer
{"detail":"invalid or missing bearer token"}

HTTP/1.1 200 OK
{"reply":"Deploy là việc đưa ứng dụng từ môi trường phát triển (localhost) lên hạ tầng hạ tầng server công khai.","client_id":"sv-test","turns_before":0,"usd_cost":0.00005,"usage":{"prompt":10,"completion":25}}

200 200 200 200 200 200 200 200 200 200 429 429 429 429 429
```

## Ảnh Chụp Màn Hình

Đặt ảnh trong thư mục `screenshots/`:

- `screenshots/dashboard.png` — trang quản lý service trên platform
- `screenshots/healthz.png` — kết quả gọi `/healthz` từ trình duyệt hoặc curl
