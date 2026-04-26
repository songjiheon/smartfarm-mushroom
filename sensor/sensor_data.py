import time
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class SensorData:
    temperature : Optional[float] = None
    humidity    : Optional[float] = None
    lux         : Optional[float] = None
    lux_raw     : Optional[int]   = None
    timestamp   : float = field(default_factory=time.time)

    def summary(self) -> str:
        t = f"{self.temperature:.1f}C" if self.temperature is not None else "N/A"
        h = f"{self.humidity:.1f}%"    if self.humidity    is not None else "N/A"
        l = f"{self.lux:.1f} lux"      if self.lux         is not None else "N/A"
        return f"온도={t} 습도={h} 조도={l}"