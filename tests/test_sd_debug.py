"""
CircuitPython SD Card Bug Test

Usage:
1. Copy sd_config.py and this file to your CircuitPython board
2. Ensure SD card has at least one file on it
3. Run: import test_sd_bug
4. For most reliable reproduction: Press Ctrl+D and run again
"""

import board
import busio
import sdcardio
import storage
import os
import time

# Import board-specific config
import sd_config

print("=" * 50)
print("SD Card Cache Bug Test (with safety)")
print("=" * 50)

def safe_listdir(path, timeout_note=5):
    """List directory with progress tracking"""
    start = time.monotonic()
    
    try:
        print(f"  [Starting listdir at {start:.2f}s]")
        files = os.listdir(path)
        elapsed = time.monotonic() - start
        print(f"  [Completed in {elapsed:.2f}s]")
        return files
    except Exception as e:
        elapsed = time.monotonic() - start
        print(f"  [FAILED after {elapsed:.2f}s: {e}]")
        return None

# Display configuration
print(f"\nBoard: {board.board_id}")
print(f"Config loaded from sd_config.py")

# Mount SD card
print("\n[STEP 1] Mounting SD card...")
spi = None
sd = None
vfs = None

try:
    spi = busio.SPI(sd_config.SD_SCK, MOSI=sd_config.SD_MOSI, MISO=sd_config.SD_MISO)
    print("  ✓ SPI initialized")
    
    sd = sdcardio.SDCard(spi, sd_config.SD_CS, baudrate=sd_config.SD_BAUDRATE)
    print(f"  ✓ SDCard object created ({sd_config.SD_BAUDRATE:,} Hz)")
    
    vfs = storage.VfsFat(sd)
    print("  ✓ VfsFat created")
    
    storage.mount(vfs, sd_config.SD_MOUNT)
    print(f"  ✓ Mounted to {sd_config.SD_MOUNT}")
    
except Exception as e:
    print(f"  ✗ Mount failed: {e}")
    print("\n❌ Test aborted - could not mount SD card")
    print("\nTroubleshooting:")
    print("  • Check SD card is inserted properly")
    print("  • Verify SD card is FAT32 formatted")
    print("  • Check wiring matches sd_config.py")
    print("  • Try lower baudrate (edit SD_BAUDRATE in sd_config.py)")
    raise SystemExit

# Check disk usage (should work even if listdir fails)
print("\n[STEP 2] Checking disk usage...")
used_mb = 0
try:
    stats = os.statvfs(sd_config.SD_MOUNT)
    total_mb = (stats[0] * stats[2]) / (1024 * 1024)
    used_mb = ((stats[0] * stats[2]) - (stats[0] * stats[3])) / (1024 * 1024)
    free_mb = (stats[0] * stats[3]) / (1024 * 1024)
    print(f"  Total: {total_mb:.2f} MB")
    print(f"  Used:  {used_mb:.2f} MB")
    print(f"  Free:  {free_mb:.2f} MB")
except Exception as e:
    print(f"  ✗ statvfs failed: {e}")

# Test 1: Immediate listdir
print("\n[STEP 3] First listdir (immediate after mount)...")
print("  (If this hangs, the bug is severe - press RESET to recover)")
files1 = safe_listdir(sd_config.SD_MOUNT)

if files1 is None:
    print("  ⚠️ First listdir failed/hung - this is part of the bug!")
    files1 = []
else:
    print(f"  Result: {files1}")
    print(f"  Count: {len(files1)} files")

# Wait and try again
print("\n[STEP 4] Waiting 3 seconds...")
for i in range(3):
    time.sleep(1)
    print(f"  {i+1}...")

print("\n[STEP 5] Second listdir (after delay)...")
files2 = safe_listdir(sd_config.SD_MOUNT)

if files2 is None:
    print("  ⚠️ Second listdir also failed!")
    files2 = []
else:
    print(f"  Result: {files2}")
    print(f"  Count: {len(files2)} files")

