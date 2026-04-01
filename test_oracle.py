import asyncio
import os
from dotenv import load_dotenv
from src.infra.llm_bridge import LLMBridge
from src.schemas.eden import ActionPlan

# 加载环境变量
load_dotenv()

async def test_llm():
    print("=== Cyber-Eden: Oracle 圣遗物校验测试 ===")
    
    # 1. 检查 API KEY
    api_key = os.getenv("GOOGLE_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")
    
    if not api_key:
        print("[!] 错误: 未在 .env 中发现 GOOGLE_API_KEY")
        return
    
    print(f"[*] 准备连接 Google Gemini API...")
    print(f"[*] 目标模型: {model_name}")
    
    try:
        # 2. 初始化桥接
        bridge = LLMBridge.from_env()
        
        # 3. 发起一次模拟祷告
        print("[*] 正在发送模拟祷告 (Test Prayer)...")
        response = await bridge.chat(
            messages=[{"role": "user", "content": "你好，你是亚当的灵魂导引吗？告诉我你的名字。"}],
            response_model=ActionPlan
        )
        
        # 4. 验证解析
        if response.parsed:
            print("[√] 成功！神谕响应并正确解析了 JSON 结构:")
            print(f"    - 思绪: {response.parsed.thoughts}")
            print(f"    - 日记: {response.parsed.diary_entry}")
        else:
            print("[?] 模型响应了，但未能成功解析 JSON。")
            print(f"    - 原始文本: {response.content[:200]}...")
            
        print(f"[*] Token 消耗: {response.usage}")
        print("[*] 停止原因: {response.stop_reason}")

    except Exception as e:
        print(f"[!] 致命故障: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm())
