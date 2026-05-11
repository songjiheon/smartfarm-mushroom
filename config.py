RELAY_ACTIVE_LOW = True

class PinConfig:
   DHT11_DATA = 17
   CDS_DO = 27

   HUMIDIFIER = 5
   FAN = 6
   LED = 18


class CdSConfig:
   RAW_MIN = 0
   RAW_MAX = 1023
   LUX_MIN = 0.0
   LUX_MAX = 1000.0

class CO2Config:
    CO2_PORT = "/dev/ttyAMA0"

MUSHROOM_PROFILES = {
   "느타리":{
      "발생":{
         "temp_min":21.0, "temp_max":23.0, "temp_target":22.0,
         "humi_min":90.0, "humi_max":95.0,
         "co2_max":1200, "co2_danger":2000,
         "lux_mode":"flash10",
      },
      
      "생육":{
         "temp_min":16.0, "temp_max":21.0, "temp_target":18.0,
         "humi_min":75.0, "humi_max":85.0,
         "co2_max": 1500, "co2_danger": 2500,
         "lux_mode":"flash20",
      },
      "수확":{
         "temp_min": 12.0, "temp_max": 16.0,
            "humi_min": 60.0, "humi_max": 70.0,
            "co2_max": 1100, "co2_danger": 1100,
            "lux_mode": "off",
      }
   }
}

class LoopConfig:
   SENSOR_INTERVAL = 5
   CAMERA_INTERVAL = 300
   MAX_DHT_ERRORS = 5

class CameraConfig:
   SAVE_DIR = "captures"
   RESOLUTION = (1280,720)
   JPEG_QUALITY = 85

class LogConfig:
   CSV_PATH = "log/smartfarm_log.csv"


