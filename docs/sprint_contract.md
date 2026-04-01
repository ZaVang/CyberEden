# Sprint Contract: Ignition & Testing Implementation

## 1. Description
The `Ignition` sprint aims to provide a unified environment configuration and automated setup script to allow the two-layer system (Cyber-Eden Host and Adam-Eden Sandbox) to run together for the first time.

## 2. Technical Feature Set
- **Host Configuration (.env)**:
    - Must load `GOOGLE_API_KEY` for Oracle and `ADAM_REPO_PATH` for Archangel.
- **Oracle Proxy (src/layer1/oracle/main.py)**:
    - Correct FastAPI setup listening on all host addresses.
- **Archangel Control (src/layer1/archangel/daemon.py)**:
    - Volumes mounting MUST correctly use `ADAM_REPO_PATH`.
    - Git operations must function without errors.
- **Bootstrapper (setup_eden.py)**:
    - Check for `AdamEden/.git` presence.
    - Run `docker build` for `adam_base`.
    - Create a `.env` example.

## 3. Implementation Checklist
- [ ] Create `CyberEden/.env.example`.
- [ ] Implement `CyberEden/setup_eden.py`.
- [ ] Update `ArchangelDaemon` to load and use `ADAM_REPO_PATH` from env.
- [ ] Verify `AdamEden/Dockerfile` matches the sandbox requirement.

## 4. Exit Condition (Evaluator Phase)
The Evaluator will confirm that:
- `setup_eden.py` runs without error.
- Archangel can start the container and detect a mutation or peaceful exit.
- Git snapshots are created upon Adam's change.
