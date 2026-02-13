# Sử dụng python slim làm gốc
FROM python:3.11-slim

# Cài đặt git hệ thống (Bắt buộc để GitPython hoạt động)
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy và cài đặt thư viện python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy mã nguồn server
COPY github_server.py .

# Expose cổng 8002
EXPOSE 8002

# Lệnh chạy server
CMD ["python", "github_server.py"]