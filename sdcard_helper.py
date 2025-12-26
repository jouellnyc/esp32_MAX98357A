"""
Robust SD card helper for CircuitPython with proper initialization.

Addresses timing issues in CircuitPython's sdcardio module:
- Settling time after mount
- Directory cache priming
- Rate limiting to prevent controller overwhelm

Usage:
    import sdcard_helper
    
    if sdcard_helper.mount():
        sdcard_helper.print_info()
        files = sdcard_helper.list_files()
"""

import busio
import sdcardio
import storage
import os
import time
import sd_config

# Module-level state
_spi = None
_sd = None
_vfs = None
_mounted = False
_last_operation_time = 0


def _check_rate_limit():
    """Internal helper to enforce rate limiting across all SD operations."""
    global _last_operation_time
    
    current_time = time.monotonic()
    time_since_last = current_time - _last_operation_time
    
    if _last_operation_time > 0 and time_since_last < 0.5:  # 500ms between operations
        wait_time = 0.5 - time_since_last
        time.sleep(wait_time)
    
    _last_operation_time = time.monotonic()


def mount():
    """Initialize SPI and mount the SD card with proper settling."""
    global _spi, _sd, _vfs, _mounted, _last_operation_time
    
    if _mounted:
        print("✓ SD card already mounted")
        return True
    
    print("Initializing SD card...")
    
    try:
        # Initialize SPI
        _spi = busio.SPI(
            clock=sd_config.SD_SCK,
            MOSI=sd_config.SD_MOSI,
            MISO=sd_config.SD_MISO,
        )
        
        # Create SD card + filesystem
        _sd = sdcardio.SDCard(
            _spi,
            sd_config.SD_CS,
            baudrate=sd_config.SD_BAUDRATE,
        )
        _vfs = storage.VfsFat(_sd)
        storage.mount(_vfs, sd_config.SD_MOUNT, readonly=True)  # Read-only for stability
        
        # CRITICAL: Let SD card settle after mount
        print("Waiting for SD card to stabilize...")
        time.sleep(1.0)
        
        # Prime the directory cache with a dummy read
        print("Initializing directory cache...")
        try:
            _ = os.listdir(sd_config.SD_MOUNT)
        except:
            pass  # Ignore errors on first read
        
        os.sync()
        time.sleep(0.5)
        
        _mounted = True
        _last_operation_time = time.monotonic()  # Set timestamp to prevent immediate rapid access
        print("✓ SD card mounted successfully!")
        return True
        
    except OSError as e:
        print(f"✗ Mount failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check SD card is inserted properly")
        print("2. Ensure SD card is FAT32 formatted")
        print("3. Try different CS pin")
        print("4. Check wiring connections")
        print("5. Verify VCC is 3.3V (NOT 5V)")
        print("6. Add 100µF capacitor to SD VCC")
        print("7. Try slower baudrate (100000)")
        return False


def unmount():
    """Unmount the SD card."""
    global _spi, _sd, _vfs, _mounted, _last_operation_time
    
    if not _mounted:
        print("✓ SD card not mounted, nothing to do")
        return True
    
    try:
        storage.umount(sd_config.SD_MOUNT)
        if _spi:
            _spi.deinit()
        _spi = None
        _sd = None
        _vfs = None
        _mounted = False
        _last_operation_time = 0
        print("✓ SD card unmounted")
        return True
    except Exception as e:
        print(f"✗ Unmount failed: {e}")
        return False


def print_info():
    """Print SD card size and file list with rate limiting."""
    if not _mounted:
        print("✗ SD card not mounted")
        return False
    
    _check_rate_limit()
    
    # Get filesystem stats
    stats = os.statvfs(sd_config.SD_MOUNT)
    total_mb = (stats[0] * stats[2]) / (1024 * 1024)
    free_mb = (stats[0] * stats[3]) / (1024 * 1024)
    used_mb = total_mb - free_mb
    
    print("\nSD Card:")
    print(f"  Total: {total_mb:.2f} MB")
    print(f"  Used:  {used_mb:.2f} MB")
    print(f"  Free:  {free_mb:.2f} MB")
    
    print("\nFiles:")
    files = os.listdir(sd_config.SD_MOUNT)
    if files:
        for f in files:
            print(f"  - {f}")
    else:
        print("  (empty)")
    
    return True


def test_sd(slow=False, count=60, interval=1):
    """
    Test SD card read/write.
    
    NOTE: This will fail if SD is mounted read-only!
    
    Args:
        slow: If False (default), single quick write/read test
              If True, repeated writes over time
        count: Number of writes for slow test (default: 60)
        interval: Seconds between writes for slow test (default: 1)
    """
    if not _mounted:
        print("✗ SD card not mounted")
        return False
    
    _check_rate_limit()
    
    path = sd_config.SD_MOUNT + "/test.txt"
    
    try:
        if not slow:
            # Quick test
            print("\nTesting write...")
            with open(path, "w") as f:
                f.write("Hello from ESP32!\n")
            print("✓ Write successful")
            
            print("Testing read...")
            with open(path, "r") as f:
                content = f.read()
                print(f"✓ Read successful: {content.strip()}")
            return True
        
        # Slow test - repeated writes
        print(f"\nStarting slow SD test ({count} writes, {interval}s interval)")
        for i in range(count):
            with open(path, "a") as f:
                f.write(f"Slow test {i+1}/{count}\n")
            print(f"  ✓ Write {i+1}/{count}")
            time.sleep(interval)
        
        print("✓ Slow SD test completed successfully")
        return True
        
    except OSError as e:
        if "Read-only" in str(e):
            print(f"✗ Test failed: SD card is mounted read-only")
            print("  This is normal - SD card is read-only for stability")
        else:
            print(f"✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def list_files(path=None):
    """
    List all files in a directory (rate-limited).
    
    Args:
        path: Directory path (default: SD mount point)
    
    Returns:
        List of filenames, or empty list on error
    """
    if not _mounted:
        print("✗ SD card not mounted")
        return []
    
    _check_rate_limit()
    
    if path is None:
        path = sd_config.SD_MOUNT
    
    try:
        return os.listdir(path)
    except Exception as e:
        print(f"✗ Error listing files: {e}")
        return []


def get_stats():
    """
    Get SD card statistics (rate-limited).
    
    Returns:
        Dictionary with total_mb, used_mb, free_mb, or None on error
    """
    if not _mounted:
        return None
    
    _check_rate_limit()
    
    try:
        stats = os.statvfs(sd_config.SD_MOUNT)
        total_mb = (stats[0] * stats[2]) / (1024 * 1024)
        free_mb = (stats[0] * stats[3]) / (1024 * 1024)
        used_mb = total_mb - free_mb
        
        return {
            'total_mb': total_mb,
            'used_mb': used_mb,
            'free_mb': free_mb
        }
    except Exception as e:
        print(f"✗ Error getting stats: {e}")
        return None


def is_mounted():
    """Check if SD card is currently mounted."""
    return _mounted