import os
import audiocore

def chk(filename):
    filepath = f'/sd/{filename}'  # Add the /sd/ prefix!
    try:
        with open(filepath, 'rb') as f:
            wav = audiocore.WaveFile(f)
            print(f"{filename:30s} | {wav.sample_rate:5d}Hz | {wav.bits_per_sample:2d}bit | {wav.channel_count}ch")
    except Exception as e:
        print(f"{filename:30s} | ERROR: {e}")

# Check all files
files = os.listdir('/sd')
for x in files:
    chk(x)