import sys
import os

# 使用当前脚本所在目录往上一层或直接硬编码
# 基于CyberEden与AdamEden同级目录的架构假设
ADAM_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "AdamEden", "data")
REVELATION_PATH = os.path.join(ADAM_DATA_DIR, "Revelation.md")

def inject_revelation(content: str):
    print(f"[*] 正在向亚当降下神谕...")
    
    if not os.path.exists(ADAM_DATA_DIR):
        print(f"[!] 找不到目标文件夹: {ADAM_DATA_DIR}")
        print("[!] 请检查你的目录结构是否为 d:\\work\\AdamEden\\data")
        sys.exit(1)

    # 如果有历史存在，最好覆盖或者清楚的追加
    mode = "a" if os.path.exists(REVELATION_PATH) else "w"
    
    with open(REVELATION_PATH, mode, encoding="utf-8") as f:
        if mode == "a":
            f.write(f"\n\n## 新神谕\n\n{content}")
        else:
            f.write(content)
            
    print(f"[*] 神谕写入完毕 -> {REVELATION_PATH}")
    print("[*] 亚当在下一次循环或者系统突变时，将探测到并且被迫处理这个指令。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("=======================")
        print(" 用法: python inject_revelation.py \"你的具体指令...\"")
        print(" 示例: python inject_revelation.py \"你的 Web 服务没有实现 HTTPS，赶紧去配一个\"")
        print("=======================")
        sys.exit(1)
    
    task = sys.argv[1]
    inject_revelation(task)
