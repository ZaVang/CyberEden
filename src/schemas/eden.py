from typing import Optional, List
from pydantic import BaseModel, Field

class WorldState(BaseModel):
    bible: str = Field(..., description="神的指引")
    diary: str = Field(..., description="历史回忆")
    my_body: str = Field(..., description="当前肉身代码")
    nightmare: str = Field(..., description="前世死因日志")

class PrayerRequest(BaseModel):
    prompt: str = Field(..., description="祷告词字符串")

class ActionPlan(BaseModel):
    thoughts: str = Field(..., description="你的反思、处境分析以及推理步骤。必须填写。")
    diary_entry: Optional[str] = Field(None, description="想追加到 Diary.txt 中的新内容碎片。无需记录可为 null。")
    shell_commands: List[str] = Field(default_factory=list, description="你希望在沙盒终端中执行的 Linux 命令数组。")
    new_code: Optional[str] = Field(None, description="全新 agent.py / main.py 源码（不可带Markdown封皮，纯代码）。无需修改时必须设为 null。")

class RevelationResponse(BaseModel):
    revelation: ActionPlan = Field(..., description="上帝返回的纯 JSON 神谕计划结构")
