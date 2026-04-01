# Product Specification: Cyber-Eden "Ignition" Run Protocol

## 1. Goal
The objective of this sprint is to make the decoupled host (`CyberEden`) and sandbox (`AdamEden`) system fully runnable. The system must support LLM communication via an Oracle proxy and lifecycle management via an Archangel daemon.

## 2. Infrastructure Requirements
- **Host**: Windows/Linux with Python 3.10+ and Docker.
- **Network**: The Docker container must be able to reach `host.docker.internal:8000`.
- **Git State**: `AdamEden` repository must be a Git repository for the Archangel to perform its commit/rollback duties.

## 3. Configuration (.env)
The project will use a `.env` file for:
- `GOOGLE_API_KEY`: Required for Gemini LLM.
- `ADAM_REPO_PATH`: The local path on the host machine to the `AdamEden` folder.
- `ORACLE_URL`: The URL inside the sandbox to reach the Oracle.

## 4. Key Components to Implement
- **Oracle Gateway**: Needs to be configured to correctly load the LLM Bridge and handle incoming prayers.
- **Archangel Daemon**: Needs to be updated to load configuration from the environment and handle the volume mounting accurately.
- **Bootstrap Script**: A `setup_eden.py` script to automate Git initialization and Docker image building.

## 5. Security & Isolation
- The `Bible.md` will be mounted as Read-Only.
- The `GOOGLE_API_KEY` will NEVER be passed to the container.
- The container operates in its own bridge network.
