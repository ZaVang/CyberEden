# Sprint Contract: Foundation & V2 Ignition of Cyber-Eden

## Goal
在完成基础架构解耦之上，进入真正的联调运转设计阶段。本阶段将细化底层组件的真实逻辑，并完善 Docker 沙盒引擎的实际操纵点。

## Previous Completed Work (v0.1 Framework)
- [x] 架构分层规划、解耦及空壳骨架部署。

## Next Phase Plan (v0.2 Ignition & Core Implementation)
- [ ] **1. 全备的 LLM 接入层 (LLM Bridge & Oracle)**
  - 实现 `src/layer1/oracle/main.py` 内部逻辑。
  - 引入真实的 `real_llm_sdk` 实现大模型 API 的调用，以及 Prompt 模板（`src/prompts/oracle_system.j2`）的加载和组装。
- [ ] **2. 大天使沙盒操纵系统 (Archangel Docker Orchestrator)**
  - 接入 `docker` SDK 库，实现对 `eden_container` 沙盒的启动、强制杀死与资源监控。
  - 建立原子化的代码回滚机制：监控 `agent.py` 哈希变化的同时，需防范“写到一半中断崩溃”的情形。
- [ ] **3. 初始物种诞生 (Adam Genesis)**
  - 产出首个切实可用的极简版 `agent.py`，能够真实发出 `httpx` HTTP POST 请求到宿主机 Gateway 并覆写自身文件系统。
  - 创建初始设定集：真正的 `Bible.txt`（禁止修改）与空的 `Diary.txt`。
- [ ] **4. 绝对隔离启动编排 (Local Deployment & Isolation)**
  - 编写启动脚本或 `docker-compose` 编排隔离层，确保：
  - 沙盒层 `Bible.txt` 挂载属性为仅仅 `ro` (Read Only)。
  - 关闭沙盒进程一切非必要网络，只暴露出网到 `host.docker.internal:8000`。

## 验收命令 (TBD For Next Run)
- [`pytest`] 运行所有包含 Oracle、Archangel Mock 的基本单元测试。
- [`sh run_eden.sh`] 沙盒全量空载跑通第一次生命迭代。
