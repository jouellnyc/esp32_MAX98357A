# ESP32-S3 Audio Player with SD Card

A complete audio player implementation using CircuitPython.

<img width="620" height="410" alt="image" src="https://github.com/user-attachments/assets/1f45a891-cf0c-4fd3-8cee-0005e7e165b6" />

<img width="620" height="410" alt="Thonny" src="https://github.com/user-attachments/assets/ac42a89d-103b-402d-8637-a6717cc6a9fc" />

## Hardware Requirements

* [Waveshare RP2350-Plus](https://www.waveshare.com/rp2350-plus.htm) (Recommended) OR
* Adafruit Huzzah (Recommended See below) OR
* [ESP32-S3-DevKitC-1-N8R8 Development Board](https://www.amazon.com/dp/B09MHP42LY) (See below - not recomended in the end, but did partially work)
* [MAX98357A I2S Audio Amplifier Breakout](https://www.amazon.com/dp/B0B4J93M9N)
* [HiLetgo SD Card Module](https://www.amazon.com/dp/B07BJ2P6X6) (or similar SPI SD card reader)
* [4-8 ohm Speaker](https://www.adafruit.com/product/1669)
* Jumper wires
* Breadboard
* Two 100-470uF electrolytic capacitors (recommended for stability)
* Micro SD card (2GB-32GB, formatted as FAT32)

Author's Note:

- I did the same with an [Adafruit Metro ESP32-S3](https://www.adafruit.com/product/5500) with 16 MB Flash 8 MB PSRAM.  
- That worked flawlessly using it's internal sd and did not need any 100 uF capacitors.
- I leaned on Claude Ai  sd card help -  See [link](https://github.com/jouellnyc/hiletgo_sdcard_reader) to save hours of tshoots.
- These are not professional sound systems, your experience will be varied!

## Software Requirements

- **Adafruit CircuitPython** (tested on 10.0.3)
- Download from: https://circuitpython.org/board/espressif_esp32s3_devkitc_1_n8r8/
- I would not suggest using MicroPython with an sdcard reader with level shifters.

### Required CircuitPython Libraries

**No external libraries required!** This project uses only built-in CircuitPython modules:
- `board` - GPIO pin definitions
- `busio` - SPI and I2S communication
- `sdcardio` - SD card support (built-in)
- `storage` - File system mounting
- `audiobusio` - I2S audio output
- `audiocore` - WAV file support
- `audiomp3` - MP3 file support (built-in)

## Wiring Diagram

### MAX98357A Audio Amplifier

(see audio_config.py for each device)

| MAX98357A Pin | ESP32 Pin | Notes |
|---------------|--------------|-------|
| LRC (LRCLK)   | GPIO X       | Word Select |
| BCLK          | GPIO Y       | Bit Clock |
| DIN           | GPIO Z       | Data Input |
| GAIN          | 5V           | Maximum volume (15dB) |
| SD            | 5V           | Shutdown control (HIGH = ON) |
| VIN           | 5V           | Power input |
| GND           | GND          | Ground |

**Speaker Connection:**
- Connect speaker wires to **+** and **-** terminals on MAX98357A
- Use 4-8 ohm speaker (NOT headphones)

### SD Card Module

(see sd_config.py for each device)

| SD Module Pin | ESP32-S3 Pin | Notes |
|---------------|--------------|-------|
| CS            | GPIO X      | Chip Select |
| MOSI (DI)     | GPIO Y      | Data In |
| MISO (DO)     | GPIO Z      | Data Out |
| SCK (CLK)     | GPIO Q      | Clock |
| VCC           | 5V           | **IMPORTANT: Must use 5V** |
| GND           | GND          | Ground |

**Note:** The HiLetgo SD card module has an onboard voltage regulator (AMS1117) that converts 5V to 3.3V for the SD card. Using 3.3V may cause initialization failures.

### Power Stability (Critical)

Add 100-470µF electrolytic capacitors for stable operation:

1. **SD Card Power Filtering:**
   - Place capacitor between SD module VCC and GND
   - Positive (+) leg to VCC, negative (-) leg to GND
   - Position as close to the module as possible

2. **Audio Amplifier Power Filtering:**
   - Place capacitor between MAX98357A VIN and GND
   - Positive (+) leg to VIN, negative (-) leg to GND

**Warning:** Electrolytic capacitors are polarized. Connecting them backwards can cause damage or failure. The longer leg is positive (+), and the negative side often has a stripe.

### Complete Breadboard Layout

```
Power Rails:

  5V  ─┬─── SD Card VCC (with 100µF cap to GND)
       ├─── MAX98357A VIN (with 100µF cap to GND)
       └─── MAX98357A SD

  An external spliced usb cable would work here...

  GND ─┬─── SD Card GND
       ├─── MAX98357A GND
       ├─── MAX98357A GAIN (or left floating or set to 3.3V ) (see audio_config.py for GAIN settings) 
       └─── ESP32-S3 GND
       └─── External 5V GND

Signals (Dev Kit C example) 
  ESP32           MAX98357A
    GPIO 4    ───►   LRC
    GPIO 5    ───►   BCLK
    GPIO 6    ───►   DIN

  ESP32            SD Card
    GPIO 16   ───►   CS
    GPIO 11   ───►   MOSI
    GPIO 13   ───►   MISO
    GPIO 12   ───►   SCK
```

## SD Card Preparation

1. **Format the SD card:**
   - Use FAT32 file system
   - Maximum 32GB recommended for best compatibility
   - Use official SD Card Formatter: https://www.sdcard.org/downloads/formatter/

2. **Add audio files:**
   - Supported formats: WAV, MP3
   - Recommended: 16-bit PCM WAV files
   - Sample rates: 22050 Hz or 44100 Hz
   - Mono or Stereo

3. **Convert audio files (if needed):**
   ```bash
   # Convert MP3 to WAV (most reliable)
   ffmpeg -i input.mp3 -ar 22050 -ac 2 output.wav
   
   # Convert to mono for smaller file size
   ffmpeg -i input.mp3 -ar 22050 -ac 1 output.wav
   ```

## Software Installation

1. **Install CircuitPython:**
   - Download UF2 file for ESP32-S3-DevKitC-1-N8R8
   - Hold BOOT button, press RESET, release both
   - Drag UF2 file to USB drive that appears
   - Board will reboot with CIRCUITPY drive

2. **Copy the project files to CIRCUITPY drive:**
   ```
   CIRCUITPY/
   ├── code.py              # Main audio player (rename play.py to code.py for auto-run)
   ├── audio_config.py      # Hardware pin configuration
   └── (optional) audio files on root or use SD card
   ```

3. **No additional libraries needed!** All required modules are built into CircuitPython 9.0.0+

4. **Board will auto-run** `code.py` on power-up or reset

## Usage

### Basic Functions

```python
# Play a specific file
play('mysong.wav')

# Play all files in sequence
play_all()

# Shuffle play
play_all(shuffle=True)

# Repeat playlist
play_all(repeat=True)

# Play track by number
play_track(3)

# List all available tracks
list_tracks()

# Stop playback
stop()

# Check if playing
is_playing()
```

### File Organization

Files can be stored in two locations:
- **Internal storage:** `/` (CIRCUITPY drive, limited space)
- **SD card:** `/sd/` (larger capacity)

The player automatically searches both locations.

## Troubleshooting

### SD Card Not Detected

**Symptom:** "timeout waiting for v2 card" or SD mount fails

**Solutions:**
1. Verify VCC is connected to **5V** (not 3.3V)
2. Check all wiring connections
3. Try different CS pin (GPIO 14, 15, 17, 18, or 21)
4. Reduce baudrate: `baudrate=250000`
5. Format SD card as FAT32
6. Try a different SD card (some cards have compatibility issues)
7. Use shorter wires (under 6 inches ideal)

**Test SD card detection:**
```python
import os
print(os.listdir("/sd"))
```

### SD Card Becomes Unstable During Playback

**Symptom:** Files disappear, "Input/output error" during playback

**Solutions:**
1. **Add 100µF capacitors** (this helped a lot!)
   - One between SD card VCC and GND
   - One between MAX98357A VIN and GND
2. Use external 5V power supply (2A minimum) (most effective solution) (not shown - added later)
3. Lower SD card baudrate to 250000
4. Ensure all grounds are connected together
5. Use higher quality USB power adapter

**Test stability:**
```python
# Monitor SD card during audio playback
import time
while True:
    print(len(os.listdir("/sd")))
    time.sleep(0.5)
```

### No Audio Output

**Symptom:** Audio plays but no sound from speaker

**Solutions:**
1. **Verify SD pin is HIGH:**
   - Must be connected to VCC (5V or 3.3V)
   - If floating or LOW, amp is in shutdown mode
2. Check GAIN pin is connected (GND=9dB, Float=12dB, VCC=15dB)
3. Verify speaker is 4-8 ohm (not headphones)
4. Test speaker with 1.5V battery (should hear pop/click)
5. Check all I2S connections (BCLK, LRC, DIN)
6. Verify VIN has 5V power
7. Try different GPIO pins for I2S

**Test with tone generator:**
```python
import board
import audiobusio
import audiocore
import array
import math

audio = audiobusio.I2SOut(
    bit_clock=board.IO5,
    word_select=board.IO4,
    data=board.IO6
)

def generate_tone(freq=440, duration=2):
    samples = array.array("H", [0] * (22050 * duration))
    for i in range(len(samples)):
        samples[i] = int((math.sin(2 * math.pi * freq * i / 22050) + 1) * 32767)
    return audiocore.RawSample(samples, sample_rate=22050)

audio.play(generate_tone())
```

### MP3 Playback Issues

**Symptom:** "Input/output error" when playing MP3 files

**Solutions:**
1. Convert MP3 files to WAV format (most reliable)
2. Re-encode MP3 with simpler settings:
   ```bash
   ffmpeg -i input.mp3 -ar 22050 -ac 1 -b:a 128k output.mp3
   ```
3. Use 22050 Hz sample rate instead of 44100 Hz
4. Convert stereo to mono

**Note:** CircuitPython's MP3 decoder can be finicky with certain encodings. WAV files are recommended for best compatibility.

### Audio Quality Issues

**Symptom:** Distortion, crackling, or low volume

**Solutions:**
1. Adjust GAIN pin connection:
   - GND = 9dB (quietest)
   - Float = 12dB (default)
   - VCC = 15dB (loudest)
2. Reduce volume in code (scale samples to 0.5-0.8)
3. Use higher quality audio files
4. Ensure VIN has stable 5V
5. Add capacitors for power filtering
6. Check speaker impedance matches (4-8 ohm)

### Power Supply Issues

**Symptom:** Inconsistent behavior, resets, brownouts

**Solutions:**
1. Use 2A+ USB power adapter (not computer USB)
2. Add 100-470µF capacitors near power-hungry components
3. Use external 5V supply for SD card and audio amp
4. Ensure common ground connection
5. Check for voltage drop with multimeter

## Performance Optimization

### Recommended Audio Formats

**Best compatibility:**
- Format: 16-bit PCM WAV
- Sample rate: 22050 Hz
- Channels: Mono
- File size: ~2.5 MB per minute

**Higher quality:**
- Format: 16-bit PCM WAV
- Sample rate: 44100 Hz
- Channels: Stereo
- File size: ~10 MB per minute

### Memory Considerations
The ESP32-S3-DevKitC-1-N8R8 has:
- 8MB Flash (CIRCUITPY storage)
- 8MB PSRAM (for large buffers)
(but again was not reliable in the end)

For large music libraries, use SD card storage.

## A word about the Waveshare RP2350-Plus 
- It worked flawlessly and easily with the HiLetGo SD carder Reader.
- It's sound was the best overall and could set it's spi speed to the highest working speed.
- Overall, highly recommend for this project! (Did not try it until after I named the repo!)
- This board was able to reliably play WAVs at 44100Hz, 2ch, 16bit

## A word about the Adafruit HUZZAH32 – ESP32 Feather Board
You can play music with the same general setup (different pins obviously) using this board BUT, in my experience:

- Although the ESP32 Feather has limited total ram (512k) compared to newer ESP32-S3 boards (4MB+), it is very stable with the Hiletgo SD card reader.
- In the end it performed better than the DEV KIT C (which crashed/hung too often) with the Hiletdo sd card reader (5V or even 3.X Volts). 
- But a worse performance than the Waveshare RP2350
- If you want to try with Adafruit, buy this one with 2MB psram https://www.adafruit.com/product/5900 (not tested, but very likely more capable)
- I.E Don't buy the one with only 512 total 'local' ram: https://www.adafruit.com/product/3591 (but that's the one I used here)

### What to avoid ... Generally 
* 44.1kHz stereo WAV - Causes "jackhammer" effect (buffer underruns)
* High bitrate MP3s - Decoder struggles, causes stuttering
* Loading files to RAM - "memory allocation failed" errors (even for small files)
* Multiple simultaneous file handles - Causes SD "corruption"

### What WORKS Perfectly
**Audio Format: 16kHz mono WAV files (and most 22kHz)**

```bash
# Convert audio to ESP32-friendly format
ffmpeg -i input.mp3 -ar 16000 -ac 1 output_16khz.wav
ffmpeg -i input.mp3 -ar 22050 -ac 1 output_16khz.wav
```

See the updated play.py that filters for lower quality wavs.


## SD Card Support

This music player supports reading audio files from SD cards using the SPI interface.

### Important: Use sdcard_helper

CircuitPython's `sdcardio` module appears to have timing issues that can cause:
- Empty directories after soft reboot
- Files appearing only on second access
- Device hangs during playback

**Solution:** This project uses the `sdcard_helper.py` module which handles  initialization with settling time and rate limiting.

### Audio Files on SD Card

**Supported formats:**
- **MP3:** Any bitrate, mono or stereo
- **WAV:** 16-bit PCM, 22050Hz or 44100Hz recommended for best quality (BUT see above about what actually works well)

Place audio files in the root of your SD card (`/sd/`) or subdirectories.

```python

# Play all files (scans internal storage AND SD card)
play_all()

# Play all lower quality files 
play.play_all_low()
```

** For more SD troubleshooting, and details, see  [hiletgo_sdcard_reader repository](https://github.com/jouellnyc/hiletgo_sdcard_reader) **


## Additional Resources
- **CircuitPython Documentation:** https://docs.circuitpython.org/
- **MAX98357A Datasheet:** https://datasheets.maximintegrated.com/en/ds/MAX98357A-MAX98357B.pdf
- **Audio conversion with ffmpeg:** https://ffmpeg.org/
- **Adafruit MP3 Page** - https://learn.adafruit.com/mp3-playback-with-circuitpython/mp3-capabilities-by-microcontroller
- **Adafruit SD Page** - https://learn.adafruit.com/adafruit-microsd-spi-sdio/adafruit-circuitpython-sd

## License
This project is provided as-is for educational and personal use.
