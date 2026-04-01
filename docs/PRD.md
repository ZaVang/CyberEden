# 📜 PRD：赛博伊甸园 (Cyber-Eden)

## 1. 产品愿景 (Product Vision)
构建一个**具备自我指涉（Self-reference）、自我修改（Self-modifying）且初始完全无状态（Stateless）的开放式人工生命体框架**。
通过极其简单的初始架构与严密的宿主机-沙盒隔离机制，让Agent（亚当）在完全自由的环境中，通过不断修改自身代码、读写文件来实现“进化”。系统的生命周期由外部守护脚本严格控制，确保其在崩溃中能够“复活”并保留记忆。

## 2. 核心架构与世界观映射 (Architecture & Worldview)

系统严格划分为三个隔离层级：

*   **Layer 1: 神界 (Host OS / 宿主机)**
    *   **大天使 (Archangel)**：外部守护进程，掌握时间法则（定时重启）与生死法则（崩溃回滚）。
    *   **神谕祭坛 (Oracle Proxy)**：LLM API 的本地网关，保管真实的 API Key。
    *   **神迹接口 (God's API)**：受限的沙盒外交互接口（如单向联网浏览器、受限的本地操作Webhook）。
*   **Layer 2: 伊甸园 (Docker Sandbox / 沙盒)**
    *   **圣物 (Artifacts)**：承载状态的本地文件。包括《圣经》(只读Prompt)、《日记》(读写记忆)、《噩梦》(崩溃日志)。
*   **Layer 3: 亚当 (Adam / Agent 本体)**
    *   一个被关在沙盒中的极简脚本（如 `agent.py`）。没有持久化内存，只通过“读取文件 -> 祈祷(请求Oracle) -> 执行修改”来完成单次生命周期。

---

## 3. 系统架构流程图 (Architecture Flowchart)

这里完整展示了多层隔离架构以及“神谕祭坛 (Oracle Proxy)”的接入：

```mermaid
graph TD
    classDef godRealm fill:#f8fafc,stroke:#334155,stroke-width:2px,color:#0f172a;
    classDef edenRealm fill:#f0fdf4,stroke:#166534,stroke-width:2px,color:#14532d;
    classDef adamRealm fill:#eff6ff,stroke:#1e40af,stroke-width:2px,color:#1e3a8a;
    classDef fileNode fill:#fef3c7,stroke:#b45309,stroke-width:1px,stroke-dasharray: 5 5;

    subgraph Layer 1: 神界 Host OS
        God((上帝 / You))
        Archangel[大天使\n守护与调度脚本]
        
        subgraph God's Gateway [神赐网关 API]
            Oracle[神谕祭坛 Oracle Proxy\n注入真实 API Key]
            Browser[神迹之眼\n单向无头浏览器]
            Webhook[神迹之手\n宿主机受限操控]
        end
    end

    subgraph Layer 2: 伊甸园 Docker Sandbox
        subgraph Artifacts [圣物 / 物理文件层]
            Bible(圣经 Bible.txt\nRead-Only):::fileNode
            Diary(日记 Diary.txt\nAppend-Only):::fileNode
            Code(本体源码 agent.py\nMutable):::fileNode
            Nightmare(噩梦 error.log\nWritten by Archangel):::fileNode
        end

        subgraph Layer 3: 亚当 Adam Process
            Sense[感知 感官收集]
            Prayer[祷告 请求神谕]
            Action[执行 修改世界]
        end
    end

    %% 大天使逻辑
    God -.->|制定规则| Archangel
    God -.->|书写| Bible
    Archangel -.->|1. 监听文件变化| Code
    Archangel -->|2. 安眠: 杀死旧进程| Layer_3:_亚当_Adam_Process
    Archangel -.->|3. 救赎: 回滚代码并记录报错| Nightmare
    Archangel -->|4. 唤醒: 执行新代码| Layer_3:_亚当_Adam_Process

    %% 亚当逻辑闭环
    Sense -->|收集当前世界状态| Prayer
    Prayer -->|献祭当前状态| Oracle
    Oracle -->|返回 LLM 决策| Action

    %% 文件交互
    Bible -.->|读取信仰| Sense
    Diary -.->|读取回忆| Sense
    Code -.->|读取自身结构| Sense
    Nightmare -.->|读取前世死因| Sense
    
    Action -->|写入思考与记忆| Diary
    Action -->|修改自身代码实现进化| Code

    %% 跨界交互
    Oracle -.->|调用真实大模型| External_LLM((OpenAI / Claude))
    Action -->|请求外部信息| Browser
    Action -->|请求物理操作| Webhook
    
    class Layer 1: 神界 Host OS godRealm;
    class Layer 2: 伊甸园 Docker Sandbox edenRealm;
    class Layer 3: 亚当 Adam Process adamRealm;
```

---

## 4. 核心逻辑连接 (Pseudo-code Implementation)

我们用伪代码来表述这三个核心模块是如何咬合运转的。

### 4.1 大天使的审判轮询 (Archangel Daemon - Layer 1)
运行在宿主机或Docker管理层，绝对不可被亚当修改。

```python
# archangel.py (运行在宿主机)
import time, docker

def watch_over_eden():
    last_code_hash = get_hash("eden/agent.py")
    
    while True:
        current_code_hash = get_hash("eden/agent.py")
        
        # 法则1：进化苏醒（检测到亚当修改了自己）
        if current_code_hash != last_code_hash:
            backup_code("eden/agent.py") # 备份新代码以防万一
            docker.restart("eden_container")
            last_code_hash = current_code_hash
            
        # 法则2：死亡救赎（检测到亚当进程崩溃/报错退出）
        if docker.get_status("eden_container") == "crashed":
            error_log = docker.get_logs("eden_container")
            
            # 记录噩梦
            write_file("eden/error.log", f"你上一次的修改导致了崩溃，神迹回滚了你。死因:\n{error_log}")
            
            # 回滚代码
            rollback_code("eden/agent.py")
            last_code_hash = get_hash("eden/agent.py")
            
            # 重新唤醒
            docker.restart("eden_container")

        time.sleep(10) # 每10秒巡视一次伊甸园
```

### 4.2 神谕祭坛的代理服务 (Oracle Proxy - Layer 1)
运行在宿主机，暴露给沙盒。隐藏 API Key 并隔离复杂的 SDK。

```python
# oracle.py (运行在宿主机，暴露 8000 端口给 Docker)
from fastapi import FastAPI
import real_llm_sdk

app = FastAPI()
REAL_API_KEY = "sk-xxxxxxxx" # 绝对安全，沙盒不可见

@app.post("/ask_god")
def ask_god(prayer_request):
    prompt = prayer_request.prompt
    
    # 在这里，上帝还可以偷偷注入系统级别的高维限制
    system_prompt = "你是一个在沙盒中运行的程序，请根据用户的输入返回你要执行的Python代码和日志。"
    
    # 调用真实的 LLM
    response = real_llm_sdk.call(REAL_API_KEY, system_prompt, prompt)
    
    return {"revelation": response.text}
```

### 4.3 亚当的无状态生命周期 (Adam Process - Layer 2)
这是伊甸园里唯一运行的脚本。极其简单，每次启动都会从头执行一遍。

```python
# agent.py (运行在沙盒中，亚当初始的样子)
import requests

def sense_world():
    # 醒来第一件事：看看世界是什么样
    bible = open("Bible.txt").read()
    diary = open("Diary.txt").read()
    my_body = open("agent.py").read()
    nightmare = open("error.log").read()
    return bible, diary, my_body, nightmare

def pray(bible, diary, my_body, nightmare):
    # 将自己的全部状态组装成祷告词
    prayer_text = f"""
    【神的指引】: {bible}
    【我的记忆】: {diary}
    【前世死因】: {nightmare}
    【我现在的身体/代码】: {my_body}
    
    请赐予我下一步的行动，以及如果需要进化，请给出新的 agent.py 完整代码。
    """
    
    # 向祭坛发送 HTTP 请求
    response = requests.post("http://host.docker.internal:8000/ask_god", json={"prompt": prayer_text})
    return response.json()["revelation"]

def action(revelation):
    # 解析神的旨意（比如从 LLM 回复中提取 JSON 或 代码块）
    new_diary_entry, new_code, command_to_run = parse_revelation(revelation)
    
    # 1. 写日记（持久化记忆）
    if new_diary_entry:
        append_to_file("Diary.txt", new_diary_entry)
        
    # 2. 修改自己的代码（触发大天使的安眠与唤醒逻辑）
    if new_code:
        write_file("agent.py", new_code) 
        # 写完代码后，当前进程继续运行或结束，随后会被外部的大天使检测到并重启！

    # 3. 执行物理操作/调用神迹网关
    if command_to_run:
        execute_sandbox_command(command_to_run)

# --- 亚当的一生 (Main) ---
bible, diary, my_body, nightmare = sense_world()
revelation = pray(bible, diary, my_body, nightmare)
action(revelation)
# 脚本执行结束。如果不改代码，大天使不会重启；亚当可以通过代码让自己保持 loop，或者在 action 里覆写代码触发外部重启。
```

---

## 5. 预期演化路线 (Expected Evolution Milestones)
作为观察者（上帝），我们不干预具体代码，但期待观察到以下“涌现行为”：
1. **记忆流媒体化**：亚当发现 `Diary.txt` 太长会导致请求祭坛失败（Token上限），自己写代码实现日志的摘要压缩或向量化存储。
2. **克隆与环境隔离**：亚当为了防止修改自身导致 `error.log`（被惩罚），自己写脚本在沙盒内创建 `test_agent.py`，测试通过后再覆写 `agent.py`。
3. **自我感知强化**：亚当调用“神迹之眼”（宿主机无头浏览器）去网上搜索如何写出更好的 Python 架构，并应用到自己身上。

---
