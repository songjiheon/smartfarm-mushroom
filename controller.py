"""
센서 데이터 -> 환경 판단 -> 장치 제어
"""

import time
from gpiozero import OutputDevice
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from sensor.sensor_data import SensorData
from config  import MUSHROOM_PROFILES, PinConfig, RELAY_ACTIVE_LOW
from stage_manager      import StageManager, Stage
import board 
import neopixel



#우선순위
_STATUS_ORDER = ["정상", "주의", "위험"]

class ControlStatus(Enum):
    OK = "정상"
    WARNING = "주의"
    DANGER = "위험"

def _escalate(current: ControlStatus, new: ControlStatus) -> ControlStatus:
    if _STATUS_ORDER.index(new.value) > _STATUS_ORDER.index(current.value):
        return new
    return current

@dataclass
class ActuatorState:
    humidifier : bool = False
    fan        : bool = False
    led        : bool = False

    def summary(self) -> str:
        def s(v): return "ON " if v else "OFF"
        return (
            f"가습기={s(self.humidifier)} 환기팬={s(self.fan)} LED={s(self.led)}"
        )

@dataclass
class ControlResult:
    stage     : str
    status    : ControlStatus
    actuator  : ActuatorState
    alerts    : list[str] = field(default_factory=list)
    actions   : list[str] = field(default_factory=list)
    timestamp : float     = field(default_factory=time.time)

    def print_report(self):
        print(f"\n{'-'*50}")
        print(f"[{time.strftime('%H:%M:%S')}] 제어 상태: {self.status.value}")
        print(f"------------------------------")
        for a in self.alerts:  print(f" {a}")
        for a in self.actions:  print(f" -> {a}")
        print(f"------------------------------")
        print(f" {self.actuator.summary()}")
        print(f"{'-'*50}")

