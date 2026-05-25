"""
Tapo 플러그(P110)을 통해 가습기 전원 제어
.env에서 IP/비밀번호/계정 읽어옴
"""

import asyncio
import os
from dotenv import load_dotenv
from tapo import ApiClient

load_dotenv()

class TapoHumidifier:
    #.env에서 계정 정보 읽어오기
    def __init__(self):
        self._email      = os.getenv("TAPO_EMAIL")
        self._password   = os.getenv("TAPO_PASSWORD")
        self._ip         = os.getenv("DEVICE_IP")
        self._device     = None
        self._is_on      = False

    #Tapo API 초기화 및 연결
    async def setup(self):
        client = ApiClient(self._email, self._password)
        self._device = await client.p110(self._ip)
        await self._device.off()
        print("tapo 초기화")

    #플러그 ON
    async def turn_on(self):
        if not self._is_on:
            await self._device.on()
            self._is_on = True
            print("가습기 ON")

    #플러그 OFF
    async def turn_off(self):
        if self._is_on:
            await self._device.off()
            self._is_on = False
            print("가습기 OFF")

    async def apply(self, should_on: bool):
        if should_on:
            await self.turn_on()
        else:
            await self.turn_off()

    async def cleanup(self):
        await self.turn_off()
        print("[TapoHumidifier] 정리 완료")
        
