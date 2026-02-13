import os
import logging
import subprocess
import json
from mcp.server.fastmcp import FastMCP
from git import Repo, InvalidGitRepositoryError
from github import Github

# --- CẤU HÌNH HỆ THỐNG ---
# Ép GitPython không kiểm tra quá khắt khe lúc khởi động để tránh lỗi trong Docker
os.environ["GIT_PYTHON_REFRESH"] = "quiet"

# Khởi tạo MCP Server trên cổng 8002
mcp = FastMCP("Git & GitHub Expert Manager", host="0.0.0.0", port=8002)

# Thiết lập Logging chi tiết
LOG_FILE = 'github_log.txt'
current_dir = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(current_dir, "git_expert.txt")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG, # Ghi nhận từ mức Debug trở lên
    format="%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s",
    force=True,
    encoding="utf-8"
)

# Khởi tạo GitHub Cloud Client
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
gh_client = Github(GITHUB_TOKEN) if GITHUB_TOKEN else None

if not GITHUB_TOKEN:
    logging.warning("GITHUB_TOKEN không tồn tại. Các tính năng Cloud sẽ bị hạn chế.")

# --- NHÓM 1: QUẢN TRỊ HỆ THỐNG TỆP & AN TOÀN ---

@mcp.tool()
def create_local_folder(path: str) -> str:
    """Tạo thư mục mới và cấu hình safe.directory cho Git."""
    logging.info(f"Yêu cầu tạo thư mục: {path}")
    try:
        os.makedirs(path, exist_ok=True)
        # Sửa lỗi bảo mật khi mount volume từ Host vào Docker
        subprocess.run(["git", "config", "--global", "--add", "safe.directory", path])
        logging.debug(f"Đã tạo và thiết lập safe.directory cho: {path}")
        return f"Thành công: Đã tạo thư mục {path}"
    except Exception as e:
        logging.error(f"Lỗi tạo thư mục {path}: {str(e)}")
        return f"Lỗi: {str(e)}"

@mcp.tool()
def git_init_safe(repo_path: str) -> str:
    """Khởi tạo Git repo và cấu hình an toàn."""
    logging.info(f"Khởi tạo Git tại: {repo_path}")
    try:
        subprocess.run(["git", "config", "--global", "--add", "safe.directory", repo_path])
        repo = Repo.init(repo_path)
        logging.debug(f"Git Init hoàn tất tại {repo_path}")
        return f"Đã khởi tạo repo tại: {repo_path}"
    except Exception as e:
        logging.error(f"Lỗi Init tại {repo_path}: {str(e)}")
        return f"Lỗi: {str(e)}"

# --- NHÓM 2: THAO TÁC LOCAL (GIT CORE) ---

@mcp.tool()
def git_full_status(repo_path: str) -> str:
    """Kiểm tra trạng thái chi tiết của repository."""
    logging.info(f"Kiểm tra status: {repo_path}")
    try:
        repo = Repo(repo_path)
        status = repo.git.status()
        logging.debug(f"Kết quả status cho {repo_path} đã được trích xuất.")
        return status
    except Exception as e:
        logging.error(f"Lỗi lấy status: {str(e)}")
        return f"Lỗi: {str(e)}"

@mcp.tool()
def git_add(repo_path: str, file_paths: list[str]) -> str:
    """Đưa file vào khu vực chờ commit (Staging Area)."""
    logging.info(f"Git Add: {file_paths} tại {repo_path}")
    try:
        repo = Repo(repo_path)
        repo.index.add(file_paths)
        logging.debug(f"Đã Stage {len(file_paths)} tệp tin.")
        return f"Đã add: {', '.join(file_paths)}"
    except Exception as e:
        logging.error(f"Lỗi Git Add: {str(e)}")
        return f"Lỗi: {str(e)}"

@mcp.tool()
def git_commit(repo_path: str, message: str) -> str:
    """Tạo commit mới với nội dung mô tả."""
    logging.info(f"Git Commit: '{message}' tại {repo_path}")
    try:
        repo = Repo(repo_path)
        new_commit = repo.index.commit(message)
        logging.info(f"Commit thành công: {new_commit.hexsha}")
        return f"Đã commit: {new_commit.hexsha}"
    except Exception as e:
        logging.error(f"Lỗi Commit: {str(e)}")
        return f"Lỗi: {str(e)}"

# --- NHÓM 3: ĐỒNG BỘ & CLOUD (SYNC) ---

