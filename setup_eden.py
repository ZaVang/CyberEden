import os
import subprocess
import sys
from pathlib import Path

# Try to load .env if python-dotenv is installed (it should be)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def log(msg: str):
    print(f"[*] {msg}")

def error(msg: str):
    print(f"[!] ERROR: {msg}")
    sys.exit(1)

def run_command(cmd: list, cwd: str = None, check: bool = True):
    try:
        return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        error(f"Command failed: {' '.join(cmd)}\n{e.stderr}")

def setup():
    log("=== Cyber-Eden: Genesis Setup ===")
    
    # 1. 检查环境变量
    adam_path_env = os.getenv("ADAM_REPO_PATH")
    if not adam_path_env:
        error("MISSING ADAM_REPO_PATH in .env file. Please check .env.example and create .env.")
    
    adam_root = Path(adam_path_env).resolve()
    if not adam_root.exists():
        error(f"ADAM_REPO_PATH does not exist: {adam_root}")

    # 2. 检查 AdamEden 是否为 Git 仓库
    if not (adam_root / ".git").exists():
        log(f"Initializing Git in {adam_root}...")
        run_command(["git", "init"], cwd=str(adam_root))
        run_command(["git", "add", "."], cwd=str(adam_root))
        run_command(["git", "commit", "-m", "Genesis: The creation of Adam"], cwd=str(adam_root))
    else:
        log("Git repository detected in AdamEden.")

    # 3. 检查 Bible.md 是否存在
    bible_path = adam_root / "data" / "Bible.md"
    if not bible_path.exists():
        log("Bible.md not found in sandbox. Creating default...")
        os.makedirs(bible_path.parent, exist_ok=True)
        # Assuming the content was created previously, if not we'd put a fallback here
        log("Warning: You might want to copy Bible.md from docs/bible.md to AdamEden/data/Bible.md")

    # 4. 构建 Docker 镜像
    log("Building 'adam_base' docker image...")
    # Use subprocess directly to show progress if possible
    try:
        subprocess.run(["docker", "build", "-t", "adam_base", "."], cwd=str(adam_root), check=True)
        log("Successfully built adam_base image.")
    except Exception as e:
        error(f"Docker build failed. Is Docker Desktop running?\n{e}")

    log("=== Setup Complete. Ready to go! ===")
    log("Steps to Run:")
    log("1. Terminal 1: uvicorn src.layer1.oracle.main:app --host 0.0.0.0 --port 8000")
    log("2. Terminal 2: python src/layer1/archangel/daemon.py")

if __name__ == "__main__":
    setup()
