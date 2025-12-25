
import struct
import math

def create_quiet_test_tone(filename="quiet_test.wav", duration=2, frequency=440, volume=0.05):
    """
    Create a very quiet test tone WAV file.

    Args:
        filename: Output filename
        duration: Duration in seconds (default: 2)
        frequency: Tone frequency in Hz (default: 440 = A note)
        volume: Volume level 0.0-1.0 (default: 0.05 = whisper quiet!)
    """
    sample_rate = 22050  # Lower sample rate = smaller file
    num_samples = sample_rate * duration

    # Generate quiet sine wave
    samples = []
    for i in range(num_samples):
        # Sine wave: amplitude * sin(2π * frequency * time)
        t = i / sample_rate
        sample_value = int(volume * 32767 * math.sin(2 * math.pi * frequency * t))
        samples.append(sample_value)

    # WAV file structure
    with open(filename, "wb") as f:
        # RIFF header
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + num_samples * 2))  # File size
        f.write(b'WAVE')

        # fmt chunk
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))  # fmt chunk size
        f.write(struct.pack('<H', 1))   # PCM format
        f.write(struct.pack('<H', 1))   # Mono
        f.write(struct.pack('<I', sample_rate))
        f.write(struct.pack('<I', sample_rate * 2))  # Byte rate
        f.write(struct.pack('<H', 2))   # Block align
        f.write(struct.pack('<H', 16))  # Bits per sample

        # data chunk
        f.write(b'data')
        f.write(struct.pack('<I', num_samples * 2))

        # Write samples
        for sample in samples:
            f.write(struct.pack('<h', sample))

    print(f"✓ Created {filename}")
    print(f"  Duration: {duration}s")
    print(f"  Frequency: {frequency}Hz")
    print(f"  Volume: {int(volume * 100)}% (whisper level)")
    print(f"  Size: {(36 + num_samples * 2) / 1024:.1f} KB")

# Create the quiet test file
create_quiet_test_tone("quiet_test.wav", duration=2, frequency=440, volume=0.05)

print("\n💡 To test on ESP32:")
print("  1. Copy quiet_test.wav to CIRCUITPY drive or SD card")
print("  2. Run: play('quiet_test.wav')")
print("\n🔇 Volume is set to 5% - very quiet!")
print("   If still too loud, regenerate with volume=0.02 (2%)")


