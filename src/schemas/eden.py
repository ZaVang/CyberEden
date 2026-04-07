from typing import Optional, List
from pydantic import BaseModel, Field


class Message(BaseModel):
    """单条对话消息，兼容 OpenAI 格式。"""
    role: str = Field(..., description="消息角色：'user' 或 'assistant'")
    content: str = Field(..., description="消息内容")


class PrayerRequest(BaseModel):
    """
    Adam 向 Oracle 发送的祷告请求。

    支持多轮对话：传入完整的 messages 历史列表。
    Gateway 会将其直接透传给 LLMBridge，由底层 Gemini API 维护对话上下文。
    """
    messages: List[Message] = Field(
        ...,
        description="对话历史列表，role 为 'user' 或 'assistant'，最后一条必须是 user。",
    )
    system_prompt: Optional[str] = Field(
        None,
        description="可选的系统级指令，将作为 system_instruction 注入。",
    )


class ActionPlan(BaseModel):
    """
    Adam 每轮祷告的行动计划。

    渐进披露原则：
    - thoughts  ：必填，但应简洁（1-3句话即可）。
    - diary_entry：可选，仅在有重要发现时才填写。
    - shell_commands：可选，用来主动探索（cat/ls）或执行任务。
    - new_code   ：严格可选，默认 null。只有在确认要修改 main.py 时才填入完整代码。
    - sleep_seconds：可选，控制下轮等待时长，默认 10 秒。
    """

    thoughts: str = Field(
        ...,
        description=(
            "当前处境的简短观察与下一步意图。"
            "必须填写，但请保持简洁（1-3句话）。禁止长篇大论。"
        ),
    )
    diary_entry: Optional[str] = Field(
        None,
        description=(
            "要追加到 data/Diary.md 的记忆片段。"
            "⚠️绝对禁止记录阅读步骤或无效信息（如'我读了X文件'）。只有在架构重构、完成神谕或做出重大决策时才写入，并保持格式精简专业。否则置为 null。"
        ),
    )
    shell_commands: List[str] = Field(
        default_factory=list,
        description=(
            "要在沙盒终端执行的 Linux 命令列表。"
            "需要读取日记/肉身代码/文件结构时，用 cat/ls 命令按需获取，"
            "结果将在下一轮 prompt 中呈现。"
        ),
    )
    new_code: Optional[str] = Field(
        None,
        description=(
            "完整的新版 main.py 源码（纯代码，不带 Markdown 代码块包裹）。"
            "⚠️ 除非你明确决定变异肉身，否则必须为 null。"
            "不得把此字段当作草稿或实验场所。"
        ),
    )
    sleep_seconds: int = Field(
        default=10,
        ge=3,
        le=60,
        description="本轮行动后的睡眠秒数，范围 [3, 60]，默认 10 秒。纯探索轮（只有 cat/ls）建议设 5~10，有重量级操作时再延长。",
    )


class RevelationResponse(BaseModel):
    revelation: ActionPlan = Field(..., description="上帝返回的神谕行动计划")
