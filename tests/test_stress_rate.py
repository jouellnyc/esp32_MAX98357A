import board
import audiobusio
import audiocore
import array
import math
import time

# Use your I2S Pins
I2S_BIT_CLOCK   = board.IO5
I2S_WORD_SELECT = board.IO4
I2S_DATA        = board.IO6

audio = audiobusio.I2SOut(I2S_BIT_CLOCK, I2S_WORD_SELECT, I2S_DATA)

def test_at_rate(rate):
    print(f"Testing Sample Rate: {rate} Hz...", end=" ")
    
    # Generate a simple 440Hz tone at the target sample rate
    length = rate // 440
    if length < 2: length = 2 # Prevent divide by zero
    
    sine_wave = array.array("h", [
        int(math.sin(2 * math.pi * i / length) * 5000)
        for i in range(length)
    ])
    
    tone = audiocore.RawSample(sine_wave, sample_rate=rate)
    
    try:
        audio.play(tone, loop=True)
        time.sleep(2) # Play for 2 seconds
        audio.stop()
        print("✅ STABLE")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

# List of common rates to test
test_rates = [8000, 11025, 16000, 22050, 32000, 44100, 48000, 88200, 96000]

print("Starting ESP32-S3 Audio Stress Test")
print("Listen for: clear tone -> static/crackling -> total silence/crash")
print("-" * 40)

for r in test_rates:
    success = test_at_rate(r)
    if not success:
        print(f"\nYour S3's limit is likely around {r} Hz.")
        break
    time.sleep(0.5)

print("-" * 40)
print("Stress test complete.")