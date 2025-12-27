import board

# ============================================
# I2S Audio Configuration
# ============================================
I2S_BIT_CLOCK   = board.D14   # BCLK (GPIO14)
I2S_WORD_SELECT = board.D32   # LRC / WS (GPIO32)
I2S_DATA        = board.D27   # DIN (GPIO27)

"""
This amp's actual behavior is:
GAIN      Connection Volume
Floating  LOUDEST
3.3V      Quieter
GND       Quieter (same as 3.3V)

Some MAX98357A modules (especially clones) behave differently than the datasheet.
What you're seeing makes sense if the GAIN pin has internal pull-up/pull-down resistors that create this behavior.

Your Volume Control Options:

Loudest: Leave GAIN disconnected (floating) ← Use this if you want max volume
Quieter: Connect GAIN to either GND or 3.3V (both seem similar)
"""

