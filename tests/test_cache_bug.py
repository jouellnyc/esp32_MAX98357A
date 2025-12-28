"""
CircuitPython SD Card Cache Bug Test

Tests for Issue #3: Cache Bug
- First listdir() returns empty even though files exist

USAGE:
======
1. Press RESET button
2. Run: import test_cache_bug
"""

import board
import busio
import sdcardio
import storage
import os
import time

print("=" * 60)
print("SD Card Cache Bug Test")
print("=" * 60)

# Import config
try:
    import sd_config
except ImportError:
    print("\n✗ ERROR: sd_config.py not found!")
    raise SystemExit

# Handle baudrate
baudrate = sd_config.SD_BAUDRATE
if isinstance(baudrate, tuple):
    baudrate = baudrate[0]

print(f"\nBoard: {board.board_id}")
print(f"Baudrate: {baudrate:,} Hz")

# Mount SD card
print("\n" + "=" * 60)
print("MOUNTING SD CARD")
print("=" * 60)

try:
    spi = busio.SPI(sd_config.SD_SCK, MOSI=sd_config.SD_MOSI, MISO=sd_config.SD_MISO)
    sd = sdcardio.SDCard(spi, sd_config.SD_CS, baudrate=sd_config.SD_BAUDRATE)
    vfs = storage.VfsFat(sd)
    storage.mount(vfs, sd_config.SD_MOUNT)
    print("✓ Mounted!")
except Exception as e:
    print(f"✗ Failed: {e}")
    raise SystemExit

# Test: Check immediately vs after settling
print("\n" + "=" * 60)
print("TESTING")
print("=" * 60)

print("\n[1] Checking files IMMEDIATELY after mount:")
files1 = os.listdir(sd_config.SD_MOUNT)
print(f"    Result: {len(files1)} files")

print("\n[2] Waiting 2 seconds...")
time.sleep(2)

print("\n[3] Checking files AFTER 2 seconds:")
files2 = os.listdir(sd_config.SD_MOUNT)
print(f"    Result: {len(files2)} files")

# Diagnosis
print("\n" + "=" * 60)
print("DIAGNOSIS")
print("=" * 60)

if len(files1) == 0 and len(files2) > 0:
    print("\n❌ CACHE BUG!")
    print(f"   • Immediate check: {len(files1)} files (WRONG!)")
    print(f"   • After 2 seconds: {len(files2)} files (CORRECT!)")
    print("\n   FIX: Add settling time after mount")
    print("   storage.mount(vfs, '/sd')")
    print("   time.sleep(1.0)")
    print("   _ = os.listdir('/sd')")

elif len(files1) == len(files2) and len(files1) > 0:
    print("\n✅ NO CACHE BUG!")
    print(f"   • Both checks found {len(files1)} files")
    print("   • This board is good!")

else:
    print("\n⚠️  UNEXPECTED RESULT")
    print(f"   • Immediate: {len(files1)} files")
    print(f"   • After wait: {len(files2)} files")

# Cleanup
print("\n" + "=" * 60)
print("CLEANUP")
print("=" * 60)

try:
    storage.umount(sd_config.SD_MOUNT)
    spi.deinit()
    print("✓ Done")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\n✓ TEST COMPLETE\n")