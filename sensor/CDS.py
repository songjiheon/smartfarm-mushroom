import spidev
import time
import sys
import os
from typing import Optional, Tuple
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CdSConfig

#MCP3008 설정
SPI_BUS     = 0
SPI_DEVICE  = 0
SPI_SPEED   = 1_350_000

MCP_RAW_MAX = 1023

class CdSSensor:

    def __init__(
        self,
        channel:    int = 0,         
        spi_bus:    int = SPI_BUS,
        spi_device: int = SPI_DEVICE,
    ):
        self._channel    = channel
        self._spi_bus    = spi_bus
        self._spi_device = spi_device
        self._spi        = None

    def setup(self) -> None:
        self._spi          = spidev.SpiDev()
        self._spi.open(self._spi_bus, self._spi_device)
        self._spi.max_speed_hz = SPI_SPEED
        self._spi.mode         = 0b00   # MCP3008 SPI Mode 0
        print(f"[CdS] 초기화 완료 (MCP3008 CH{self._channel}, SPI{self._spi_bus})")
 
    def read(self) -> Tuple[Optional[float], Optional[int]]:
        if self._spi is None:
            raise RuntimeError("setup()을 먼저 호출하세요.")
        try:
            raw = self._read_mcp3008(self._channel)
            lux = self._raw_to_lux(raw)
            return lux, raw

        except Exception as e:
            print(f"[CdS] 읽기 오류:{e}")
            return None, None

    def _read_mcp3008(self, channel: int) -> int:
        cmd = [0x01, (0x08 + channel) << 4, 0x00]
        result = self._spi.xfer2(cmd)

        raw = ((result[1] & 0x03) << 8) | result[2]
        return raw

    @staticmethod
    def _raw_to_lux(raw: int) -> float:
        raw_clamped = max(0, min(MCP_RAW_MAX, raw))
        ratio = raw_clamped / MCP_RAW_MAX
        return round(CdSConfig.LUX_MIN + ratio * (CdSConfig.LUX_MAX - CdSConfig.LUX_MIN), 1)

    def cleanup(self) -> None:
        if self._spi:
            self._spi.close()
        print("[CdS] 정리 완료")

if __name__ == "__main__":
    sensor = CdSSensor(channel=0)
    sensor.setup()
    print("CdS 단독 테스트 (Ctrl+c 종료)")
    try:
        while True:
            lux, raw = sensor.read()
            ts = time.strftime("%H:%M:%S")
            if lux is not None:
                bar = "?" * int(raw / 100) + "?" * (10 - int(raw / 100))
                print(f"[{ts}] 조도={lux:6.1f} lux ADC={raw:4d}")
            else:
                print(f"[{ts}] 읽기 실패")
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        sensor.cleanup()


