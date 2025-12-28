"""
audio_config.py
Unified I2S Audio configuration for RP2350, ESP32, and ESP32-S3
"""

import board

# Detect board identity
board_type = board.board_id
print(f"--- Audio Config: Detected {board_type} ---")

# ============================================
# RP2350-Plus (Waveshare)
# ============================================
if "rp2350" in board_type:
    I2S_BIT_CLOCK    = board.GP20   
    I2S_WORD_SELECT  = board.GP21  
    I2S_DATA         = board.GP22  

# ============================================
# ESP32 HUZZAH (Original)
# ============================================
elif "huzzah32" in board_type and "s3" not in board_type:
    I2S_BIT_CLOCK    = board.D14   
    I2S_WORD_SELECT  = board.D32   
    I2S_DATA         = board.D27   

# ============================================
# ESP32-S3 DevKit-C
# ============================================
elif "s3" in board_type:
    I2S_BIT_CLOCK    = board.GP20
    I2S_WORD_SELECT  = board.GP21  
    I2S_DATA         = board.GP22  

# ============================================
# Fallback / Default
# ============================================
else:
    print("Warning: Unknown board. Using standard ESP32 fallback pins.")
    I2S_BIT_CLOCK    = board.D14
    I2S_WORD_SELECT  = board.D32
    I2S_DATA         = board.D27