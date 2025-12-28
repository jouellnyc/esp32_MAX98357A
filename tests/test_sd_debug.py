"""
CircuitPython SD Card Bug Test - Compatible with CP 10.0.3

WHAT THIS TEST DOES:
====================
This script tests for two common SD card bugs in CircuitPython:

1. CACHE BUG ("Schrödinger's Files"):
   - Symptom: os.listdir() returns [] on first call after mount, but shows 
     files on second call
   - Cause: SD card directory cache not initialized after mount
   - Pattern: 0 files → (wait) → 10 files

2. TIMEOUT BUG (DevKitC specific):
   - Symptom: Files appear on first call, then DISAPPEAR after 1+ second idle
   - Cause: SD card enters power-saving mode after 1 second of inactivity
   - Pattern: 10 files → (wait 3s) → 0 files

HOW IT WORKS:
=============
1. Mounts the SD card (will hang if you used Ctrl+D soft reboot)
2. Checks disk usage to verify files exist
3. Calls os.listdir() three times with delays between:
   - Immediate after mount
   - After 3 seconds
   - After 1 more second
4. Analyzes the pattern of results to identify which bug (if any) is present
5. Provides specific workarounds for the detected issue

TESTED BOARDS:
==============
- Waveshare RP2350-Plus: ✅ No bugs (works perfectly)
- ESP32 Feather Huzzah: ✅ No cache/timeout bugs (soft reboot issue only)
- ESP32-S3 DevKitC: ❌ Has 1-second timeout bug at all speeds

IMPORTANT:
==========
- NEVER use Ctrl+D (soft reboot) when testing SD cards on ESP32 boards
  (causes hang at VfsFat creation)
- Always use RESET button to restart between tests
- Requires sd_config.py with board-specific pin configuration

USAGE:
======
1. Hard reset your board (press RESET button)
2. Run: import test_sd_debug
3. Review the diagnosis output
4. Follow the recommended workarounds

For more info: https://github.com/adafruit/circuitpython/issues/10741
"""

import board
import busio
import sdcardio
import storage
import os
import time

print("=" * 60)
print("SD Card Bug Test - Complete Diagnostic")
print("=" * 60)

# Import config
try:
    import sd_config
except ImportError:
    print("\n✗ ERROR: sd_config.py not found!")
    raise SystemExit

# Warn about soft reboot
print("\n⚠️  IMPORTANT: If you just pressed Ctrl+D, this will hang!")
print("    Use RESET button instead")
print("")

print(f"Board: {board.board_id}")
print(f"Config: {sd_config.SD_BAUDRATE:,} Hz")

def safe_listdir(path):
    """List directory with timing info"""
    start = time.monotonic()
    try:
        files = os.listdir(path)
        elapsed = time.monotonic() - start
        print(f"  Completed in {elapsed:.3f}s")
        return files
    except Exception as e:
        elapsed = time.monotonic() - start
        print(f"  FAILED after {elapsed:.3f}s: {e}")
        return None

# Mount
print("\n" + "=" * 60)
print("MOUNTING SD CARD")
print("=" * 60)

try:
    print("\n[1/4] Creating SPI...")
    spi = busio.SPI(sd_config.SD_SCK, MOSI=sd_config.SD_MOSI, MISO=sd_config.SD_MISO)
    print("      ✓ Done")
    
    print(f"\n[2/4] Creating SDCard ({sd_config.SD_BAUDRATE:,} Hz)...")
    sd = sdcardio.SDCard(spi, sd_config.SD_CS, baudrate=sd_config.SD_BAUDRATE)
    print("      ✓ Done")
    
    print("\n[3/4] Creating VfsFat...")
    print("      (Soft reboot hangs here - press RESET if stuck)")
    vfs = storage.VfsFat(sd)
    print("      ✓ Done")
    
    print(f"\n[4/4] Mounting to {sd_config.SD_MOUNT}...")
    storage.mount(vfs, sd_config.SD_MOUNT)
    print("      ✓ Mounted!")
    
except Exception as e:
    print(f"\n      ✗ Failed: {e}")
    print("\nIf 'IO pin in use', press RESET and try again")
    raise SystemExit

# Check disk usage
print("\n" + "=" * 60)
print("DISK USAGE")
print("=" * 60)

used_mb = 0
try:
    stats = os.statvfs(sd_config.SD_MOUNT)
    total_mb = (stats[0] * stats[2]) / (1024 * 1024)
    used_mb = ((stats[0] * stats[2]) - (stats[0] * stats[3])) / (1024 * 1024)
    free_mb = (stats[0] * stats[3]) / (1024 * 1024)
    print(f"\n  Total: {total_mb:.2f} MB")
    print(f"  Used:  {used_mb:.2f} MB")
    print(f"  Free:  {free_mb:.2f} MB")
except Exception as e:
    print(f"\n  ✗ Failed: {e}")

# Test for bugs
print("\n" + "=" * 60)
print("TESTING FOR BUGS")
print("=" * 60)

