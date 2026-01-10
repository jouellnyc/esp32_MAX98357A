"""
sd_config.py
Universal configuration for RP2350, ESP32, and ESP32-S3
"""

import board

# Detect board identity
board_type = board.board_id
print(f"--- SD Config: Detected {board_type} ---")

# ============================================
# RP2350-Plus (Waveshare) - YOUR NEW BOARD
# ============================================
if "rp2350" in board_type:
    SD_SCK  = board.GP18
    SD_MOSI = board.GP19
    SD_MISO = board.GP16
    SD_CS   = board.GP17
    # 12MHz: The "Goldilocks" speed we found for audio stability
    SD_BAUDRATE = 12_000_000

# ============================================
# ESP32 HUZZAH (Original) Pins
# ============================================
elif "huzzah32" in board_type and "s3" not in board_type:
    SD_SCK  = board.SCK   # GPIO 5
    SD_MOSI = board.MOSI  # GPIO 18
    SD_MISO = board.MISO  # GPIO 19
    SD_CS   = board.A5    # GPIO 4
    SD_BAUDRATE = 8_000_000
    
# ============================================
# ESP32-S3 DevKit-C Pins
# ============================================
elif "s3" in board_type:
    SD_MISO = board.IO11
    SD_MOSI = board.IO12
    SD_SCK  = board.IO13
    SD_CS   = board.IO14
    SD_BAUDRATE = 4_000_000

elif "s2" in board_type:
    SD_SCK  = board.IO12
    SD_MOSI = board.IO11
    SD_MISO = board.IO13
    SD_CS   = board.IO14
    SD_BAUDRATE = 4_000_000
    
# ============================================
# Fallback / Default (Just in case)
# ============================================
else:
    print("Warning: Unknown board. Using default SPI pins.")
    SD_SCK  = board.SCK
    SD_MOSI = board.MOSI
    SD_MISO = board.MISO
    SD_CS   = board.D5
    SD_BAUDRATE = 1_000_000

print(f"--- SD Config: using {SD_BAUDRATE} SD_BAUDRATE ---")
# ============================================
# Shared Settings
# ============================================
SD_MOUNT     = "/sd"
SD_TEST_FILE = SD_MOUNT + "/test.txt"