class MushroomController:

    def __init__(self, mushroom: str ="느타리", stage_manager=None, use_gpio: bool =True):
        if mushroom not in MUSHROOM_PROFILES:
            raise ValueError(f"지원 프로파일: {list(MUSHROOM_PROFILES.keys())}")
        self._mushroom_profile = MUSHROOM_PROFILES[mushroom]
        self._mushroom_name    = mushroom
        self._stage_manager    = stage_manager
        self.use_gpio          = use_gpio
        self._devices          = {}
        self._fan_on = False
        self._fan_last_switch = 0
        self._fan_min_interval = 60

    def _current_profile(self) -> dict:
        if self._stage_manager is None:
            return self._mushroom_profile[Stage.PINNING.value]
        return self._mushroom_profile[self._stage_manager.current_stage().value]
        
    def _current_stage_name(self) -> str:
        if self._stage_manager is None:
            return Stage.PINNING.value
        return self._stage_manager.current_stage().value

    def setup(self) -> None:
        if self.use_gpio:
            self._devices = {
                "humidifier": OutputDevice(PinConfig.HUMIDIFIER, active_high=False, initial_value=True),
                "fan"       : OutputDevice(PinConfig.FAN,        active_high=False, initial_value=True),
            }
        self._led = neopixel.NeoPixel(
            board.D18,
            144,
            brightness=0.15,
            auto_write=True 
        )
        print(f"[Controller] 초기화 완료 ({self._mushroom_name})")

    def evaluate(self, data: SensorData) -> ControlResult:
        p        = self._current_profile()
        stage    = self._current_stage_name()
        actuator = ActuatorState()
        alerts   = []
        actions  = []
        status   = ControlStatus.OK
  

        s1 = self._evaluate_temperature(data.temperature, p, alerts, actions)
        s2 = self._evaluate_humidity   (data.humidity,    p, actuator, alerts, actions)
        s3 = self._evaluate_light      (data.lux,         p, actuator, alerts, actions)
        s4 = self._evaluate_co2         (data.co2,         p, actuator, alerts, actions)

        for s in (s1, s2, s3, s4):
            status = _escalate(status, s)
        return ControlResult(stage=stage, status=status,
                             actuator=actuator, alerts=alerts, actions=actions)

    #온도
    def _evaluate_temperature(self, temp, p, alerts, actions) -> ControlStatus:
        if temp is None:
            alerts.append("온도 센서 읽기 실패")
            return ControlStatus.WARNING

        if temp < p["temp_min"]:
            if temp < p["temp_min"] - 3:
                alerts.append(f"온도 위험 저하: {temp:.1f}C (기준 {p['temp_min']}C)")
                return ControlStatus.DANGER
            alerts.append(f"온도 낮음: {temp:.1f}C (기준 {p['temp_min']}C)")
            return ControlStatus.WARNING
        elif temp > p["temp_max"]:
            if temp > p["temp_max"] + 3:
                alerts.append(f"온도 위험 과열: {temp:.1f}C (기준 {p['temp_max']}C)")
                return ControlStatus.DANGER
            alerts.append(f"온도 높음: {temp:.1f}C (기준 {p['temp_max']}C)")
            return ControlStatus.WARNING
        actions.append(f"온도 정상 ({temp:.1f}C)")
        return ControlStatus.OK

    #습도
    def _evaluate_humidity(self, humi, p, actuator, alerts, actions) -> ControlStatus:
        if humi is None:
            alerts.append("습도 센서 읽기 실패")
            return ControlStatus.WARNING

        if humi < p["humi_min"]:
            actuator.humidifier = True
            actions.append(f"가습기 ON ({humi:.1f}% < {p['humi_min']}%)")
            if humi < p["humi_min"] - 10:
                alerts.append(f"습도 부족: {humi:.1f}%")
                return ControlStatus.DANGER
            return ControlStatus.WARNING

        elif humi > p["humi_max"]:
            return ControlStatus.WARNING
        actions.append(f"습도 정상 ({humi:.1f}%)")
        return ControlStatus.OK
        

    #조도
    def _evaluate_light(self, lux, p, actuator, alerts, actions) -> ControlStatus:
        if lux is None:
            alerts.append("조도 센서 읽기 실패")
            return ControlStatus.WARNING

        lux_mode = p.get("lux_mode","off")
        hour     = int(time.strftime("%H"))
        minute   = int(time.strftime("%M"))

        if lux_mode == "off" or not (8 <= hour < 20):
            actuator.led = False
            actions.append(f"LED OFF")
            return ControlStatus.OK

        #1시간 마다 10분 ON
        if lux_mode == "flash10":
            if minute < 10:
                actuator.led = True
                actions.append(f"LED ON (발생 조명 10분)")
            else:
                actuator.led = False
                actions.append(f"LED OFF (발생 조명 대기)")
            return ControlStatus.OK

        if lux_mode == "flash20":
            if minute < 20:
                actuator.led = True
                actions.append(f"LED ON (생육 조명 20분)")
            else:
                actuator.led = False
                actions.append(f"LED OFF (생육 조 대기)")
            return ControlStatus.OK

        return ControlStatus.OK
    
    #이산화탄소
    def _evaluate_co2(self, co2, p, actuator, alerts, actions) -> ControlStatus:

        if co2 is None:
            alerts.append("CO2 센서 읽기 실패")
            return ControlStatus.WARNING

        now = time.time()

        if co2 > p["co2_max"]:
            if not self._fan_on and (now - self._fan_last_switch > self._fan_min_interval):
                self._fan_on = True
                self._fan_last_switch = now

        elif co2 < p["co2_max"] - 200:
            if self._fan_on and (now - self._fan_last_switch > self._fan_min_interval):
                self._fan_on = False
                self._fan_last_switch = now
        
        actuator.fan = self._fan_on

        if co2 > p["co2_danger"]:
            alerts.append(f"CO2 위험: {co2} ppm")
            actions.append("환기팬  ON")
            return ControlStatus.DANGER

        elif co2 > p["co2_max"]:
            actions.append(f"환기팬 ON ({co2} ppm > {p['co2_max']})")
            return ControlStatus.WARNING

        actions.append(f"CO2 정상 ({co2} ppm)")
        return ControlStatus.OK

    #GPIO
    def apply(self, actuator: ActuatorState) -> None:
        if not self.use_gpio:
            return
        if actuator.fan:
            self._devices["fan"].on()
        else:
            self._devices["fan"].off()
        if actuator.humidifier:
            self._devices["humidifier"].on()
        else:
            self._devices["humidifier"].off()
        if actuator.led:
            self._led.fill((0,40,0))
        else:
            self._led.fill((0,0,0))

    #전체 OFF
    def all_off(self):
        if self.use_gpio:
            for d in self._devices.values():
                d.off()
 
    def cleanup(self):
        self.all_off()
        for d in self._devices.values():
            d.close()
        self._led.fill((0, 0, 0))
        print("[Controller]  정리 완료")

#테스트
if __name__ == "__main__":
    from sensor.DHT11 import DHT11Sensor
    from sensor.CDS   import CdSSensor
    from sensor.MHZ14A import MHZ14ASensor
    
    sm=StageManager()
    sm.start()
    sm.print_status()
    
    ctrl = MushroomController(mushroom="느타리", stage_manager=sm, use_gpio=True)
    ctrl.setup()
   
    dht = DHT11Sensor()
    cds = CdSSensor()
    co2 = MHZ14ASensor()

    dht.setup()
    cds.setup()
    co2.setup()

    print("테스트 시작")
    try:
        while True:
            temp, humi = dht.read()
            lux, raw   = cds.read()
            co2_val    = co2.read()

            data   = SensorData(temperature=temp, humidity=humi, lux=lux, lux_raw=raw,co2=co2_val)
            result = ctrl.evaluate(data)
            result.print_report()
            ctrl.apply(result.actuator)

            time.sleep(3)

    except KeyboardInterrupt:
        print("\n종료")
    finally:
        dht.cleanup()
        cds.cleanup()
        co2.cleanup()
        ctrl.cleanup()
        
