#!/usr/bin/env python3
"""Control Crossy Road with chest pumps using a laptop webcam.

Mapping:
- Right chest pump  -> Right arrow
- Left chest pump   -> Left arrow
- Both chest pumps  -> Up arrow (forward)

How it works:
1. Mediapipe Pose tracks shoulder landmarks.
2. A short calibration records each shoulder's neutral depth (z).
3. Moving a shoulder toward the camera lowers z; we detect this as a pump.
4. Key presses are emitted with a cooldown to avoid repeats.
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass

import cv2
import mediapipe as mp
import pyautogui


LEFT_SHOULDER_INDEX = 11
RIGHT_SHOULDER_INDEX = 12


@dataclass
class DetectorConfig:
    camera_index: int = 0
    calibration_seconds: float = 3.0
    single_threshold: float = 0.07
    both_threshold: float = 0.06
    isolation_threshold: float = 0.025
    cooldown_seconds: float = 0.35
    model_complexity: int = 1
    min_detection_confidence: float = 0.6
    min_tracking_confidence: float = 0.6


class ChestPumpController:
    def __init__(self, config: DetectorConfig) -> None:
        self.config = config
        self.baseline_left: float | None = None
        self.baseline_right: float | None = None
        self.last_command_at = 0.0

        pyautogui.FAILSAFE = True

        self.pose = mp.solutions.pose.Pose(
            model_complexity=config.model_complexity,
            min_detection_confidence=config.min_detection_confidence,
            min_tracking_confidence=config.min_tracking_confidence,
        )

    def run(self) -> None:
        cap = cv2.VideoCapture(self.config.camera_index)
        if not cap.isOpened():
            raise RuntimeError(
                f"Could not open camera index {self.config.camera_index}."
            )

        calibration_end = time.time() + self.config.calibration_seconds
        left_samples: list[float] = []
        right_samples: list[float] = []

        print("Starting webcam. Press q to quit.")
        print("During calibration, stand naturally and face the camera.")
        print("Focus the game window before playing so keypresses go to Crossy Road.")

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    print("Warning: camera frame not available.")
                    break

                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = self.pose.process(rgb)

                now = time.time()
                status_text = "No body detected"

                if result.pose_landmarks:
                    landmarks = result.pose_landmarks.landmark
                    left_z = landmarks[LEFT_SHOULDER_INDEX].z
                    right_z = landmarks[RIGHT_SHOULDER_INDEX].z

                    if now < calibration_end:
                        left_samples.append(left_z)
                        right_samples.append(right_z)
                        remaining = max(0.0, calibration_end - now)
                        status_text = f"Calibrating... {remaining:0.1f}s"
                    else:
                        if self.baseline_left is None or self.baseline_right is None:
                            self.baseline_left = sum(left_samples) / max(1, len(left_samples))
                            self.baseline_right = sum(right_samples) / max(1, len(right_samples))
                            print(
                                "Calibration complete.",
                                f"baseline_left={self.baseline_left:.4f}",
                                f"baseline_right={self.baseline_right:.4f}",
                            )

                        left_push = self.baseline_left - left_z
                        right_push = self.baseline_right - right_z

                        command = self._detect_command(left_push, right_push, now)
                        status_text = (
                            f"L push: {left_push:+0.3f} | R push: {right_push:+0.3f}"
                        )

                        if command:
                            pyautogui.press(command)
                            status_text += f" -> {command.upper()}"

                    mp.solutions.drawing_utils.draw_landmarks(
                        frame,
                        result.pose_landmarks,
                        mp.solutions.pose.POSE_CONNECTIONS,
                    )

                cv2.putText(
                    frame,
                    status_text,
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )

                cv2.imshow("Chest Pump Crossy Controller", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.pose.close()

    def _detect_command(self, left_push: float, right_push: float, now: float) -> str | None:
        if now - self.last_command_at < self.config.cooldown_seconds:
            return None

        if (
            left_push > self.config.both_threshold
            and right_push > self.config.both_threshold
        ):
            self.last_command_at = now
            return "up"

        if (
            right_push > self.config.single_threshold
            and left_push < self.config.isolation_threshold
        ):
            self.last_command_at = now
            return "right"

        if (
            left_push > self.config.single_threshold
            and right_push < self.config.isolation_threshold
        ):
            self.last_command_at = now
            return "left"

        return None


def parse_args() -> DetectorConfig:
    parser = argparse.ArgumentParser(description="Chest-pump controller for Crossy Road")
    parser.add_argument("--camera", type=int, default=0, help="Webcam index")
    parser.add_argument(
        "--calibration-seconds",
        type=float,
        default=3.0,
        help="How long to collect neutral chest posture before control starts",
    )
    parser.add_argument(
        "--single-threshold",
        type=float,
        default=0.07,
        help="Depth delta needed for one-sided chest pump (left/right)",
    )
    parser.add_argument(
        "--both-threshold",
        type=float,
        default=0.06,
        help="Depth delta needed for both-chest pump (forward)",
    )
    parser.add_argument(
        "--isolation-threshold",
        type=float,
        default=0.025,
        help="Maximum opposite side movement allowed for left/right detection",
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=0.35,
        help="Minimum seconds between commands",
    )

    args = parser.parse_args()

    return DetectorConfig(
        camera_index=args.camera,
        calibration_seconds=args.calibration_seconds,
        single_threshold=args.single_threshold,
        both_threshold=args.both_threshold,
        isolation_threshold=args.isolation_threshold,
        cooldown_seconds=args.cooldown,
    )


if __name__ == "__main__":
    config = parse_args()
    controller = ChestPumpController(config)
    controller.run()
