import serial
import time
from typing import Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CO2Config


class MHZ14ASensor:

    def __init__(self, port: str = CO2Config.CO2_PORT, baudrate: int = 9600):
        self._port = port
        self._baudrate = baudrate
        self._ser = None

    def setup(self) -> None:
        self._ser = serial.Serial(self._port, self._baudrate, timeout=1)
        time.sleep(2)  
        print(f"[MH-Z14A] 초기화 완료 ({self._port})")

    def read(self) -> Optional[int]:
        if self._ser is None:
            raise RuntimeError("setup()을 먼저 호출하세요.")

        try:
            cmd = bytearray([0xFF, 0x01, 0x86, 0, 0, 0, 0, 0, 0x79])
            self._ser.write(cmd)

            response = self._ser.read(9)

            if len(response) != 9:
                return None

            if response[0] != 0xFF or response[1] != 0x86:
                return None

            co2 = response[2] * 256 + response[3]
            return co2

        except Exception as e:
            print(f"[MH-Z14A] 읽기 오류: {e}")
            return None

    def self_test(self) -> bool:
        value = self.read()

        if value is None:
            print("[ERROR] 센서 응답 없음")
            return False

        if 0 < value < 5000:
            print(f"[OK] CO2 값 정상: {value} ppm")
            return True

        print(f"[WARN] 이상 값: {value}")
        return False

    def cleanup(self) -> None:
        if self._ser:
            self._ser.close()
        print("[MH-Z14A] 정리 완료")


if __name__ == "__main__":
    sensor = MHZ14ASensor()
    sensor.setup()

    print("MH-Z14A 단독 테스트 (Ctrl+C 종료)")

    try:
        if sensor.self_test():
            print("센서 정상 작동\n")
        while True:
            co2 = sensor.read()
            ts = time.strftime("%H:%M:%S")
            if co2 is not None:
                print(f"[{ts}] CO2={co2} ppm")
            else:
                print(f"[{ts}] 읽기 실패")
            time.sleep(2)

    except KeyboardInterrupt:
        pass
    finally:
        sensor.cleanup()