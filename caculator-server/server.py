import sys
import os
from mcp.server.fastmcp import FastMCP

# Khởi tạo FastMCP
mcp = FastMCP("Advanced Calculator")

# Hàm helper để ghi log ra một file riêng trong cùng thư mục để bạn dễ theo dõi
def local_log(message):
    with open("debug_mcp.txt", "a", encoding="utf-8") as f:
        f.write(message + "\n")
        f.flush() # Ép dữ liệu xuống ổ cứng ngay lập tức
        os.fsync(f.fileno()) # Đảm bảo hệ điều hành đã ghi xong

@mcp.tool()
def add(a: float, b: float) -> float:
    """Cộng hai số."""
    local_log(f"Gọi hàm cộng: {a} + {b}")
    return a + b

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Trừ số thứ hai khỏi số thứ nhất."""
    local_log(f"Gọi hàm trừ: {a} - {b}")
    return a - b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Nhân hai số."""
    local_log(f"Gọi hàm nhân: {a} * {b}")
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> str:
    """Chia số thứ nhất cho số thứ hai. Trả về thông báo nếu chia cho 0."""
    local_log(f"Gọi hàm chia: {a} / {b}")
    if b == 0:
        return "Lỗi: Không thể chia cho số 0!"
    return str(a / b)

if __name__ == "__main__":
    local_log("--- Server bắt đầu chạy ---")
    mcp.run(transport="stdio")