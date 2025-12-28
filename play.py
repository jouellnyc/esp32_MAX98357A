import time
import os
import gc

import board
import audiobusio
import audiocore
import audiomp3

import audio_config

print("=" * 50)
print("ESP32 Universal Music Player")
print("=" * 50)

# ============= BOARD DETECTION =============
BOARD_NAME = board.board_id
print(f"\nDetected: {BOARD_NAME}")

# ============= SD CARD SETUP =============
SD_AVAILABLE = False
SDCARD_HELPER_AVAILABLE = False

print("\n[1/3] Checking for SD card...")

try:
    import sdcard_helper
    SDCARD_HELPER_AVAILABLE = True
    
    # Check if already mounted
    if sdcard_helper.is_mounted():
        print("✓ SD card already mounted!")
        SD_AVAILABLE = True
    else:
        # Mount it
        if sdcard_helper.mount():
            print("✓ SD card ready!")
            SD_AVAILABLE = True
        else:
            print("⚠ No SD card detected (this is OK!)")
            print("  Will use internal storage instead")
            
except ImportError:
    print("⚠ sdcard_helper not found - SD card support disabled")
    print("  Will use internal storage only")
except Exception as e:
    print(f"⚠ SD card error: {e}")
    print("  Will use internal storage instead")

# ============= AUDIO SETUP (MAX98357A) =============
print("\n[2/3] Initializing audio...")

audio = audiobusio.I2SOut(
    bit_clock=audio_config.I2S_BIT_CLOCK,
    word_select=audio_config.I2S_WORD_SELECT,
    data=audio_config.I2S_DATA,
)

print("✓ Audio initialized!")

# ============= SD CARD HELPERS =============

def refresh_sd():
    """Remount SD card to recover from failed state.
    
    Use this if files disappear or SD card becomes unresponsive.
    
    Returns:
        bool: True if refresh successful, False otherwise
    """
    global SD_AVAILABLE
    
    if not SDCARD_HELPER_AVAILABLE:
        print("✗ sdcard_helper not available")
        return False
    
    if not SD_AVAILABLE:
        print("✗ No SD card to refresh")
        return False
    
    print("\n🔄 Refreshing SD card...")
    
    try:
        import sdcard_helper
        
        # Unmount
        sdcard_helper.unmount()
        print("  Unmounted...")
        
        time.sleep(1)
        
        # Remount
        if sdcard_helper.mount():
            SD_AVAILABLE = True
            print("✓ SD card refreshed and ready!")
            return True
        else:
            SD_AVAILABLE = False
            print("✗ Refresh failed")
            return False
            
    except Exception as e:
        print(f"✗ Refresh error: {e}")
        SD_AVAILABLE = False
        return False

# ============= MUSIC LIBRARY =============

def get_audio_files(directory="/", file_filter=None):
    """Get all audio files from specified directory
    
    Args:
        directory: Directory to scan
        file_filter: Optional filter:
                    'mp3' - only MP3 files
                    'wav' - only WAV files
                    'low' - only low quality files (16khz or 22khz in name)
                    function - custom filter function(filename) -> bool
    """
    audio_files = []
    
    try:
        # Use sdcard_helper's rate-limited list_files for SD card
        if directory == "/sd" and SDCARD_HELPER_AVAILABLE:
            import sdcard_helper
            files = sdcard_helper.list_files(directory)
        else:
            files = os.listdir(directory)
        
        for filename in files:
            # Skip system files and directories
            if filename.startswith('.') or filename == 'sd':
                continue

            filepath = f"{directory}/{filename}" if directory != "/" else f"/{filename}"

            # Check if it's an audio file
            if not filename.lower().endswith(('.wav', '.mp3')):
                continue
            
            # Apply filter if provided
            if file_filter:
                if file_filter == 'mp3' and not filename.lower().endswith('.mp3'):
                    continue
                elif file_filter == 'wav' and not filename.lower().endswith('.wav'):
                    continue
                elif file_filter == 'low':
                    name_lower = filename.lower()
                    if not ('16khz' in name_lower or '22khz' in name_lower or '8khz' in name_lower):
                        continue
                elif callable(file_filter) and not file_filter(filename):
                    continue
            
            audio_files.append(filepath)

        # Sort alphabetically
        audio_files.sort()

    except Exception as e:
        print(f"⚠ Error reading directory {directory}: {e}")
        if directory == "/sd":
            print("  💡 Tip: Try refresh_sd() to fix SD card issues")

    return audio_files

def get_all_audio_files(file_filter=None):
    """Get audio files from both internal and SD card
    
    Args:
        file_filter: Optional filter - 'mp3', 'wav', 'low', or function
    """
    all_files = []

    # Get files from internal storage
    internal_files = get_audio_files("/", file_filter)
    if internal_files:
        print(f"  Found {len(internal_files)} file(s) on internal storage")
        all_files.extend(internal_files)

    # Get files from SD card if available
    if SD_AVAILABLE:
        sd_files = get_audio_files("/sd", file_filter)
        if sd_files:
            print(f"  Found {len(sd_files)} file(s) on SD card")
            all_files.extend(sd_files)
        elif not sd_files and SD_AVAILABLE:
            print("  ⚠ SD card returned no files (may need refresh)")

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
                
            except KeyboardInterrupt:
                audio.stop()
                print(f"\n  ⏹ Stopped at {elapsed}s                ")
        
        # Cleanup after playback
        audio.stop()
        gc.collect()  # Free up memory
        time.sleep(0.3)  # Let SD card settle
        return True

    except KeyboardInterrupt:
        audio.stop()
        raise
    except Exception as e:
        print(f"  ✗ Error: {e}")
        if "sd/" in filepath.lower():
            print("  💡 Tip: Try refresh_sd() if SD card files won't play")
        audio.stop()
        gc.collect()
        return False

