"""
CyberEden LLM Bridge — Google Gemini Provider.

这是唯一允许直接 import google.genai 的模块。
业务层（Oracle Gateway / Adam Agent）绝不应绕过此模块直接调用 SDK。

依赖: google-genai>=1.0  (google.genai，不是已废弃的 google.generativeai)
"""

from __future__ import annotations

import json
import logging
import os
import httpx
from typing import Any, Optional, Type

from google import genai
from google.genai import types as genai_types
from pydantic import BaseModel

from ..models import BridgeConfig, ChatParameters, UnifiedResponse, UsageInfo

logger = logging.getLogger("cybereden.llm_bridge.google")


def _build_retryable_exceptions() -> tuple[type[BaseException], ...]:
    """
    构建 Google API 中值得重试的异常类型元组。
    网络超时、速率限制、服务暂时不可用均应重试；认证失败和参数错误则不应重试。
    """
    try:
        from google.api_core import exceptions as gax_exc
        return (
            gax_exc.ServiceUnavailable,
            gax_exc.ResourceExhausted,   # 429 Rate Limit
            gax_exc.DeadlineExceeded,    # 请求超时
            gax_exc.InternalServerError, # 5xx
            httpx.HTTPError,             # 包括所有的 httpx 错误
            httpx.RemoteProtocolError,   # 特别针对协议中断
            ConnectionError,
            TimeoutError,
        )
    except ImportError:
        # 如果 google-api-core 还没安装，回退到通用异常
        logger.warning("google-api-core 未安装，将对所有 Exception 进行重试。")
        return (Exception,)


RETRYABLE_EXCEPTIONS = _build_retryable_exceptions()


class GoogleProvider:
    """
    封装 Google Gemini API 调用。

    所有调用都通过 `LLMBridge.chat()` 进来，不对外暴露。
    """

    def __init__(self, config: BridgeConfig) -> None:
        self._config = config
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "[Oracle] 未找到环境变量 GOOGLE_API_KEY。"
                "请在宿主机 .env 或启动环境中设置，不可硬编码。"
            )
        self._client = genai.Client(api_key=api_key)
        logger.info("[Oracle] Google Provider 初始化完成，使用模型: %s", config.model)

    async def call(
        self,
        messages: list[dict[str, str]],
        params: ChatParameters,
    ) -> UnifiedResponse:
        """
        执行单次（无重试）的 Gemini API 对话调用。
        重试逻辑由外层的 `router.retry_with_backoff` 管理。

        Parameters
        ----------
        messages:
            标准 OpenAI 格式的消息列表：[{"role": "user", "content": "..."}]
        params:
            本次调用的生成参数。
        """
        # 转换消息格式为 google-genai SDK 所需的 Content 列表
        contents = self._convert_messages(messages)

        # 构建 GenerateContentConfig
        generation_config = genai_types.GenerateContentConfig(
            max_output_tokens=params.max_tokens,
            temperature=params.temperature,
            system_instruction=params.system_prompt,
        )

        # 如果需要结构化输出，则强制要求 JSON 并注入 Schema
        if params.response_model is not None:
            generation_config.response_mime_type = "application/json"
            generation_config.response_schema = params.response_model

        response = await self._client.aio.models.generate_content(
            model=self._config.model,
            contents=contents,
            config=generation_config,
        )

        return self._parse_response(response, params.response_model)

    def _convert_messages(
        self, messages: list[dict[str, str]]
    ) -> list[genai_types.Content]:
        """将标准消息列表转换为 google-genai Content 格式。"""
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            content_text = msg.get("content", "")
            # Google SDK 的角色只有 'user' 和 'model'，system 由 system_instruction 处理
            google_role = "model" if role == "assistant" else "user"
            contents.append(
                genai_types.Content(
                    role=google_role,
                    parts=[genai_types.Part(text=content_text)],
                )
            )
        return contents

    def _parse_response(
        self,
        response: Any,
        response_model: Optional[Type[BaseModel]],
    ) -> UnifiedResponse:
        """将 Google API 原始响应解析为 UnifiedResponse。"""
        # 安全获取文本内容：避免在安全过滤触发时调用 .text 报错
        raw_text = ""
        try:
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                raw_text = response.candidates[0].content.parts[0].text or ""
        except (AttributeError, IndexError) as e:
            logger.warning("[Oracle] 无法从响应中提取文本内容: %s", e)

        # 解析结构化输出
        parsed = None
        if response_model is not None and raw_text:
            try:
                parsed = response_model.model_validate_json(raw_text)
            except Exception as e:
                logger.warning("[Oracle] 结构化输出解析失败: %s，原始文本: %s", e, raw_text[:200])

        # 提取 Token 使用量
        usage_meta = getattr(response, "usage_metadata", None)
        usage = UsageInfo(
            input_tokens=getattr(usage_meta, "prompt_token_count", 0) or 0,
            output_tokens=getattr(usage_meta, "candidates_token_count", 0) or 0,
            total_tokens=getattr(usage_meta, "total_token_count", 0) or 0,
        )

        # 提取停止原因
        stop_reason = "UNKNOWN"
        if response.candidates:
            stop_reason = str(response.candidates[0].finish_reason)
        
        if stop_reason == "SAFETY":
            logger.error("[Oracle] 响应被安全过滤器拦截！请检查 Prompt 是否包含敏感内容。")
            raw_text = raw_text or "（内容因安全策略被拦截）"

        return UnifiedResponse(
            model=self._config.model,
            content=raw_text,
            parsed=parsed,
            usage=usage,
            stop_reason=stop_reason,
        )
