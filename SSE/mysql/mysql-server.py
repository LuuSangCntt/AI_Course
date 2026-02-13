import mysql.connector
from mcp.server.fastmcp import FastMCP
from datetime import datetime
import contextlib
import os
import logging

# 1. Khởi tạo MCP Server
mcp = FastMCP(
    "MySQL Manager",
    host="0.0.0.0",  # Cho phép kết nối từ ngoài container
    port=8000,  # Port bên trong container
)

# Cấu hình logging chuyên nghiệp
current_dir = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(current_dir, "mysql_debug.txt")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True,
    encoding="utf-8"
)

db_config = {
    # Ưu tiên lấy từ biến môi trường, nếu không có mới dùng localhost
    "host": os.getenv("DB_HOST", "localhost"),
    "user": "root",
    "password": "p123456",
    "database": "DTN2025",
    "connect_timeout": 5,
}

@contextlib.contextmanager
def get_db_connection():
    """Quản lý kết nối an toàn."""
    conn = mysql.connector.connect(**db_config)
    try:
        yield conn
    finally:
        if conn.is_connected():
            conn.close()

@mcp.tool()
def execute_query(sql_query: str) -> str:
    """
    Thực thi các câu lệnh SQL trên database DTN2025.
    Hỗ trợ: SELECT, SHOW, DESCRIBE, INSERT, UPDATE.
    Cảnh báo: Hãy cẩn thận với các câu lệnh xóa dữ liệu.
    """
    logging.info(f"Yêu cầu thực thi SQL: {sql_query}")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(sql_query)
            
            if cursor.description:
                results = cursor.fetchall()
                # Chuyển đổi kết quả sang JSON string để LLM dễ xử lý hơn
                import json
                return json.dumps(results, indent=2, default=str)
            else:
                conn.commit()
                return f"Thành công. Số dòng bị ảnh hưởng: {cursor.rowcount}"
                
    except Exception as e:
        logging.error(f"LỖI SQL: {str(e)}")
        return f"Lỗi hệ thống SQL: {str(e)}"

if __name__ == "__main__":
    logging.info("--- SERVER MYSQL KHỞI ĐỘNG (SSE MODE) ---")
    # Chạy trên port 8001 để tránh đụng độ với server Calculator (port 8000)
    mcp.run(transport="sse")
    # mcp.run(transport="sse", host="0.0.0.0", port=8000)
