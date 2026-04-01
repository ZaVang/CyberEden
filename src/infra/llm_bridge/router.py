"""
CyberEden LLM Bridge — Retry & Backoff Router (Google-specific).

这是系统的"永不中断"保证层。
无论 Google API 遭遇 429 / 503 / 网络抖动，这里的指数退避机制保证
Oracle 不会因为单次 API 失败而让整个 Archangel 的轮询死循环中断。

设计原则：
- ±25% 随机抖动（Jitter）防止 Thundering Herd 效应（多次重启同时轰炸 API）
- 只有 max_retries 全部耗尽后才最终 raise，此时由上层记录进 error.log
- 使用 logging 而非 print（符合项目规范）
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, Callable, Coroutine

from .models import RetryConfig

logger = logging.getLogger("cybereden.llm_bridge.router")

# 哪些 Google SDK 异常类型值得重试（其余直接 raise 给上层）
# 实际引入时会在 bridge.py 中注入真实的 google.api_core.exceptions 类型
_DEFAULT_RETRYABLE: tuple[type[BaseException], ...] = (Exception,)


async def retry_with_backoff(
    fn: Callable[..., Coroutine[Any, Any, Any]],
    *args: Any,
    retry_config: RetryConfig | None = None,
    retryable_exceptions: tuple[type[BaseException], ...] = _DEFAULT_RETRYABLE,
    **kwargs: Any,
) -> Any:
    """
    对异步函数 `fn` 执行带指数退避的重试。

    Parameters
    ----------
    fn:
        需要包裹的 async 函数（例如 google_provider.call）。
    retry_config:
        重试策略；为 None 时使用 RetryConfig 的默认值。
    retryable_exceptions:
        哪些异常类型触发重试（其余异常直接透传给上层 caller）。

    Returns
    -------
    fn 调用成功时的返回值。

    Raises
    ------
    RuntimeError
        所有 max_retries 次均失败后抛出，携带最后一次的原始异常。
    """
    cfg = retry_config or RetryConfig()
    last_error: BaseException | None = None

    for attempt in range(1, cfg.max_retries + 1):
        try:
            return await fn(*args, **kwargs)
        except retryable_exceptions as exc:
            last_error = exc

            # 最后一次尝试不再等待，直接跳出循环去 raise
            if attempt == cfg.max_retries:
                break

            # 指数退避 + ±25% 随机 Jitter
            base_delay = cfg.base_delay * (cfg.exponential_base ** (attempt - 1))
            capped_delay = min(base_delay, cfg.max_delay)
            jitter = capped_delay * 0.25 * (2 * random.random() - 1)
            sleep_time = max(0.0, capped_delay + jitter)

            logger.warning(
                "[Oracle Retry] 第 %d/%d 次失败 (%s: %s)。%.2fs 后重试 …",
                attempt,
                cfg.max_retries,
                type(exc).__name__,
                exc,
                sleep_time,
            )
            await asyncio.sleep(sleep_time)

    # 所有重试均耗尽，向上抛出——由 Archangel 或 Oracle 的边界 try/except 捕获并写入 error.log
    raise RuntimeError(
        f"[Oracle] Google LLM 调用在 {cfg.max_retries} 次重试后全部失败。"
        f"最后一次错误: {type(last_error).__name__}: {last_error}"
    ) from last_error
