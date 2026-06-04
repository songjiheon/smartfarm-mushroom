from flask import Flask, jsonify, request, send_from_directory
import os
import time
import traceback

from sensor.DHT11 import DHT11Sensor
from sensor.CDS import CdSSensor
from sensor.MHZ14A import MHZ14ASensor

from gpiozero import OutputDevice
from config import PinConfig

try:
    from config import RELAY_ACTIVE_LOW
except ImportError:
    RELAY_ACTIVE_LOW = True

try:
    from stage_manager import StageManager
except Exception:
    StageManager = None

try:
    from camera.capture import CameraCapture
except Exception:
    CameraCapture = None


app = Flask(__name__)

# 센서 객체
dht_sensor = None
cds_sensor = None
co2_sensor = None

# 단계 관리자
stage_manager = None
manual_stage = None

# 카메라 객체
camera_capture = None
last_camera_path = None
last_capture_time = 0
CAMERA_CAPTURE_INTERVAL = 5

# 카메라 이미지 저장 폴더
CAMERA_DIR = os.path.join(os.path.dirname(__file__), "camera", "captures")

# 실제 제어 장치
actuators = {}

# 앱에 보여줄 장치 상태
# cooler, led는 앱 JSON 구조 때문에 남겨두지만 실제 제어하지 않음
device_state = {
    "humidifier": False,
    "fan": False,
    "cooler": False,
    "led": False,
}

# 센서 읽기 실패 시 마지막 정상값 유지
last_sensor_data = {
    "temperature": 0.0,
    "humidity": 0.0,
    "co2": 0,
    "light": 0,
}

STAGE_TO_APP = {
    "발생": "발생단계",
    "생육": "생육단계",
    "수확": "수확단계",
}


def setup_actuators():
    global actuators

    active_high = not RELAY_ACTIVE_LOW

    try:
        actuators["humidifier"] = OutputDevice(
            PinConfig.HUMIDIFIER,
            active_high=active_high,
            initial_value=False
        )

        actuators["fan"] = OutputDevice(
            PinConfig.FAN,
            active_high=active_high,
            initial_value=False
        )

        print("[AppServer] 가습기/환기팬 제어 핀 초기화 완료")

    except Exception as e:
        actuators = {}
        print(f"[AppServer] 장치 제어 핀 초기화 실패: {e}")


def setup_hardware():
    global dht_sensor, cds_sensor, co2_sensor
    global stage_manager, camera_capture

    print("[AppServer] 하드웨어 초기화 시작")

    # 단계 관리자 초기화
    if StageManager is not None:
        try:
            stage_manager = StageManager()
            stage_manager.start()
            print("[AppServer] StageManager 초기화 완료")
        except Exception as e:
            stage_manager = None
            print(f"[AppServer] StageManager 초기화 실패: {e}")

    # DHT11 온습도 센서 초기화
    try:
        dht_sensor = DHT11Sensor()
        dht_sensor.setup()
    except Exception as e:
        dht_sensor = None
        print(f"[AppServer] DHT11 초기화 실패: {e}")

    # CdS 조도 센서 초기화
    try:
        cds_sensor = CdSSensor()
        cds_sensor.setup()
    except Exception as e:
        cds_sensor = None
        print(f"[AppServer] CdS 초기화 실패: {e}")

    # MH-Z14A CO2 센서 초기화
    try:
        co2_sensor = MHZ14ASensor()
        co2_sensor.setup()
    except Exception as e:
        co2_sensor = None
        print(f"[AppServer] CO2 초기화 실패: {e}")

    # 카메라 초기화
    if CameraCapture is not None:
        try:
            camera_capture = CameraCapture()
            camera_capture.setup()
            print("[AppServer] 카메라 초기화 완료")
        except Exception as e:
            camera_capture = None
            print(f"[AppServer] 카메라 초기화 실패: {e}")

    # 가습기 / 환기팬 제어 핀 초기화
    setup_actuators()

    print("[AppServer] 하드웨어 초기화 완료")


def get_growth_stage():
    if manual_stage is not None:
        return manual_stage

    if stage_manager is not None:
        try:
            stage_value = stage_manager.current_stage().value
            return STAGE_TO_APP.get(stage_value, stage_value)
        except Exception:
            pass

    return "생육단계"


