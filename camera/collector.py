import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from camera.capture  import CameraCapture
from camera.upload import DriveUploader
from stage_manager   import StageManager

INTERVAL = 60 #1분마다 촬영

class DataCollector:
    def __init__(self, stage_manager=None):
        self._capture  = CameraCapture()
        self._upload = DriveUploader()
        self._sm       = stage_manager

    def setup(self):
        self._capture.setup()
        self._upload.setup()
        print("[Collector] 초기화 완료")

    def collect(self, temp=None, humi=None):
        stage = self._sm.current_stage().value if self._sm else "unknown"
        days  = self._sm.elapsed_days()        if self._sm else 0
        path  = self._capture.capture(stage=stage, elapsed_days=days, temp=temp, humi=humi)
        self._upload.upload(path)
        return path

    def cleanup(self):
        self._capture.cleanup()
        print("[Collector] 정리 완료")

#테스트
if __name__ == "__main__":
    from sensor.DHT11 import DHT11Sensor

    sm  = StageManager()
    sm.start()

    col = DataCollector(stage_manager=sm)
    col.setup()

    dht = DHT11Sensor()
    dht.setup()

    print(f"데이터 수집 시작 ({INTERVAL}초 간격, Ctrl+C 종료)")
    try:
        while True:
            temp, humi = dht.read()
            col.collect(temp=temp, humi=humi)
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\n종료")
    finally:
        col.cleanup()
        dht.cleanup()
