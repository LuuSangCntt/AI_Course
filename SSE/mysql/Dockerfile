# Sử dụng Python bản nhẹ
FROM python:3.11-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt các thư viện cần thiết
# Lưu ý: cài 'mcp[cli]' để hỗ trợ chạy server sse
RUN pip install --no-cache-dir mcp[cli] mysql-connector-python
RUN pip install --no-cache-dir uvicorn

# Copy file code vào container
COPY mysql-server.py .

# Biến môi trường để FastMCP biết là chạy SSE
ENV MCP_TRANSPORT=sse

# Mở cổng 8000 bên trong container
EXPOSE 8000

# Lệnh chạy server
CMD ["python", "mysql-server.py"]