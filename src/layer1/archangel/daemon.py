import asyncio
import logging
import subprocess
import os
import docker
from docker.errors import DockerException, ContainerError, ImageNotFound
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger("archangel")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] ARCHANGEL - %(message)s")

class ArchangelDaemon:
    def __init__(self, adam_repo_path: str):
        self.adam_repo_path = os.path.abspath(adam_repo_path)
        try:
            self.client = docker.from_env()
        except DockerException as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            raise

    def get_git_status(self) -> bool:
        """Check if there are modified/untracked files in the Adam repo."""
        res = subprocess.run(["git", "status", "--porcelain"], cwd=self.adam_repo_path, capture_output=True, text=True)
        return bool(res.stdout.strip())

    def git_commit_snapshot(self):
        """Commit the current state of Adam Eden as an evolutionary snapshot."""
        subprocess.run(["git", "add", "-A"], cwd=self.adam_repo_path)
        subprocess.run(["git", "commit", "-m", "Evolution Snapshot"], cwd=self.adam_repo_path)
        logger.info("Committed new evolution snapshot.")
        self.git_push()

    def git_push(self):
        """Push snapshots to remote if configured (asynchronous/non-blocking ideally, but simple for now)."""
        res = subprocess.run(["git", "remote"], cwd=self.adam_repo_path, capture_output=True, text=True)
        if res.stdout.strip():
            logger.info("Pushing evolution snapshot to remote...")
            subprocess.run(["git", "push"], cwd=self.adam_repo_path)
        else:
            logger.debug("No git remote found, skipping push.")

    def git_rollback(self):
        """Rollback to the last known good snapshot (HEAD)."""
        subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=self.adam_repo_path)
        subprocess.run(["git", "clean", "-fd"], cwd=self.adam_repo_path)
        logger.warning("Rolled back AdamEden to previous cycle safely.")

    def write_nightmare(self, log_content: str):
        """Record the death logs for Adam's next incarnation."""
        error_path = os.path.join(self.adam_repo_path, "data", "error.log")
        os.makedirs(os.path.dirname(error_path), exist_ok=True)
        with open(error_path, "w", encoding="utf-8") as f:
            f.write("【Archangel Death Report】\nYou crashed in the last epoch. Here is the stack trace:\n\n")
            f.write(log_content)
            
    async def reincarnate_adam(self):
        """Run the docker container asynchronously and monitor its heartbeat."""
        import time
        logger.info("Reincarnating Adam in docker sandbox (Watchdog Mode)...")
        container_name = "adam_instance"
        
        # Cleanup
        try:
            old_container = self.client.containers.get(container_name)
            old_container.remove(force=True)
        except docker.errors.NotFound:
            pass

        # Build image lazily
        try:
            self.client.images.get("adam_base")
        except ImageNotFound:
            logger.info("Building adam_base Docker image from scratch. This may take a minute...")
            self.client.images.build(path=self.adam_repo_path, tag="adam_base")

        # Initialize heartbeat
        heartbeat_file = os.path.join(self.adam_repo_path, "data", "heartbeat.txt")
        os.makedirs(os.path.dirname(heartbeat_file), exist_ok=True)
        with open(heartbeat_file, 'w', encoding='utf-8') as f:
            f.write(str(time.time()))

        try:
            # 采用分离模式并在后台定期检查状态
            container = self.client.containers.run(
                "adam_base",
                command="sh -c 'pip install --quiet --default-timeout=100 -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt ; python main.py'",
                name=container_name,
                volumes={
                    self.adam_repo_path: {'bind': '/app', 'mode': 'rw'},
                },
                extra_hosts={"host.docker.internal": "host-gateway"},
                network_mode="bridge",
                detach=True
            )
            
            while True:
                container.reload()
                if container.status == "exited":
                    exit_code = container.attrs['State']['ExitCode']
                    logs = container.logs().decode("utf-8", errors="replace")
                    container.remove()
                    return exit_code == 0, logs

                # Heartbeat watchdog check (180s threshold)
                try:
                    if os.path.exists(heartbeat_file):
                        mtime = os.path.getmtime(heartbeat_file)
                        if time.time() - mtime > 180:
                            logs = container.logs().decode("utf-8", errors="replace")
                            logs += "\n\n[SYSTEM CRITICAL] ARCHANGEL DETECTED VEGETATIVE STATE (No heartbeat for 180s).\n[SYSTEM CRITICAL] FORCING CONTAINER SHUTDOWN AND ROLLBACK."
                            container.stop(timeout=2)
                            container.remove(force=True)
                            return False, logs
                except Exception as e:
                    logger.debug(f"Heartbeat check error: {e}")
                
                await asyncio.sleep(5)

        except ContainerError as e:
            logs = e.container.logs()
            try:
                logs_str = logs.decode("utf-8", errors="replace")
            except Exception:
                logs_str = str(logs)
            return False, logs_str

    async def watch_over_eden(self):
        logger.info(f"Archangel guarding {self.adam_repo_path}")
        if not os.path.exists(os.path.join(self.adam_repo_path, ".git")):
            subprocess.run(["git", "init"], cwd=self.adam_repo_path)
            subprocess.run(["git", "add", "-A"], cwd=self.adam_repo_path)
            subprocess.run(["git", "commit", "-m", "Genesis"], cwd=self.adam_repo_path)

        while True:
            try:
                success, logs = await self.reincarnate_adam()
                
                # 无论成功还是失败，都打印容器内部的关键日志，方便调试
                if logs.strip():
                    logger.info("--- Adam's Logs Start ---")
                    for line in logs.strip().splitlines()[-20:]: # 只显示最后20行
                        logger.info(f"  [Adam] {line}")
                    logger.info("--- Adam's Logs End ---")

                if not success:
                    logger.error("Adam has DIED (Container Crash). Preparing resurrect protocol.")
                    self.git_rollback()
                    self.write_nightmare(logs)
                else:
                    if self.get_git_status():
                        logger.info("Adam mutated himself and exited for reincarnation. Snapshoting...")
                        
                        # Check if requirements.txt was changed to decide on image rebuild
                        res = subprocess.run(["git", "diff", "--name-only", "requirements.txt"], cwd=self.adam_repo_path, capture_output=True, text=True)
                        req_changed = "requirements.txt" in res.stdout
                        
                        self.git_commit_snapshot()
                        self.write_nightmare("（当前身体非常健康，无可报告的错误日志）")
                        
                        if req_changed:
                            logger.info("Detected changes in requirements.txt. Rebuilding adam_base image...")
                            self.client.images.build(path=self.adam_repo_path, tag="adam_base")
                    else:
                        logger.info("Adam session ended peacefully without mutation. (Possible manual shutdown or logic error)")
                        # 如果 requirements.txt 当前内容与镜像不同，也需要重建
                        # 这处不需要，因为 command 里已经包含了 startup pip install
                
            except Exception as e:
                logger.error(f"Archangel internal error: {e}", exc_info=True)
                
            logger.info("Epoch complete. Rest for 5s before next reincarnation...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    # 强制优先从 .env 获取 ADAM_REPO_PATH
    adam_repo = os.getenv("ADAM_REPO_PATH")
    if not adam_repo:
        logger.error("ADAM_REPO_PATH not found in .env! Please run setup_eden.py or create .env.")
        exit(1)
    
    daemon = ArchangelDaemon(adam_repo)
    asyncio.run(daemon.watch_over_eden())
