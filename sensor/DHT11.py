import time
import board
import adafruit_dht
import sys
import os
from typing import Optional, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PinConfig


class DHT11Sensor:

    def __init__(self, pin=None):
        self._pin = pin or getattr(board, f"D{PinConfig.DHT11_DATA}")
        self._device = None

    def setup(self) -> None:
        self._device = adafruit_dht.DHT11(self._pin)
        print(f"[DHT11] Initialization complete (GPIO{PinConfig.DHT11_DATA})")

    def read(self, retries: int = 3) -> Tuple[Optional[float], Optional[float]]:
        if self._device is None:
            raise RuntimeError("Call setup() first.")

        for attempt in range(retries):
            try:
                temp = self._device.temperature
                humi = self._device.humidity
                if temp is not None and humi is not None:
                    return float(temp), float(humi)
            except RuntimeError:
                if attempt < retries - 1:
                    time.sleep(1)

        return None, None

    def reboot(self) -> None:
        try:
            self._device.exit()
        except Exception:
            pass
        time.sleep(1)
        self._device = adafruit_dht.DHT11(self._pin)
        print("[DHT11] Reinitialized")

    def cleanup(self) -> None:
        if self._device:
            try:
                self._device.exit()
            except Exception:
                pass
        print("[DHT11] 정리 완료")


if __name__ == "__main__":
    sensor = DHT11Sensor()
    sensor.setup()
    print("DHT11 standalone test (Ctrl+C to exit)")
    try:
        while True:
            temp, humi = sensor.read()
            ts = time.strftime("%H:%M:%S")
            if temp is not None:
                print(f"[{ts}] Temp={temp:.1f}C Humi={humi:.1f}%")
            else:
                print(f"[{ts}] Read failed")
            time.sleep(3)
    except KeyboardInterrupt:
        pass
    finally:
        sensor.cleanup()