@mcp.tool()
def git_clone(repo_url: str, local_path: str) -> str:
    """Clone repo từ URL. Tự động xử lý Auth qua Token."""
    logging.info(f"Đang Clone {repo_url} về {local_path}")
    try:
        url = repo_url
        if GITHUB_TOKEN and "github.com" in url and "@" not in url:
            url = url.replace("https://", f"https://{GITHUB_TOKEN}@")
            logging.debug("Đã nhúng Token vào URL để xác thực.")
            
        Repo.clone_from(url, local_path)
        subprocess.run(["git", "config", "--global", "--add", "safe.directory", local_path])
        return f"Clone thành công về {local_path}"
    except Exception as e:
        logging.error(f"Lỗi Clone: {str(e)}")
        return f"Lỗi: {str(e)}"

@mcp.tool()
def git_sync(repo_path: str, action: str, remote: str = "origin") -> str:
    """Đồng bộ code: 'pull' (kéo) hoặc 'push' (đẩy)."""
    logging.info(f"Thực hiện {action} tại {repo_path}")
    try:
        repo = Repo(repo_path)
        origin = repo.remote(name=remote)
        if action == "pull":
            origin.pull()
        else:
            origin.push()
        logging.debug(f"Hoàn tất {action} thành công.")
        return f"Đã {action} thành công."
    except Exception as e:
        logging.error(f"Lỗi Sync ({action}): {str(e)}")
        return f"Lỗi: {str(e)}"

@mcp.tool()
def create_remote_repo(name: str, description: str = "", private: bool = True) -> str:
    """Tạo Repository mới trên GitHub Cloud."""
    logging.info(f"Yêu cầu tạo Repo Cloud: {name}")
    if not gh_client: return "Lỗi: Không có GITHUB_TOKEN"
    try:
        user = gh_client.get_user()
        repo = user.create_repo(name=name, description=description, private=private)
        logging.info(f"Repo Cloud đã tạo: {repo.html_url}")
        return f"Đã tạo Repo: {repo.html_url}"
    except Exception as e:
        logging.error(f"Lỗi tạo Repo Cloud: {str(e)}")
        return f"Lỗi: {str(e)}"

# --- NHÓM 4: CẤU HÌNH & LỆNH NÂNG CAO ---

@mcp.tool()
def git_config_identity(repo_path: str, name: str, email: str) -> str:
    """Thiết lập user.name và user.email cho các commit."""
    logging.info(f"Cấu hình danh tính: {name} <{email}>")
    try:
        repo = Repo(repo_path)
        with repo.config_writer() as cw:
            cw.set_value("user", "name", name)
            cw.set_value("user", "email", email)
        return "Cấu hình danh tính thành công."
    except Exception as e:
        logging.error(f"Lỗi cấu hình danh tính: {str(e)}")
        return f"Lỗi: {str(e)}"

@mcp.tool()
def git_raw_command(repo_path: str, command: list[str]) -> str:
    """Thực thi lệnh Git thô (Raw) cho các trường hợp đặc biệt."""
    logging.info(f"Thực thi lệnh Raw: git {' '.join(command)}")
    try:
        repo = Repo(repo_path)
        result = repo.git.execute(["git"] + command)
        logging.debug(f"Kết quả lệnh Raw: {result}")
        return result
    except Exception as e:
        logging.error(f"Lỗi thực thi lệnh Raw: {str(e)}")
        return f"Lỗi: {str(e)}"

@mcp.tool()
def manage_gitignore(repo_path: str, action: str, pattern: str = "") -> str:
    """Quản lý tệp .gitignore (đọc/thêm)."""
    logging.debug(f"Manage .gitignore: {action} tại {repo_path}")
    path = os.path.join(repo_path, ".gitignore")
    try:
        if action == "read":
            if not os.path.exists(path): return ".gitignore không tồn tại."
            with open(path, 'r') as f: return f.read()
        elif action == "add":
            with open(path, 'a') as f:
                f.write(f"\n{pattern}")
            logging.info(f"Đã thêm '{pattern}' vào .gitignore")
            return f"Đã thêm {pattern}"
    except Exception as e:
        logging.error(f"Lỗi manage .gitignore: {str(e)}")
        return f"Lỗi: {str(e)}"

# --- KHỞI CHẠY SERVER ---
if __name__ == "__main__":
    logging.info("--- SERVER GIT EXPERT ĐANG KHỞI CHẠY TRÊN PORT 8002 ---")
    try:
        mcp.run(transport="sse")
    except Exception as e:
        logging.critical(f"SERVER CRASHED: {str(e)}")