def play_all(shuffle=False, repeat=False, file_filter=None):
    """Play audio files
    
    Args:
        shuffle: Randomize playback order
        repeat: Loop playlist
        file_filter: Filter files - 'mp3', 'wav', 'low', or None for all
    """
    files = get_all_audio_files(file_filter)

    if not files:
        filter_msg = ""
        if file_filter == 'mp3':
            filter_msg = " (MP3 files)"
        elif file_filter == 'wav':
            filter_msg = " (WAV files)"
        elif file_filter == 'low':
            filter_msg = " (low quality files)"
        
        print(f"\n✗ No audio files found{filter_msg}!")
        print("\n📁 To add files:")
        if SD_AVAILABLE:
            print("  • Copy .wav or .mp3 files to SD card, OR")
            print("  • If SD files are missing, try: refresh_sd()")
        print("  • Copy .wav or .mp3 files to CIRCUITPY drive")
        print("\n  Supported formats: .wav, .mp3")
        return

    print(f"\n[3/3] Found {len(files)} audio file(s)")
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
            gc.collect()
    except KeyboardInterrupt:
        print("\n⏹ Playback stopped")
        audio.stop()

def play_all_mp3(shuffle=False, repeat=False):
    """Play all MP3 files"""
    print("🎵 Playing MP3 files only")
    play_all(shuffle=shuffle, repeat=repeat, file_filter='mp3')

def play_all_wav(shuffle=False, repeat=False):
    """Play all WAV files"""
    print("🎵 Playing WAV files only")
    play_all(shuffle=shuffle, repeat=repeat, file_filter='wav')

def play_all_low(shuffle=False, repeat=False):
    """Play all low quality files (16khz, 22khz, 8khz)"""
    print("🎵 Playing low quality files only")
    play_all(shuffle=shuffle, repeat=repeat, file_filter='low')

def play_track(track_number, file_filter=None):
    """Play a specific track by number
    
    Args:
        track_number: Track number to play (1-based)
        file_filter: Optional filter - 'mp3', 'wav', 'low'
    """
    files = get_all_audio_files(file_filter)

    if not files:
        print("No audio files found!")
        if SD_AVAILABLE:
            print("💡 Tip: Try refresh_sd() if SD files are missing")
        return

    if 1 <= track_number <= len(files):
        play_file(files[track_number - 1])
    else:
        print(f"Track {track_number} not found. Available: 1-{len(files)}")

def list_tracks(file_filter=None):
    """List all available tracks
    
    Args:
        file_filter: Optional filter - 'mp3', 'wav', 'low'
    """
    files = get_all_audio_files(file_filter)

    if not files:
        print("\n✗ No audio files found!")
        print("\n📁 To add files:")
        if SD_AVAILABLE:
            print("  • Copy files to SD card (/sd/), OR")
            print("  • If SD files are missing, try: refresh_sd()")
        print("  • Copy files to CIRCUITPY drive (/)")
        return

    filter_msg = ""
    if file_filter == 'mp3':
        filter_msg = " (MP3 only)"
    elif file_filter == 'wav':
        filter_msg = " (WAV only)"
    elif file_filter == 'low':
        filter_msg = " (Low quality only)"

    print(f"\nPlaylist ({len(files)} tracks{filter_msg}):")
    print("-" * 50)
    for i, filepath in enumerate(files, 1):
        filename = filepath.split('/')[-1]
        location = "SD" if filepath.startswith("/sd/") else "Internal"
        print(f"  {i}. {filename} [{location}]")
    print("-" * 50)

def play(filename, wait=True):
    """Play a file by name (searches both internal and SD card)

    Args:
        filename: Name of the audio file (e.g., "sound.wav")
        wait: If True, wait for playback to finish

    Example:
        play("hello.wav")
    """
    # Search in internal storage first
    try:
        if filename in os.listdir("/"):
            filepath = f"/{filename}"
        # Then search SD card
        elif SD_AVAILABLE:
            # Use sdcard_helper's rate-limited list if available
            if SDCARD_HELPER_AVAILABLE:
                import sdcard_helper
                sd_files = sdcard_helper.list_files("/sd")
            else:
                sd_files = os.listdir("/sd")
                
            if filename in sd_files:
                filepath = f"/sd/{filename}"
            else:
                print(f"File '{filename}' not found!")
                print("Available files:")
                list_tracks()
                return False
        else:
            print(f"File '{filename}' not found!")
            print("Available files:")
            list_tracks()
            return False
    except Exception as e:
        print(f"Error searching for file: {e}")
        if SD_AVAILABLE:
            print("💡 Tip: Try refresh_sd() if having SD card issues")
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
    print("  ✓ SD card available (read-only)")
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
print("  play_all_mp3()          - Play all MP3 files")
print("  play_all_wav()          - Play all WAV files")
print("  play_all_low()          - Play low quality files")
print("  play_all(shuffle=True)  - Play all shuffled")
print("  play_all(repeat=True)   - Repeat playlist")
print("  play_track(3)           - Play track #3")
print("  list_tracks()           - List all tracks")
print("  list_tracks('mp3')      - List MP3 files only")
print("  list_tracks('low')      - List low quality only")
if SD_AVAILABLE:
    print("  refresh_sd()            - Refresh SD if files disappear ⚡")
print("  stop()                  - Stop playback")
print("  is_playing()            - Check if playing")
if SD_AVAILABLE:
    print("\n💡 If SD files disappear, just run: refresh_sd()")
print("=" * 50)