# Try one more time
print("\n[STEP 6] Third listdir (for good measure)...")
time.sleep(1)
files3 = safe_listdir(sd_config.SD_MOUNT)

if files3 is None:
    print("  ⚠️ Third listdir also failed!")
    files3 = []
else:
    print(f"  Result: {files3}")
    print(f"  Count: {len(files3)} files")

# Analysis
print("\n" + "=" * 50)
print("RESULTS:")
print("=" * 50)
print(f"Board:       {board.board_id}")
print(f"Baudrate:    {sd_config.SD_BAUDRATE:,} Hz")
print(f"First call:  {len(files1)} files")
print(f"Second call: {len(files2)} files")
print(f"Third call:  {len(files3)} files")
print(f"Disk usage:  {used_mb:.2f} MB")

# Diagnosis
print("\n" + "=" * 50)
print("DIAGNOSIS:")
print("=" * 50)

if len(files1) == 0 and len(files2) > 0:
    print("❌ BUG CONFIRMED!")
    print("   Symptom: Files invisible on first call, appeared on second")
    print("   This is the 'Schrödinger's files' cache bug")
    print(f"   Files appeared after ~{3:.0f} second delay")
    
elif len(files1) == 0 and len(files2) == 0 and len(files3) > 0:
    print("❌ BUG CONFIRMED (severe variant)!")
    print("   Symptom: Required 2 delays (6+ seconds) before files appeared")
    print("   This board/baudrate combo needs longer settling time")
    
elif len(files1) == 0 and len(files2) == 0 and len(files3) == 0:
    if used_mb > 1:
        print("❌ BUG CONFIRMED (critical - files never appeared)!")
        print(f"   Disk shows {used_mb:.2f} MB used but listdir() always returns empty")
        print("   SD card completely unusable without workaround")
        print("\n   Suggestions:")
        print("   • Try much lower baudrate (100000 Hz)")
        print("   • Add settling time after mount (see workaround below)")
    else:
        print("⚠️ UNCLEAR - SD card appears empty")
        print("   Either:")
        print("   • SD card has no files (add a test file and try again)")
        print("   • SD card not formatted correctly (should be FAT32)")
        
elif len(files1) > 0:
    print("✅ No bug detected on this run")
    print("   Files visible immediately")
    print("\n   Possible reasons:")
    print("   • This board/baudrate is fast enough")
    print("   • SD card was already 'warmed up' from previous run")
    print("   • Try soft reboot (Ctrl+D) and run again for most reliable test")
    
else:
    print("⚠️ Unexpected result")
    print("   Check SD card and wiring")

# Workaround
if len(files1) == 0 and (len(files2) > 0 or len(files3) > 0):
    print("\n" + "=" * 50)
    print("WORKAROUND:")
    print("=" * 50)
    print("Add this after storage.mount():")
    print("")
    print("    storage.mount(vfs, '/sd')")
    print("    time.sleep(2.0)        # Let hardware settle")
    print("    _ = os.listdir('/sd')  # Prime cache")
    print("    os.sync()")
    print("    time.sleep(0.5)        # Extra settling")
    print("    # Now listdir() works reliably")

# Reproduction instructions
print("\n" + "=" * 50)
print("TO REPRODUCE MOST RELIABLY:")
print("=" * 50)
print("1. Press Ctrl+D (soft reboot)")
print("2. Run: import test_sd_bug")
print("3. Bug should appear consistently after soft reboot")
print("")
print("Report to: https://github.com/adafruit/circuitpython/issues")
print("Include: Board model, baudrate, and this test output")

# Cleanup
print("\n[CLEANUP] Attempting to unmount...")
try:
    storage.umount(sd_config.SD_MOUNT)
    if spi:
        spi.deinit()
    print("  ✓ Cleaned up successfully")
    print("  Safe to run test again or press RESET")
except Exception as e:
    print(f"  ⚠️ Cleanup failed: {e}")
    print("  Press RESET button before next test")

print("\n✓ Test complete")