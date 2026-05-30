## 📖 프로젝트 개요

- ~~는 센서와 카메라, 그리고 AI를 결합해 식물의 현재 생장 단계를 자동으로 판별하고, 단계별 최적 환경을 유지해주는 자동화 재배 시스템입니다.

- 사용자가 직접 환경을 조절하지 않아도, 시스템이 버섯의 상태를 스스로 파악하고 환풍기·가습기·LED 조명을 제어하여 최적의 성장 환경을 만들어냅니다.
---

## 🛠  주요 기능
- 온도,습도,이산화 탄소 등의 수치를 파악함
- 

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
# 시스템 패키지
sudo apt update && sudo apt install -y python3-pip libcamera-apps

# Python 패키지
pip3 install -r requirements.txt
```

### 2. 하드웨어 설정

```bash
# I2C, SPI, Camera 인터페이스 활성화
sudo raspi-config
# → Interface Options → I2C / SPI / Camera → Enable
```

### 3. 설정 파일 구성

```bash
cp config/settings.example.yaml config/settings.yaml
# settings.yaml 에서 센서 핀 번호, 모델 경로 등 환경에 맞게 수정
```

### 4. 실행

```bash
python3 main.py
```

---