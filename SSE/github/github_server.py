import os
import logging
import subprocess
import shutil
from mcp.server.fastmcp import FastMCP
from git import Repo, InvalidGitRepositoryError
from github import Github
import json

# Ép GitPython không kiểm tra quá khắt khe lúc khởi động
os.environ["GIT_PYTHON_REFRESH"] = "quiet"

# 1. Khởi tạo MCP Server trên cổng 8002
mcp = FastMCP("Git & GitHub Expert Manager", host="0.0.0.0", port=8002)

# Logging chuyên nghiệp
current_dir = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(current_dir, "git_expert.txt")
logging.basicConfig(
    filename=LOG_FILE, 
    level=logging.DEBUG, 
    format="%(asctime)s - %(levelname)s - %(message)s", 
    force=True,
    encoding="utf-8"
)

# Khởi tạo GitHub API Client (Xác thực Cloud)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
gh_client = Github(GITHUB_TOKEN) if GITHUB_TOKEN else None

# --- NHÓM 1: HỆ THỐNG TỆP & CẤU HÌNH AN TOÀN ---

@mcp.tool()
def create_local_folder(path: str) -> str:
    """Tạo một thư mục mới tại đường dẫn chỉ định (trong container/mount volume)."""
    try:
        os.makedirs(path, exist_ok=True)
        # Tự động add vào safe.directory để tránh lỗi permission của Git
        subprocess.run(["git", "config", "--global", "--add", "safe.directory", path])
        return f"Đã tạo thư mục thành công: {path}"
    except Exception as e:
        return f"Lỗi tạo thư mục: {str(e)}"

@mcp.tool()
def git_init_safe(repo_path: str) -> str:
    """Khởi tạo hoặc đánh dấu một thư mục là an toàn để Git có thể truy cập."""
    try:
        subprocess.run(["git", "config", "--global", "--add", "safe.directory", repo_path])
        repo = Repo.init(repo_path)
        return f"Đã thiết lập an toàn và khởi tạo repo tại: {repo_path}"
    except Exception as e:
        return f"Lỗi: {str(e)}"

# --- NHÓM 2: THAO TÁC LOCAL (GitPython) ---

@mcp.tool()
def git_full_status(repo_path: str) -> str:
    """Kiểm tra trạng thái chi tiết, các file thay đổi, file chưa track."""
    try:
        repo = Repo(repo_path)
        return repo.git.status()
    except Exception as e: return f"Lỗi: {str(e)}"

@mcp.tool()
def git_clone(repo_url: str, local_path: str) -> str:
    """Clone một repository về thư mục local. Tự động chèn Token để Auth nếu cần."""
    try:
        url = repo_url
        if GITHUB_TOKEN and "github.com" in url and "@" not in url:
            url = url.replace("https://", f"https://{GITHUB_TOKEN}@")
            
        Repo.clone_from(url, local_path)
        subprocess.run(["git", "config", "--global", "--add", "safe.directory", local_path])
        return f"Đã clone thành công về {local_path}"
    except Exception as e:
        return f"Lỗi clone: {str(e)}"

@mcp.tool()
def git_sync(repo_path: str, action: str, remote: str = "origin", branch: str = "main") -> str:
    """Thực hiện pull hoặc push code. action: 'pull' hoặc 'push'."""
    try:
        repo = Repo(repo_path)
        origin = repo.remote(name=remote)
        if action == "pull":
            origin.pull()
            return "Đã kéo code mới nhất về."
        elif action == "push":
            origin.push()
            return "Đã đẩy code lên remote thành công."
    except Exception as e: return f"Lỗi sync: {str(e)}"

@mcp.tool()
def git_merge_local(repo_path: str, source_branch: str, target_branch: str) -> str:
    """Merge nhánh source vào nhánh target ở máy local."""
    try:
        repo = Repo(repo_path)
        repo.git.checkout(target_branch)
        result = repo.git.merge(source_branch)
        return f"Kết quả merge: {result}"
    except Exception as e: return f"Lỗi merge: {str(e)}"

