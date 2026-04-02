import datetime
import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from src.schemas.eden import PrayerRequest, RevelationResponse, ActionPlan
from src.infra.llm_bridge import LLMBridge
from src.infra.llm_bridge.models import ChatParameters

logger = logging.getLogger("oracle")
logging.basicConfig(level=logging.INFO)

# ── 轮次日志配置 ──────────────────────────────────────────────────────────
# 日志目录通过环境变量配置，默认写到 CyberEden 项目根目录下的 logs/
_LOG_DIR = Path(os.environ.get("ORACLE_LOG_DIR", Path(__file__).parents[3] / "logs"))
_LOG_DIR.mkdir(parents=True, exist_ok=True)
TURN_LOG_PATH = _LOG_DIR / "oracle_turns.jsonl"

logger.info("Oracle 轮次日志路径: %s", TURN_LOG_PATH)


def _append_turn_log(record: dict) -> None:
    """将一轮完整记录以 JSON Lines 格式追加到 oracle_turns.jsonl。"""
    try:
        with open(TURN_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning("写入 oracle_turns.jsonl 失败: %s", e)


# ── FastAPI App ───────────────────────────────────────────────────────────

bridge: LLMBridge = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bridge
    bridge = LLMBridge.from_env()
    yield


app = FastAPI(title="Oracle Gateway", lifespan=lifespan)


@app.post("/ask_god", response_model=RevelationResponse)
async def ask_god(prayer: PrayerRequest) -> RevelationResponse:
    """
    接收 Adam 的多轮祷告历史，向 Gemini 发起调用并返回结构化行动计划。
    每轮完整的 request + response 记录到 logs/oracle_turns.jsonl。
    """
    turn_record: dict = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "messages_count": len(prayer.messages),
        "system_prompt_chars": len(prayer.system_prompt or ""),
        "request": {
            "system_prompt": prayer.system_prompt,
            "messages": [m.model_dump() for m in prayer.messages],
        },
        "response": None,
        "usage": None,
        "stop_reason": None,
        "error": None,
    }

    try:
        logger.info(
            "Oracle 收到祷告，共 %d 条消息记录，正在调用 LLMBridge…",
            len(prayer.messages),
        )

        messages = [{"role": m.role, "content": m.content} for m in prayer.messages]
        params = ChatParameters(response_model=ActionPlan)

        response = await bridge.chat(
            messages=messages,
            params=params,
            system_prompt=prayer.system_prompt,
        )

        # 记录 token 用量和停止原因
        turn_record["usage"] = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.total_tokens,
        }
        turn_record["stop_reason"] = response.stop_reason

        if response.parsed:
            revelation_dict = response.parsed.model_dump()
            turn_record["response"] = revelation_dict
            _append_turn_log(turn_record)

            logger.info(
                "Oracle 成功解析神谕 | input=%d output=%d | thoughts: %s",
                response.usage.input_tokens,
                response.usage.output_tokens,
                response.parsed.thoughts,
            )
            return RevelationResponse(revelation=response.parsed)

        # 截断处理
        if response.stop_reason == "MAX_TOKENS":
            error_msg = "【神谕截断】你的话太多了（Token 溢出），请在下一次祷告中保持精简。"
            logger.warning("Oracle truncation: %s", error_msg)
            turn_record["error"] = f"MAX_TOKENS: {error_msg}"
            _append_turn_log(turn_record)
            raise HTTPException(status_code=413, detail=error_msg)

        error_msg = "神谕解析失败：LLM 返回了无效的结构化数据。"
        raw_preview = (response.content or "")[:200]
        logger.error("Oracle parse error | raw: %s", raw_preview)
        turn_record["error"] = f"parse_failed: {raw_preview}"
        _append_turn_log(turn_record)
        raise HTTPException(status_code=500, detail=error_msg)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Oracle 异常: %s", e, exc_info=True)
        turn_record["error"] = str(e)
        _append_turn_log(turn_record)
        raise HTTPException(status_code=500, detail=str(e))
