import os
import time
from datetime import datetime
import cv2

SAVE_DIR = os.path.join(os.path.dirname(__file__), "captures")


class CameraCapture:
    def __init__(self, resolution=(1280, 720), device_index=0):
        self._cam = None
        self._resolution  = resolution
        self._device_index = device_index
        os.makedirs(SAVE_DIR, exist_ok=True)

    def setup(self):
        self._cam = cv2.VideoCapture(self._device_index)
        if not self._cam.isOpened():
            raise RuntimeError(f"웹캠 열기 실패 (device_index={self._device_index})")

        # 해상도 설정
        w, h = self._resolution
        self._cam.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self._cam.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

        time.sleep(1)
        print("[Camera] 웹캠 초기화 완료")

    def capture(self, stage="unknown", elapsed_days=0, temp=None, humi=None):
        if self._cam is None:
            raise RuntimeError("setup()을 먼저 호출하세요.")

        ret, frame = self._cam.read()
        if not ret:
            raise RuntimeError("웹캠 프레임 캡처 실패")

        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"{ts}.jpg"
        path = os.path.join(SAVE_DIR, name)

        # 이미지 저장
        cv2.imwrite(path, frame)

        print(f"[Camera] 촬영 완료: {name}")
        return path

    def cleanup(self):
        if self._cam:
            self._cam.release()
            self._cam = None
        print("[Camera] 정리 완료")

if __name__ == "__main__":
    cam = CameraCapture(resolution=(1280, 720), device_index=0)
    cam.setup()

    INTERVAL = 300 
     
    try:
        while True:
            cam.capture()
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\n[Camera] 사용자 종료 (Ctrl+C)")
    finally:
        cam.cleanup()

