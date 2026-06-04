import tflite_runtime.interpreter as tflite
import cv2
import numpy as np
from PIL import Image
import time
from datetime import datetime
import os

# ── 설정 ───────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model_fp16.tflite")  # 모델 파일 위치
LABELS      = ['발생', '생육', '수확']        # 클래스 이름
DB_PATH     = '/home/pi/mushroom/mushroom/db'
_last_stage = '발생'                         # 단계 초기값

# ── 모델 불러오기 (처음 한 번만) ───────────────────────────
interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details  = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("모델 로딩 완료")


# ── 단계 반환하는 함수     ─────────────────────────────────
def get_current_stage() -> str:
    return _last_stage

# ── 사진 1장 예측하는 함수 ─────────────────────────────────
def predict(image_path):
    # 1. 사진 읽고 전처리
    img = Image.open(image_path).convert('RGB')
    img = img.resize((224, 224))
    img_array = np.array(img, dtype=np.float32) / 255.0
    img_array = np.expand_dims(img_array, axis=0)  # (1, 224, 224, 3)

    # 2. 모델에 넣기
    interpreter.set_tensor(input_details[0]['index'], img_array)

    # 3. 추론 실행 + 시간 측정
    start = time.time()
    interpreter.invoke()
    elapsed_ms = (time.time() - start) * 1000

    # 4. 결과 꺼내기
    output = interpreter.get_tensor(output_details[0]['index'])[0]

    predicted_idx  = np.argmax(output)       # 가장 높은 확률 인덱스
    predicted_label = LABELS[predicted_idx]  # 단계 이름
    confidence      = output[predicted_idx] * 100  # 확률 (%)

    return {
        'stage':      predicted_label,
        'confidence': confidence,
        'elapsed_ms': elapsed_ms,
        'all_probs':  {LABELS[i]: round(float(output[i])*100, 1)
                       for i in range(len(LABELS))}
    }
"""
# ── 카메라로 1분마다 자동 촬영 + 예측 ─────────────────────
def capture_and_predict():
    #cap = cv2.VideoCapture(0)   # 카메라 열기
    global _last_stage

    while True:

        # 사진 찍기
        ret, frame = cap.read()
        if not ret:
            print("카메라 오류")
            break

        # 저장
        timestamp  = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_path = f'/home/pi/mushroom/captures/{timestamp}.jpg'
        cv2.imwrite(image_path, frame)

       
        # 예측
        result = predict(image_path)
        _last_stage = result['stage']

        # 출력
        print(f"\n[{timestamp}]")
        print(f"  현재 단계 : {result['stage']}")
        print(f"  확신도    : {result['confidence']:.1f}%")
        print(f"  추론 시간 : {result['elapsed_ms']:.0f}ms")
        print(f"  전체 확률 : {result['all_probs']}")

        # 학생 D DB에 저장하는 부분 (여기에 DB 저장 코드 연결)
        #save_to_db(timestamp, result)

        # 1분 대기
        time.sleep(60)

    cap.release()
"""
def capture_and_predict():
    global _last_stage

    CAPTURE_DIR = "/home/pi/mushroom/camera/captures"
    # 실제 camera/captures 경로에 맞게 수정

    while True:
        try:
            images = [
                f for f in os.listdir(CAPTURE_DIR)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]

            if not images:
                print("이미지가 없습니다.")
                time.sleep(10)
                continue

            latest = max(
                images,
                key=lambda f: os.path.getmtime(
                    os.path.join(CAPTURE_DIR, f)
                )
            )

            image_path = os.path.join(CAPTURE_DIR, latest)

            # AI 예측
            result = predict(image_path)
            _last_stage = result['stage']

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            print(f"\n[{timestamp}]")
            print(f"사용 이미지 : {latest}")
            print(f"현재 단계 : {result['stage']}")
            print(f"확신도 : {result['confidence']:.1f}%")
            print(f"추론 시간 : {result['elapsed_ms']:.0f}ms")
            print(f"전체 확률 : {result['all_probs']}")

            # save_to_db(timestamp, result)

        except Exception as e:
            print(f"예측 오류: {e}")

        time.sleep(60)

# ── DB 저장 함수 ────────────
def save_to_db(timestamp, result):
    # 예시: SQLite에 저장
    import sqlite3
    conn = db = sqlite3.connect(DB_PATH)
    conn.execute('''
        INSERT INTO growth_log
        (timestamp, stage, confidence, elapsed_ms)
        VALUES (?, ?, ?, ?)
    ''', (timestamp, result['stage'],
          result['confidence'], result['elapsed_ms']))
    conn.commit()
    conn.close()

# ── 실행 ───────────────────────────────────────────────────
if __name__ == '__main__':
    capture_and_predict()
