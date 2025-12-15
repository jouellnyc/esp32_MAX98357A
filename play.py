import time
import os

import board
import busio
import sdcardio
import storage
import audiobusio
import audiocore
import audiomp3

import audio_config
import sd_config

print("=" * 50)
print("ESP32-S3 Music Player")
print("=" * 50)

# ============= SD CARD SETUP =============
print("\n[1/3] Checking for SD card...")

SD_AVAILABLE = False

try:
    # Initialize SPI for SD card (ESP32-S3 pins)
    spi = busio.SPI(clock=sd_config.SD_SCK, MOSI=sd_config.SD_MOSI, MISO=sd_config.SD_MISO)

    # Mount SD card (CS on GPIO 16, needs 5V!)
    sd = sdcardio.SDCard(spi, sd_config.SD_CS, baudrate=sd_config.SD_BAUDRATE)
    vfs = storage.VfsFat(sd)
    storage.mount(vfs, "/sd")

    SD_AVAILABLE = True
    print("✓ SD card mounted successfully!")

except Exception as e:
    print(f"⚠ No SD card detected (this is OK!)")
    print(f"  Will use internal storage instead")

# ============= AUDIO SETUP (MAX98357A) =============
print("\n[2/3] Initializing audio...")

audio = audiobusio.I2SOut(
    bit_clock=audio_config.I2S_BIT_CLOCK,
    word_select=audio_config.I2S_WORD_SELECT,
    data=audio_config.I2S_DATA,
)
 

print("✓ Audio initialized!")

# ============= MUSIC LIBRARY =============

def get_audio_files(directory="/"):
    """Get all audio files from specified directory"""
    audio_files = []

    try:
        for filename in os.listdir(directory):
            # Skip system files and directories
            if filename.startswith('.') or filename == 'sd':
                continue

            filepath = f"{directory}/{filename}" if directory != "/" else f"/{filename}"

            # Check if it's an audio file
            if filename.lower().endswith(('.wav', '.mp3')):
                audio_files.append(filepath)

        # Sort alphabetically
        audio_files.sort()

    except Exception as e:
        print(f"Error reading directory: {e}")

    return audio_files

def get_all_audio_files():
    """Get audio files from both internal and SD card"""
    all_files = []

    # Get files from internal storage
    internal_files = get_audio_files("/")
    if internal_files:
        print(f"  Found {len(internal_files)} file(s) on internal storage")
        all_files.extend(internal_files)

    # Get files from SD card if available
    if SD_AVAILABLE:
        sd_files = get_audio_files("/sd")
        if sd_files:
            print(f"  Found {len(sd_files)} file(s) on SD card")
            all_files.extend(sd_files)

    return all_files