def read_sensors():
    global last_sensor_data

    temp = None
    humi = None
    lux = None
    co2_value = None

    try:
        if dht_sensor is not None:
            temp, humi = dht_sensor.read()
    except Exception as e:
        print(f"[AppServer] DHT11 읽기 실패: {e}")

    try:
        if cds_sensor is not None:
            lux, raw = cds_sensor.read()
    except Exception as e:
        print(f"[AppServer] CdS 읽기 실패: {e}")

    try:
        if co2_sensor is not None:
            co2_value = co2_sensor.read()
    except Exception as e:
        print(f"[AppServer] CO2 읽기 실패: {e}")

    if temp is not None:
        last_sensor_data["temperature"] = float(temp)

    if humi is not None:
        last_sensor_data["humidity"] = float(humi)

    if lux is not None:
        last_sensor_data["light"] = int(lux)

    if co2_value is not None:
        last_sensor_data["co2"] = int(co2_value)

    return last_sensor_data


def capture_latest_image_if_needed():
    global last_camera_path, last_capture_time

    if camera_capture is None:
        return

    now = time.time()

    if last_camera_path is not None and now - last_capture_time < CAMERA_CAPTURE_INTERVAL:
        return

    try:
        last_camera_path = camera_capture.capture()
        last_capture_time = now
        print(f"[AppServer] 최신 이미지 촬영 완료: {last_camera_path}")
    except Exception as e:
        print(f"[AppServer] 카메라 촬영 실패: {e}")


def get_latest_camera_image_url():
    capture_latest_image_if_needed()

    if not os.path.isdir(CAMERA_DIR):
        return None

    images = [
        f for f in os.listdir(CAMERA_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    if not images:
        return None

    latest = max(
        images,
        key=lambda f: os.path.getmtime(os.path.join(CAMERA_DIR, f))
    )

    return f"{request.host_url.rstrip('/')}/api/camera/{latest}"


def apply_device_control(device, value):
    if device not in ["humidifier", "fan"]:
        return False

    if device not in actuators:
        return False

    if value:
        actuators[device].on()
    else:
        actuators[device].off()

    print(f"[AppServer] 실제 장치 제어: {device} = {'ON' if value else 'OFF'}")
    return True


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "Smart Mushroom App Server",
        "status": "running",
    })


@app.route("/api/camera/<filename>", methods=["GET"])
def camera_image(filename):
    return send_from_directory(CAMERA_DIR, filename)


@app.route("/api/status", methods=["GET"])
def status():
    try:
        sensor = read_sensors()

        return jsonify({
            "temperature": sensor["temperature"],
            "humidity": sensor["humidity"],
            "co2": sensor["co2"],
            "light": sensor["light"],
            "growth_stage": get_growth_stage(),
            "disease_status": "정상",
            "ai_result": "라즈베리파이 실제 센서값 수신 중",
            "system_status": "정상",
            "humidifier": device_state["humidifier"],
            "fan": device_state["fan"],
            "cooler": device_state["cooler"],
            "led": device_state["led"],
            "camera_image_url": get_latest_camera_image_url(),
            "timestamp": time.time(),
        })

    except Exception as e:
        print("[AppServer] /api/status 오류")
        traceback.print_exc()

        return jsonify({
            "temperature": last_sensor_data["temperature"],
            "humidity": last_sensor_data["humidity"],
            "co2": last_sensor_data["co2"],
            "light": last_sensor_data["light"],
            "growth_stage": get_growth_stage(),
            "disease_status": "확인 필요",
            "ai_result": f"서버 오류: {str(e)}",
            "system_status": "주의",
            "humidifier": device_state["humidifier"],
            "fan": device_state["fan"],
            "cooler": device_state["cooler"],
            "led": device_state["led"],
            "camera_image_url": None,
            "timestamp": time.time(),
        })


@app.route("/api/control", methods=["POST"])
def control():
    body = request.get_json()

    device = body.get("device")
    value = bool(body.get("value"))

    if device not in device_state:
        return jsonify({
            "result": "error",
            "message": "unknown device",
        }), 400

    success = apply_device_control(device, value)

    if success:
        device_state[device] = value

    return jsonify({
        "result": "ok",
        "device": device,
        "value": device_state[device],
        "applied": success,
    })


@app.route("/api/settings", methods=["POST"])
def settings():
    global manual_stage

    body = request.get_json()
    stage = body.get("growth_stage")

    if stage in ["발생단계", "생육단계", "수확단계"]:
        manual_stage = stage

    print(f"[AppServer] 설정 요청 수신: {body}")

    return jsonify({
        "result": "ok",
        "growth_stage": manual_stage,
        "settings": body,
    })


if __name__ == "__main__":
    setup_hardware()
    app.run(host="0.0.0.0", port=5001)
