"""
sd_config.py
Universal configuration for Huzzah32 (ESP32) and DevKit-C (ESP32-S3)
"""

import board

# Detect board identity
board_type = board.board_id
print(f"--- SD Config: Detected {board_type} ---")

if "huzzah32" in board_type and "s3" not in board_type:
    # ============================================
    # ESP32 HUZZAH (Original) Pins
    # ============================================
    SD_SCK  = board.SCK   # GPIO 5
    SD_MOSI = board.MOSI  # GPIO 18
    SD_MISO = board.MISO  # GPIO 19
    SD_CS   = board.A5    # GPIO 4
    SD_BAUDRATE = 4_000_000

else:
    # ============================================
    # ESP32-S3 DevKit-C Pins
    # ============================================
    SD_SCK  = board.IO12
    SD_MOSI = board.IO11
    SD_MISO = board.IO13
    SD_CS   = board.IO16
    # Note: Using 100k for stability as per your DevKit-C working config
    SD_BAUDRATE = 100_000 

# ============================================
# Shared Settings
# ============================================
SD_MOUNT     = "/sd"
SD_TEST_FILE = SD_MOUNT + "/test.txt"