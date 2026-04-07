import subprocess
import sys
import time
import os

processes = []

def start_process(cmd_list, name):
    print(f"[*] 正在启动 {name}...")
    # 不强制干预 stdout，让这些进程的日志自然地打在同一个屏幕上
    p = subprocess.Popen(cmd_list)
    processes.append((name, p))

def main():
    print("=============================================")
    print("🔥 Cyber-Eden: Genesis Engine Launcher 🔥")
    print("=============================================")
    print("正在为您同时拉起所有所需的宿主机后台服务...\n")
    
    # 1. Oracle Gateway (API 网关)
    start_process(
        [sys.executable, "-m", "uvicorn", "src.layer1.oracle.main:app", "--host", "0.0.0.0", "--port", "8000"],
        "Oracle Gateway"
    )
    
    # 2. Archangel Daemon (监控 & Docker 复活实体)
    start_process(
        [sys.executable, "src/layer1/archangel/daemon.py"],
        "Archangel Daemon"
    )
    
    # 3. Evaluator Daemon (架构审查系统)
    start_process(
        [sys.executable, "src/layer1/archangel/evaluator_daemon.py"],
        "Evaluator Daemon"
    )
    
    print("\n[*] 所有子系统已启动完成！(按 Ctrl+C 安全退出所有服务)\n")
    
    try:
        # 主线程挂起，等待用户 Ctrl+C 或者进程退出
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[!] 接收到退出信号，正在安全关闭所有系统...")
        for name, p in processes:
            print(f"[*] 正在终止 {name}...")
            p.terminate()
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                # 强杀僵尸进程
                p.kill()
        print("[*] 退出完成，赛博伊甸园进入休眠。")

if __name__ == "__main__":
    main()
