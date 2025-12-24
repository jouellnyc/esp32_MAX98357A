import board

#ESP32 HUZZAH
#https://www.adafruit.com/product/3591
#NOT https://www.adafruit.com/product/5900 !


# ============================================
# I2S Audio Configuration
# ============================================
I2S_BIT_CLOCK   = board.D14   # BCLK (GPIO14)
I2S_WORD_SELECT = board.D32   # LRC / WS (GPIO32)
I2S_DATA        = board.D27   # DIN (GPIO27)