# Test 1: Immediate
print("\n[Test 1] First listdir (immediate after mount):")
files1 = safe_listdir(sd_config.SD_MOUNT)
if files1:
    print(f"  Result: {len(files1)} files")
else:
    print(f"  Result: Empty or failed")

# Test 2: After 3 seconds
print("\n[Test 2] Waiting 3 seconds...")
time.sleep(1)
print("  1...")
time.sleep(1)
print("  2...")
time.sleep(1)
print("  3...")

print("\n[Test 2] Second listdir (after 3s):")
files2 = safe_listdir(sd_config.SD_MOUNT)
if files2:
    print(f"  Result: {len(files2)} files")
else:
    print(f"  Result: Empty or failed")

# Test 3: One more
print("\n[Test 3] Third listdir (after 1s):")
time.sleep(1)
files3 = safe_listdir(sd_config.SD_MOUNT)
if files3:
    print(f"  Result: {len(files3)} files")
else:
    print(f"  Result: Empty or failed")

# Analysis
len1 = len(files1) if files1 else 0
len2 = len(files2) if files2 else 0
len3 = len(files3) if files3 else 0

print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)

print(f"\nBoard:       {board.board_id}")
print(f"Baudrate:    {sd_config.SD_BAUDRATE:,} Hz")
print(f"Disk usage:  {used_mb:.2f} MB")
print(f"\nFile counts:")
print(f"  First call:  {len1}")
print(f"  Second call: {len2}")
print(f"  Third call:  {len3}")

# Diagnosis
print("\n" + "=" * 60)
print("DIAGNOSIS")
print("=" * 60)

bug_type = None

# Pattern 1: Files disappear (TIMEOUT BUG)
if len1 > 0 and len2 == 0:
    bug_type = "TIMEOUT"
    print("\n❌ TIMEOUT BUG DETECTED!")
    print("   Files appeared, then DISAPPEARED")
    print("   This is the 1-second idle timeout issue")
    
# Pattern 2: Files appear late (CACHE BUG)
elif len1 == 0 and len2 > 0:
    bug_type = "CACHE"
    print("\n❌ CACHE BUG DETECTED!")
    print("   Files invisible first, appeared after delay")
    print("   This is the cache initialization bug")
    
# Pattern 3: Files appear very late
elif len1 == 0 and len2 == 0 and len3 > 0:
    bug_type = "CACHE_SEVERE"
    print("\n❌ SEVERE CACHE BUG!")
    print("   Files needed 4+ seconds to appear")
    
# Pattern 4: Files never appear
elif len1 == 0 and len2 == 0 and len3 == 0 and used_mb > 1:
    bug_type = "CRITICAL"
    print("\n❌ CRITICAL BUG!")
    print(f"   Disk: {used_mb:.2f} MB used, but NO files visible")
    
# Pattern 5: Empty SD
elif used_mb < 0.1 and len1 == 0:
    print("\n⚠️  SD card appears empty")
    print("   Add test files and try again")
    
# Pattern 6: Works perfectly
elif len1 > 0 and len2 > 0 and len3 > 0:
    print("\n✅ NO BUGS DETECTED")
    print("   All calls returned files")
    print("   This configuration is stable")
    
# Pattern 7: Weird
else:
    print("\n⚠️  UNUSUAL PATTERN")
    print("   Doesn't match known bugs")

# Details for each bug type
if bug_type == "TIMEOUT":
    print("\n" + "-" * 60)
    print("TIMEOUT BUG DETAILS:")
    print("-" * 60)
    print("\nSD card dumps cache after 1 second idle time.")
    print(f"Happens at {sd_config.SD_BAUDRATE:,} Hz (all speeds)")
    print("\nWorkaround: Keepalive pattern")
    print("  import time")
    print("  while True:")
    print("      time.sleep(0.8)")
    print("      sdcard_helper.keepalive()")

elif bug_type in ["CACHE", "CACHE_SEVERE"]:
    print("\n" + "-" * 60)
    print("CACHE BUG WORKAROUND:")
    print("-" * 60)
    print("\nAdd settling time after mount:")
    print("  storage.mount(vfs, '/sd')")
    print("  time.sleep(2.0)")
    print("  _ = os.listdir('/sd')")
    print("  os.sync()")

elif bug_type == "CRITICAL":
    print("\n" + "-" * 60)
    print("SD CARD UNUSABLE")
    print("-" * 60)
    print("\nTry different board or SD module")

# Important notes
print("\n" + "=" * 60)
print("IMPORTANT")
print("=" * 60)
print("\n🔴 NEVER use Ctrl+D with SD cards on ESP32!")
print("   Always use RESET button")
print("\n✅ To test again: Press RESET, then import test_sd_debug")

# Cleanup
print("\n" + "=" * 60)
print("CLEANUP")
print("=" * 60)

try:
    storage.umount(sd_config.SD_MOUNT)
    spi.deinit()
    print("\n✓ Done")
except Exception as e:
    print(f"\n⚠️  Failed: {e}")
    print("Press RESET before next test")

print("\n✓ TEST COMPLETE\n")