def play_file(filepath):
    """Play a single audio file"""
    try:
        filename = filepath.split('/')[-1]
        location = "SD card" if filepath.startswith("/sd/") else "internal"
        print(f"\n♪ Playing: {filename} ({location})")

        is_mp3 = filepath.lower().endswith('.mp3')

        with open(filepath, "rb") as f:
            if is_mp3:
                sound = audiomp3.MP3Decoder(f)
                print(f"  Format: MP3, {sound.sample_rate}Hz, {sound.channel_count}ch")
            else:
                sound = audiocore.WaveFile(f)
                print(f"  Format: WAV, {sound.sample_rate}Hz, {sound.channel_count}ch, {sound.bits_per_sample}bit")

            audio.play(sound)

            # Wait for playback with progress indicator
            start_time = time.monotonic()
            try:
                while audio.playing:
                    elapsed = int(time.monotonic() - start_time)
                    print(f"  Playing... {elapsed}s", end='\r')
                    time.sleep(0.1)

                print(f"  ✓ Finished ({elapsed}s)                ")
                return True
            except KeyboardInterrupt:
                audio.stop()
                print(f"\n  ⏹ Stopped at {elapsed}s                ")
                #raise

    except KeyboardInterrupt:
        raise
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def play_all(shuffle=False, repeat=False):
    """Play all audio files"""
    files = get_all_audio_files()

    if not files:
        print("\n✗ No audio files found!")
        print("\n📁 To add files:")
        if SD_AVAILABLE:
            print("  • Copy .wav or .mp3 files to SD card, OR")
        print("  • Copy .wav or .mp3 files to CIRCUITPY drive")
        print("\n  Supported formats: .wav, .mp3")
        return

    print(f"\n[3/3] Found {len(files)} audio file(s) total")
    print("-" * 50)

    for i, filepath in enumerate(files, 1):
        filename = filepath.split('/')[-1]
        location = "SD" if filepath.startswith("/sd/") else "Internal"
        print(f"{i}. {filename} [{location}]")

    print("-" * 50)

    if shuffle:
        import random
        random.shuffle(files)
        print("🔀 Shuffle mode enabled")

    if repeat:
        print("🔁 Repeat mode enabled")

    # Play all files
    try:
        while True:
            for filepath in files:
                try:
                    play_file(filepath)
                    time.sleep(0.5)  # Pause between songs
                except KeyboardInterrupt:
                    print("\n⏹ Playback stopped")
                    audio.stop()
                    return

            if not repeat:
                break

            print("\n🔁 Repeating playlist...")
    except KeyboardInterrupt:
        print("\n⏹ Playback stopped")
        audio.stop()

def play_track(track_number):
    """Play a specific track by number"""
    files = get_all_audio_files()

    if not files:
        print("No audio files found!")
        return

    if 1 <= track_number <= len(files):
        play_file(files[track_number - 1])
    else:
        print(f"Track {track_number} not found. Available: 1-{len(files)}")

def list_tracks():
    """List all available tracks"""
    files = get_all_audio_files()

    if not files:
        print("\n✗ No audio files found!")
        print("\n📁 To add files:")
        if SD_AVAILABLE:
            print("  • Copy files to SD card (/sd/), OR")
        print("  • Copy files to CIRCUITPY drive (/)")
        return

    print(f"\nPlaylist ({len(files)} tracks):")
    print("-" * 50)
    for i, filepath in enumerate(files, 1):
        filename = filepath.split('/')[-1]
        location = "SD" if filepath.startswith("/sd/") else "Internal"
        print(f"  {i}. {filename} [{location}]")
    print("-" * 50)

def play(filename, wait=True):
    """
    Play a file by name (searches both internal and SD card)

    Args:
        filename: Name of the audio file (e.g., "sound.wav")
        wait: If True, wait for playback to finish

    Example:
        play("hello.wav")
    """
    # Search in internal storage first
    if filename in os.listdir("/"):
        filepath = f"/{filename}"
    # Then search SD card
    elif SD_AVAILABLE and filename in os.listdir("/sd"):
        filepath = f"/sd/{filename}"
    else:
        print(f"File '{filename}' not found!")
        print("Available files:")
        list_tracks()
        return False

    return play_file(filepath) if wait else audio.play(filepath)

def stop():
    """Stop any currently playing audio"""
    audio.stop()

def is_playing():
    """Check if audio is currently playing"""
    return audio.playing

# ============= MAIN PROGRAM =============

# Show storage status
print("\n📦 Storage:")
if SD_AVAILABLE:
    print("  ✓ SD card available")
print("  ✓ Internal storage available")

# List all tracks
list_tracks()

# Check if we have any files
files = get_all_audio_files()

if not files:
    print("\n💡 Tip: Copy .wav or .mp3 files to play them!")

print("\n🎵 Ready to play! Use functions below to control playback.")

print("\n" + "=" * 50)
print("Music Player Functions:")
print("  play('song.wav')        - Play file by name")
print("  play_all()              - Play all files")
print("  play_all(shuffle=True)  - Play all shuffled")
print("  play_all(repeat=True)   - Repeat playlist")
print("  play_track(3)           - Play track #3")
print("  list_tracks()           - List all tracks")
print("  stop()                  - Stop playback")
print("  is_playing()            - Check if playing")
print("=" * 50)