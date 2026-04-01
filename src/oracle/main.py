from fastapi import FastAPI
from src.schemas.eden import PrayerRequest, RevelationResponse

app = FastAPI(title="Oracle Proxy - 神谕祭坛")

@app.post("/ask_god", response_model=RevelationResponse)
async def ask_god(prayer: PrayerRequest) -> RevelationResponse:
    """
    接收来自伊甸园沙盒内 Adam 的祈祷，过滤并转发给外侧真实的 LLM。
    """
    # TODO: 
    # 1. 组装 System Prompt (从 src/prompts/oracle_system.j2 加载)
    # 2. 调用外层的 LLMBridge (隔离实际的 api key 逻辑)
    # 3. 将 LLM 返回的结构体解析为 RevelationResponse 并验证返回给沙盒
    raise NotImplementedError("Oracle API Gateway structure instantiated, not yet implemented.")
