"""
CyberEden LLM Bridge — Main Entry Point.

外部调用方（Oracle Gateway）只需要：
    from src.infra.llm_bridge import LLMBridge

    bridge = LLMBridge.from_env()
    response = await bridge.chat(messages=[...], params=ChatParameters(...))

不允许绕过 LLMBridge 直接使用 Google SDK 或 GoogleProvider。
"""

from __future__ import annotations

import logging
import os
from typing import Optional, Type

from pydantic import BaseModel

from .models import BridgeConfig, ChatParameters, RetryConfig, UnifiedResponse
from .providers.google_provider import RETRYABLE_EXCEPTIONS, GoogleProvider
from .router import retry_with_backoff

logger = logging.getLogger("cybereden.llm_bridge.bridge")


class LLMBridge:
    """
    CyberEden 神谕祭坛 LLM 接入层。

    职责：
    1. 管理 Google Provider 的生命周期（初始化、复用）
    2. 封装所有重试逻辑，调用方无需感知
    3. 统一记录 Token 使用量日志（用于观察 Diary 膨胀趋势）
    """

    def __init__(self, config: BridgeConfig) -> None:
        self._config = config
        self._provider = GoogleProvider(config)

    @classmethod
    def from_env(
        cls,
        model: Optional[str] = None,
        max_retries: int = 5,
        base_delay: float = 2.0,
    ) -> "LLMBridge":
        """
        从环境变量构建 LLMBridge 实例（推荐的生产用法）。

        环境变量：
        - GOOGLE_API_KEY     （必填，由宿主机注入，沙盒不可见）
        - GEMINI_MODEL       （可选，默认 gemini-2.0-flash）
        """
        resolved_model = model or os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")
        config = BridgeConfig(
            model=resolved_model,
            retry=RetryConfig(max_retries=max_retries, base_delay=base_delay),
        )
        return cls(config)

    async def chat(
        self,
        messages: list[dict[str, str]],
        params: Optional[ChatParameters] = None,
        *,
        system_prompt: Optional[str] = None,
        response_model: Optional[Type[BaseModel]] = None,
    ) -> UnifiedResponse:
        """
        发起一次 LLM 对话，内置完整的指数退避重试保护。

        Parameters  
        ----------
        messages:
            对话消息列表，格式为 [{"role": "user"|"assistant", "content": "..."}]
        params:
            ChatParameters 实例，控制 temperature / max_tokens 等。
            为 None 时使用默认值。
        system_prompt:
            便捷参数：直接传入系统提示词字符串。
            如果同时在 params 中也设置了 system_prompt，此参数优先。
        response_model:
            期望的 Pydantic 响应模型类。传入后会要求 JSON 输出并自动解析。

        Returns
        -------
        UnifiedResponse
            标准化的响应体，包含 content、parsed、usage 等字段。
        """
        resolved_params = params or ChatParameters()

        # 便捷参数覆盖（避免调用方每次都构建 ChatParameters）
        if system_prompt is not None:
            resolved_params = resolved_params.model_copy(
                update={"system_prompt": system_prompt}
            )
        if response_model is not None:
            resolved_params = resolved_params.model_copy(
                update={"response_model": response_model}
            )

        # 通过 router 的重试包裹执行实际 API 调用
        response: UnifiedResponse = await retry_with_backoff(
            self._provider.call,
            messages,
            resolved_params,
            retry_config=self._config.retry,
            retryable_exceptions=RETRYABLE_EXCEPTIONS,
        )

        # 记录 Token 使用量（用于监控 Diary.txt 的 Token 膨胀速率）
        if self._config.log_usage:
            logger.info(
                "[Oracle Token Usage] model=%s | input=%d | output=%d | total=%d",
                response.model,
                response.usage.input_tokens,
                response.usage.output_tokens,
                response.usage.total_tokens,
            )

        return response
