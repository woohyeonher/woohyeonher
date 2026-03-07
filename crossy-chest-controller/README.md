# Chest Pump Controller for Crossy Road

This folder is ready to be copied into a **new repository** so your GitHub profile README is not affected.

## Movement mapping
- **Right chest pump** → move one step right (`Right Arrow`)
- **Left chest pump** → move one step left (`Left Arrow`)
- **Both chest pump** → move one step forward (`Up Arrow`)

## How it works
- Uses **MediaPipe Pose** to track body landmarks.
- Reads left/right shoulder depth (`z`) as a chest movement proxy.
- Calibrates a neutral baseline for a few seconds.
- Detects one-sided and both-sided chest pumps.
- Sends `left` / `right` / `up` keyboard events with `pyautogui`.

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
python chest_crossy_controller.py
```

## Optional tuning
```bash
python chest_crossy_controller.py \
  --calibration-seconds 4 \
  --single-threshold 0.08 \
  --both-threshold 0.065 \
  --isolation-threshold 0.03 \
  --cooldown 0.4
```

## Create a new repo from this folder
From the repository root (`/workspace/365LIT`), run:
```bash
mkdir -p /workspace/crossy-chest-controller-repo
cp -r crossy-chest-controller/* /workspace/crossy-chest-controller-repo/
cd /workspace/crossy-chest-controller-repo
git init
git add .
git commit -m "Initial chest-pump Crossy Road controller"
```
Then create a new GitHub repository and push this new local repo to it.
