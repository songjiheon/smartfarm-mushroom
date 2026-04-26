RELAY_ACTIVE_LOW = True

class PinConfig:
   DHT11_DATA = 17
   CDS_DO = 27

   HUMIDIFIER = 5
   FAN = 6
   LED = 13

class ADSConfig:
   CHANNEL = 0
   GAIN = 1

class CdSConfig:
   RAW_MIN = 0
   RAW_MAX = 26000
   LUX_MIN = 0.0
   LUX_MAX = 1000.0

MUSHROOM_PROFILES = {
   "느타리":{
      "발생":{
         "temp_min":21.0, "temp_max":23.0, "temp_target":22.0,
         "humi_min":53.0, "humi_max":60.0,
         "co2_min":3500, "co2_max":4000,
         "lux_mode":"flash",
         "light_cycle_hour":1,
         "light_on_sec":6,
      },
      
      "생육":{
         "temp_min":16.0, "temp_max":21.0, "temp_target":18.0,
         "humi_min":75.0, "humi_max":85.0,
         "co2_target":1500, 
         "lux_mode":"cycle",
         "light_cycle_hour":1,
         "light_on_min":20,
      },
      "수확":{
         "temp_min": 12.0, "temp_max": 16.0,
            "humi_min": 60.0, "humi_max": 70.0,
            "co2_target": 1000,
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


