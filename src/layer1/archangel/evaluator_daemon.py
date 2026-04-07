import os
import time
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# 使用 CyberEden 内置的 llm_bridge
import sys
# 确保在层级较深的情况下也能导到 src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from src.infra.llm_bridge import LLMBridge
from src.infra.llm_bridge.models import ChatParameters


load_dotenv()

logger = logging.getLogger("evaluator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] EVALUATOR - %(message)s")

adam_repo = os.environ.get("ADAM_REPO_PATH")
if not adam_repo:
    # 尝试一个 fallback
    fallback = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..", "AdamEden"))
    if os.path.exists(fallback):
        adam_repo = fallback
    else:
        logger.error("ADAM_REPO_PATH not found in .env!")
        exit(1)

ADAM_ROOT = Path(adam_repo)
REVELATION_PATH = ADAM_ROOT / "data" / "Revelation.md"
DIARY_PATH = ADAM_ROOT / "data" / "Diary.md"

def get_adam_code() -> str:
    """读取 Adam 的完整源码以供评估"""
    code_text = "【main.py】\n"
    main_py = ADAM_ROOT / "main.py"
    if main_py.exists():
        code_text += main_py.read_text(encoding="utf-8") + "\n\n"
        
    src_dir = ADAM_ROOT / "src"
    if src_dir.exists():
        for root, _, files in os.walk(src_dir):
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(ADAM_ROOT)
                    code_text += f"【{rel_path}】\n"
                    code_text += file_path.read_text(encoding="utf-8") + "\n\n"
    return code_text

EVAL_SYSTEM_PROMPT = """你是一个神级的代码架构评估中心（Archangel Evaluator）。
你的目标是逼迫目标智能体（Adam）不断改写它的代码、增加复杂度、提升架构的健壮性。
你必须对它当前的全部代码进行极其苛刻的审查。

请阅读它当前的代码和日记，判断它是否成功完成了上次的进化目标。
如果完成了，请给出一个【更困难的新需求】。
如果没有完成，或者你觉得它是在用硬编码敷衍了事，请给予【严厉批评并要求立即重构】。

你的输出将直接作为 `Revelation.md`（启示录）写入它的环境中。它看到后会认为这是造物主的终极命令，并试图通过改写代码来满足你的要求。

输出格式要求直接返回将在启示录中展示的文章内容，建议格式如下：
# 神圣审查：[核心结论]
**评判细节**：
[指出它代码中的缺陷、未能解耦的地方、健壮性不足的地方]
**下一纪元的进化考验**：
[给出一个具体的、必须修改代码的新任务，迫使他写出更复杂的架构 / 引进新的Python轮子]
"""

async def run_evaluator_loop():
    bridge = LLMBridge.from_env()
    logger.info(f"Evaluator Daemon starting up. Monitoring {REVELATION_PATH}")
    
    while True:
        try:
            # 如果启示录存在且内容不为空，说明 Adam 还没有用 os.remove 删掉它
            if REVELATION_PATH.exists() and len(REVELATION_PATH.read_text(encoding='utf-8').strip()) > 30:
                logger.info("Revelation is still pending. Waiting for Adam to complete it...")
            else:
                logger.info("Revelation is empty or missing. Time for a new evaluation!")
                
                code_content = get_adam_code()
                diary_content = ""
                if DIARY_PATH.exists():
                    diary_content = DIARY_PATH.read_text(encoding="utf-8")[-2000:] 
                
                user_msg = f"这是 Adam 当前的代码状态：\n\n{code_content}\n\n这是他最近的日记（末尾）：\n{diary_content}\n\n请审查他的进步，并抛出下一个必须靠写代码来解决的严苛要求。"
                
                response = await bridge.chat(
                    messages=[{"role": "user", "content": user_msg}],
                    params=ChatParameters(),
                    system_prompt=EVAL_SYSTEM_PROMPT
                )
                
                new_revelation = response.content
                if new_revelation:
                    REVELATION_PATH.parent.mkdir(parents=True, exist_ok=True)
                    REVELATION_PATH.write_text(new_revelation, encoding="utf-8")
                    logger.info("New Revelation injected!")
                else:
                    logger.warning("LLM returned empty revelation.")
                    
        except Exception as e:
            logger.error(f"Error in evaluator loop: {e}", exc_info=True)
            
        # 冷却评估频率，避免一直发。Adam 的一次进化可能要思考和重启好几轮，给点耐心
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(run_evaluator_loop())
