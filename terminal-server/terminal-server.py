import os
import subprocess
import logging
import sys
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Terminal Manager")

# Chỉ ghi log vào file, triệt tiêu mọi thông báo ra màn hình
logging.basicConfig(
    filename="terminal_final_debug.txt",
    level=logging.DEBUG,
    format="%(asctime)s - %(message)s",
    force=True
)

@mcp.tool()
def execute_command(command: str, cwd: str = r"C:\WORKDATA_SANG\AI_Course\MCP_Local") -> str:
    """Thực thi lệnh với sự cách ly tuyệt đối cho Windows."""
    try:
        # Chạy lệnh nhưng chuyển hướng stderr vào stdout và bắt chúng lại
        # stdin=DEVNULL ngăn chặn việc lệnh chờ người dùng nhập liệu gây treo
        process = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace", # Xử lý các ký tự Windows đặc biệt không gây lỗi JSON
            stdin=subprocess.DEVNULL 
        )
        
        output = process.stdout + process.stderr
        return output.strip() if output.strip() else "Lệnh đã hoàn thành."
    except Exception as e:
        return f"Lỗi thực thi: {str(e)}"

if __name__ == "__main__":
    # Tắt hoàn toàn việc in các thông tin debug của thư viện ra stdout
    # Đây là bước sống còn để MCP không bị Timeout trên Windows
    import asyncio
    logging.getLogger('asyncio').setLevel(logging.CRITICAL)
    mcp.run()