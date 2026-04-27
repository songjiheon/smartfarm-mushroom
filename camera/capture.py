import os
import time
from datetime import datetime
from picamera2 import Picamera2

SAVE_DIR = os.path.join(os.path.dirname(__file__), "captures")


class CameraCapture:
    def __init__(self, resolution=(1280, 720)):
        self._cam = None
        self._resolution = resolution
        os.makedirs(SAVE_DIR, exist_ok=True)

    def setup(self):
        self._cam = Picamera2()
        config = self._cam.create_still_configuration(
            main={"size": self._resolution}
        )
        self._cam.configure(config)
        self._cam.start()
        time.sleep(1)
        print("[Camera] 초기화 완료")

    def capture(self, stage="unknown", elapsed_days=0, temp=None, humi=None):
        if self._cam is None:
            raise RuntimeError("setup()을 먼저 호출하세요.")
            
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"{ts}.jpg"
        
        path = os.path.join(SAVE_DIR, name)
        self._cam.capture_file(path)
        
        print(f"[Camera] 촬영 완료: {name}")
        return path

    def cleanup(self):
        if self._cam:
            self._cam.stop()
            self._cam.close()
        print("[Camera] 정리 완료")

if __name__ == "__main__":
    cam = CameraCapture()
    cam.setup()

    INTERVAL = 30
    
    try:
        while True:
            cam.capture()
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\n[Camera] 사용자 종료 (Ctrl+C)")
    finally:
        cam.cleanup()

    cam.cleanup()
