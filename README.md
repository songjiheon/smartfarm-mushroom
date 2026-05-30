## 📖 프로젝트 개요

- ~~는 센서와 카메라, 그리고 AI를 결합해 버섯의 현재 생장 단계를 자동으로 판별하고, 단계별 최적 환경을 유지해주는 자동화 재배 시스템입니다.

- 사용자가 직접 환경을 조절하지 않아도, 시스템이 버섯의 상태를 스스로 파악하고 환풍기·가습기·LED 조명을 제어하여 최적의 성장 환경을 만들어냅니다.
---

## 🛠  주요 기능
1. **환경 수치 파악:** 온도·습도·CO2 센서를 주기적으로 읽어 재배기 내부 상태 모니터링
2. **AI 생장 단계 판별:** 카메라로 일정 주기마다 버섯을 촬영해 현재 생장 단계(발생/생육/수확) 자동 판별
3. **환경 프로파일 비교:** 판별된 생장 단계별 환경 config를 기준으로 정상/주의/위험 상태 판단
4. **장치 자동 제어:** 환경 수치에 따라 환풍기·가습기(Tapo 스마트플러그)·LED 자동 제어
5. **예외 처리 및 경고:** 이상 수치 감지 시 경고 메시지 출력 및 단계별 조치 적용
---

## 🧰 기술 스택 (Tech Stack)

### Hardware & OS
- **OS:** Raspberry Pi OS
- **Platform:** Raspberry Pi 5 (4GB)

### Language & Runtime
- **Language:** Python 3.x

### AI & Computer Vision
- **Framework:** TensorFlow Lite (tflite-runtime)
- **Library:** OpenCV (opencv-python), Pillow

### Hardware Control (IoT)
- **GPIO Framework:** gpiozero, rpi-lgpio
- **Sensor & Actuator:** rpi_ws281x, adafruit-circuitpython-neopixel, pyserial, dht11
- **Smart Plug Control:** tapo (Tapo P110M 제어 API)

---

## 🔧 하드웨어 구성

| 구성 요소 | 모델 / 사양 | 역할 |
|-----------|------------|------|
| **메인 보드** | Raspberry Pi 5 4GB | 전체 시스템 제어 |
| **온습도 센서** | DHT11 | 온도·습도 측정 |
| **CO2 센서** | MH-Z14A| 이산화탄소 농도 측정 |
| **카메라** |DRGO WC720 | 버섯 이미지 촬영 |
| **환기팬** | DC5V 팬모터 MGA4005LR-A10 | 공기 순환 및 CO₂ 조절 |
| **가습기** | 초음파 가습 모듈 | 습도 조절 |
| **LED** | 5V WS2812 Flexible LED | 광량 조절 |
| **릴레이 모듈** | 1채널 릴레이 | 환기팬 전원 제어 |
| **릴레이 플러그** | Tapo P110M | 가습기 전원 제어 |

---
## 🤖 AI 생장 단계 분석

카메라로 촬영된 식물 이미지를 AI 모델이 분석하여 현재 생장 단계를 판별합니다.

### 생장 단계 분류

```
발생 (Occurrence)  →  생육(Growth)  → 수확(Harvest)
```

---


## ⚙️ 단계별 환경 Config

각 생장 단계마다 최적 환경값이 py파일로 정의되어 있으며, AI가 단계를 판별하면 해당 config를 자동 로드합니다.

```py
# config.py (생육 단계 예시)
"느타리":{
      "발생":{
         "temp_min":21.0, "temp_max":23.0, "temp_target":22.0,
         "humi_min":90.0, "humi_max":95.0,
         "co2_max":1200, "co2_danger":2000,
         "lux_mode":"flash10",
      },
}
```

---

## 🚀 설치 및 실행

### 1. 의존성 설치

```bash
python3 -m venv ~/smartfarm
source ~/smartfarm/bin/activate

# AI 및 컴퓨터 비전 관련 패키지
pip install tflite-runtime opencv-python pillow

# 라즈베리파이 5 GPIO 패키지
pip install gpiozero rpi-lgpio

# 센서, 스마트플러그 및 LED 패키지
pip install pyserial                  # MH-Z14A (CO2)
pip install tapo                      # Tapo 스마트플러그
pip install rpi_ws281x adafruit-circuitpython-neopixel
pip install dht11
```

### 2. 하드웨어 설정

```bash
### 2. 하드웨어 설정(카메라,이산화탄소,온습도)
echo "dtparam=i2c_arm=on" | sudo tee -a /boot/firmware/config.txt
echo "dtparam=spi=on" | sudo tee -a /boot/firmware/config.txt
echo "enable_uart=1" | sudo tee -a /boot/firmware/config.txt
sudo reboot
```



### 3. 실행

```bash
python3 controller.py
```

---



## 📁 프로젝트 구조

```
smartfarm/
├── controller.py             # 메인 실행 진입점
├── config.py                 # 생장 단계별 기준 값
├── sensors/
│   ├── DHT11.py              # 온습도 센서 
│   ├── MHZ14A.py             # CO2 센서 
│   ├── __init__.py           # 센서 패키지
│   └── sensor_data.py        # 센서 데이터 통합
├── camera/
│   └── capture.py            # 카메라 촬영 모듈
├── ai/
│   ├── model_fp16.tflite     # AI 생장 단계 분류 모델
│   └── predictor.py          # 생장 단계 추론
└── tapo_plug.py              # 가습기 플러그 연결
#통신 기능 추가 예정