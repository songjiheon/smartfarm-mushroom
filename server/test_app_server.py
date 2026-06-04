from flask import Flask, jsonify, request
import time

app = Flask(__name__)

device_state = {
    "humidifier": True,
    "fan": True,
    "cooler": False,
    "led": True,
}

current_stage = "생육단계"

stage_data = {
    "발생단계": {
        "temperature": 22.0,
        "humidity": 92,
        "co2": 1200,
        "light": 100,
        "ai_result": "발생단계로 판단됨",
    },
    "생육단계": {
        "temperature": 18.5,
        "humidity": 91,
        "co2": 1500,
        "light": 320,
        "ai_result": "라즈베리파이 서버 연결 테스트 성공",
    },
    "수확단계": {
        "temperature": 14.0,
        "humidity": 65,
        "co2": 700,
        "light": 0,
        "ai_result": "수확 가능 단계로 판단됨",
    },
}

@app.route("/api/status", methods=["GET"])
def status():
    data = stage_data[current_stage]

    return jsonify({
        "temperature": data["temperature"],
        "humidity": data["humidity"],
        "co2": data["co2"],
        "light": data["light"],
        "growth_stage": current_stage,
        "disease_status": "정상",
        "ai_result": data["ai_result"],
        "system_status": "정상",
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
    value = body.get("value")

    if device not in device_state:
        return jsonify({
            "result": "error",
            "message": "unknown device",
        }), 400

    device_state[device] = bool(value)

    return jsonify({
        "result": "ok",
        "device": device,
        "value": device_state[device],
    })

@app.route("/api/settings", methods=["POST"])
def settings():
    global current_stage

    body = request.get_json()
    stage = body.get("growth_stage")

    if stage in stage_data:
        current_stage = stage

    return jsonify({
        "result": "ok",
        "growth_stage": current_stage,
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