# --- NHÓM 3: THAO TÁC CLOUD (PyGithub) ---

@mcp.tool()
def create_remote_repo(name: str, description: str = "", private: bool = True) -> str:
    """Tạo một repository mới trực tiếp trên tài khoản GitHub Cloud của bạn."""
    if not gh_client: return "Chưa cấu hình GITHUB_TOKEN"
    try:
        user = gh_client.get_user()
        repo = user.create_repo(name=name, description=description, private=private)
        return f"Đã tạo Repo Cloud thành công: {repo.html_url}"
    except Exception as e:
        return f"Lỗi tạo Repo Cloud: {str(e)}"

@mcp.tool()
def create_github_pull_request(repo_name: str, title: str, body: str, head: str, base: str = "main") -> str:
    """Tạo một Pull Request (Merge Request) trên GitHub Cloud."""
    if not gh_client: return "Chưa cấu hình GITHUB_TOKEN"
    try:
        repo = gh_client.get_repo(repo_name)
        pr = repo.create_pull(title=title, body=body, head=head, base=base)
        return f"Đã tạo PR thành công: {pr.html_url}"
    except Exception as e: return f"Lỗi tạo PR: {str(e)}"

# --- NHÓM 4: QUẢN LÝ FILE, TRACKING & IGNORE ---

@mcp.tool()
def fix_git_tracking(repo_path: str, file_path: str) -> str:
    """Xóa một file khỏi tracking (git rm --cached) nhưng giữ lại file vật lý."""
    try:
        repo = Repo(repo_path)
        repo.git.rm('--cached', file_path)
        return f"Đã ngừng theo dõi {file_path}. Đừng quên thêm nó vào .gitignore!"
    except Exception as e: return f"Lỗi: {str(e)}"

@mcp.tool()
def get_file_diff(repo_path: str, file_path: str) -> str:
    """Xem các thay đổi chưa commit của một file (git diff)."""
    try:
        repo = Repo(repo_path)
        return repo.git.diff(file_path)
    except Exception as e: return f"Lỗi lấy diff: {str(e)}"

@mcp.tool()
def manage_gitignore(repo_path: str, action: str, pattern: str = "") -> str:
    """Đọc hoặc thêm pattern vào file .gitignore."""
    path = os.path.join(repo_path, ".gitignore")
    try:
        if action == "read":
            if os.path.exists(path):
                with open(path, 'r') as f: return f.read()
            return ".gitignore chưa tồn tại."
        elif action == "add":
            with open(path, 'a') as f:
                f.write(f"\n{pattern}")
            return f"Đã thêm '{pattern}' vào .gitignore"
    except Exception as e: return f"Lỗi: {str(e)}"

@mcp.tool()
def git_add(repo_path: str, file_paths: list[str]) -> str:
    """
    Thêm các file vào staging area (git add).
    file_paths: Danh sách các đường dẫn file cần add.
    """
    try:
        repo = Repo(repo_path)
        # Thực hiện add danh sách file
        repo.index.add(file_paths)
        return f"Đã thực hiện git add cho: {', '.join(file_paths)}"
    except Exception as e:
        logging.error(f"LỖI GIT ADD: {str(e)}")
        return f"Lỗi thực hiện git add: {str(e)}"

@mcp.tool()
def git_commit(repo_path: str, message: str) -> str:
    """
    Tạo một commit mới với nội dung tin nhắn chỉ định (git commit -m).
    """
    try:
        repo = Repo(repo_path)
        # Thực hiện commit các file đã được add vào index
        new_commit = repo.index.commit(message)
        return f"Đã commit thành công với mã: {new_commit.hexsha}\nNội dung: {message}"
    except Exception as e:
        logging.error(f"LỖI GIT COMMIT: {str(e)}")
        return f"Lỗi thực hiện git commit: {str(e)}"

if __name__ == "__main__":
    logging.info("--- SERVER GIT EXPERT KHỞI ĐỘNG (PORT 8002) ---")
    mcp.run(transport="sse")