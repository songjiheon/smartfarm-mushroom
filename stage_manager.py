import json
import os
from datetime import date
from enum import Enum

STATE_FILE = "stage_state.json"

class Stage(Enum):
    PINNING = "발생"
    GROWING = "생육"
    HARVEST = "수확"

STAGE_DAYS = {
    Stage.PINNING : (1,  5),
    Stage.GROWING : (6,  12),
    Stage.HARVEST : (13, 9999),
}

class StageManager:

    def __init__(self, state_file: str = STATE_FILE):
        self._state_file = state_file
        self._start_date : date = None

    def start(self, force: bool = False) -> None:
        if os.path.isfile(self._state_file) and not force:
            self._load()
            print(f"[StageManager] 기존 시작일 로드: {self._start_date}")
        else:
            self._start_date = date.today()
            self._save()
            print(f"[StageManager] 발생 시작: {self._start_date}")

    def elapsed_days(self) -> int:
        if self._start_date is None:
            raise RuntimeError("start()를 먼저 호출하세요.")
        return (date.today() - self._start_date).days + 1

    def current_stage(self) -> Stage:
        days = self.elapsed_days()
        for stage, (start, end) in STAGE_DAYS.items():
            if start <= days <= end:
                return stage
        return Stage.HARVEST

    def status(self) -> dict:
        days  = self.elapsed_days()
        stage = self.current_stage()
        return {
            "start_date"   : str(self._start_date),
            "elapsed_days" : days,
            "stage"        : stage.value,
            "next_stage"   : self._next_stage_info(stage, days),
        }

    def _next_stage_info(self, stage: Stage, days: int) -> str:
        if stage == Stage.PINNING:
            return f"생육 전환까지 {6 - days}일"
        elif stage == Stage.GROWING:
            return f"수확 전환까지 {6 - days}일"
        else:
            return "수확 단계"

    def print_status(self) -> None:
        s = self.status()
        print(f"\n[StageManager]")
        print(f"  시작일    : {s['start_date']}")
        print(f"  경과 일수 : {s['elapsed_days']}일차")
        print(f"  현재 단계 : {s['stage']}")
        print(f"  다음 단계 : {s['next_stage']}")

    def _save(self) -> None:
        with open(self._state_file, "w") as f:
            json.dump({"start_date": str(self._start_date)}, f)

    def _load(self) -> None:
        with open(self._state_file) as f:
            data = json.load(f)
        self._start_date = date.fromisoformat(data["start_date"])

    # TODO: AI 판단 추가 예정
    def _check_ai(self, image_path: str) -> Stage:
        raise NotImplementedError("AI")

if __name__ == "__main__":
    sm = StageManager()
    sm.start()
    sm.print_status()
