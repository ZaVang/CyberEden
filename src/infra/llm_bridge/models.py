"""
CyberEden LLM Bridge — Pydantic data models (Google-only, simplified).

这是 Oracle（神谕祭坛）的数据契约层。
所有 LLM 调用的出入参数都必须通过这里的 Schema 定义，绝不允许裸字典越过模块边界。
"""

from __future__ import annotations

from typing import Any, Optional, Type
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Token Usage
# ---------------------------------------------------------------------------

class UsageInfo(BaseModel):
    """归一化的 Token 消耗统计，直接从 Google 的 usage_metadata 映射而来。"""

    input_tokens: int = Field(default=0, description="输入 Prompt 消耗的 Token 数量。")
    output_tokens: int = Field(default=0, description="模型生成的 Token 数量。")
    total_tokens: int = Field(default=0, description="输入 + 输出总 Token 数。")


# ---------------------------------------------------------------------------
# Unified Response
# ---------------------------------------------------------------------------

class UnifiedResponse(BaseModel):
    """
    所有 LLM 调用的统一返回体。

    Oracle Gateway 的调用方（如 Adam Agent 的祈祷 Handler）
    不应关心底层具体调用了哪个 Gemini 模型，只需依赖此 Schema。
    """

    model: str = Field(description="实际响应的模型名称，例如 'gemini-2.0-flash'。")
    content: Optional[str] = Field(default=None, description="模型返回的原始文本响应。")
    parsed: Optional[Any] = Field(
        default=None,
        description="当传入了 response_model 时，返回解析后的 Pydantic 实例。"
    )
    usage: UsageInfo = Field(
        default_factory=UsageInfo,
        description="本次调用的 Token 消耗统计。"
    )
    stop_reason: Optional[str] = Field(
        default=None,
        description="模型停止生成的原因，例如 'STOP' / 'MAX_TOKENS' / 'SAFETY'。"
    )


# ---------------------------------------------------------------------------
# Chat Parameters
# ---------------------------------------------------------------------------

class ChatParameters(BaseModel):
    """发起 LLM 对话时可传入的可选参数。"""

    max_tokens: Optional[int] = Field(default=8192, description="最大输出 Token 数。")
    temperature: Optional[float] = Field(default=0.7, description="采样温度，0.0 为确定性最高。")
    system_prompt: Optional[str] = Field(default=None, description="系统级指令，会被注入为 system_instruction。")
    response_model: Optional[Type[BaseModel]] = Field(
        default=None,
        description="如果提供，将要求模型以 JSON 格式返回，并自动 parse 为该 Pydantic 类型。"
    )

    model_config = {"arbitrary_types_allowed": True}


# ---------------------------------------------------------------------------
# Retry Configuration
# ---------------------------------------------------------------------------

class RetryConfig(BaseModel):
    """指数退避重试策略配置。"""

    max_retries: int = Field(default=5, description="最大重试次数，超过后抛出异常，不可静默吞下。")
    base_delay: float = Field(default=2.0, description="第一次重试前的等待基础秒数。")
    max_delay: float = Field(default=120.0, description="单次等待时间上限（秒），防止超长等待。")
    exponential_base: float = Field(default=2.0, description="每次重试后延迟的指数增长倍率。")


# ---------------------------------------------------------------------------
# Bridge Configuration  (loaded from env / inline)
# ---------------------------------------------------------------------------

class BridgeConfig(BaseModel):
    """Oracle LLM Bridge 的全局配置。"""

    model: str = Field(
        default="gemini-3.1-flash-lite-preview",
        description="默认使用的 Gemini 模型名称。"
    )
    retry: RetryConfig = Field(
        default_factory=RetryConfig,
        description="重试策略配置。"
    )
    log_usage: bool = Field(default=True, description="是否在每次对话后记录 Token 使用日志。")
