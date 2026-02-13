import os
from mcp.server.fastmcp import FastMCP
import logging
# Khởi tạo FastMCP
mcp = FastMCP("Advanced Calculator")
"""CHỈ MANG TÍNH CHẤT ĐỂ TEST MCP SERVER KO THÔI"""

# Cấu hình logging
current_dir = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(current_dir, "git_debug.txt")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True,
    encoding="utf-8"
)


@mcp.tool()
def add(a: float, b: float) -> float:
    """Cộng hai số."""
    logging.debug(f"Gọi hàm cộng: {a} + {b}")
    return a + b

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Trừ số thứ hai khỏi số thứ nhất."""
    logging.debug(f"Gọi hàm trừ: {a} - {b}")
    return a - b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Nhân hai số."""
    logging.debug(f"Gọi hàm nhân: {a} * {b}")
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> str:
    """Chia số thứ nhất cho số thứ hai. Trả về thông báo nếu chia cho 0."""
    logging.debug(f"Gọi hàm chia: {a} / {b}")
    if b == 0:
        return "Lỗi: Không thể chia cho số 0!"
    return str(a / b)

if __name__ == "__main__":
    logging.debug("--- SSE Server bắt đầu khởi động ---")
    # Thay vì mcp.run(transport="stdio"), chúng ta dùng lệnh run của FastMCP 
    # nhưng cấu hình cho SSE thông qua việc chỉ định interface
    mcp.run(transport="sse")