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
import gc
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
    global _mounted
    if _mounted: return True

    try:
        # Use the pins that just passed your Hardware Test
        spi = busio.SPI(sd_config.SD_SCK, MOSI=sd_config.SD_MOSI, MISO=sd_config.SD_MISO)
        
        # Initialize the SD Card hardware
        sd = sdcardio.SDCard(spi, sd_config.SD_CS, baudrate=sd_config.SD_BAUDRATE)
        
        # Mount the filesystem
        vfs = storage.VfsFat(sd)
        storage.mount(vfs, sd_config.SD_MOUNT)
        
        # CRITICAL: Do NOT list files or sync yet. 
        # Just wait for the electrical spike to settle.
        time.sleep(0.2) 
        
        _mounted = True
        print("✓ SD Mounted successfully")
        return True
        
    except Exception as e:
        print(f"✗ Mount failed: {e}")
        return False
    


def unmount():
    """Unmount the SD card with aggressive cleanup."""
    global _spi, _sd, _vfs, _mounted, _last_operation_time
    
    if not _mounted:
        print("✓ SD card not mounted, nothing to do")
        return True
    
    try:
        # Unmount filesystem first
        try:
            storage.umount(sd_config.SD_MOUNT)
        except:
            pass  # Might already be unmounted
        
        # Aggressively clean up SPI and related objects
        if _spi:
            try:
                _spi.deinit()
            except:
                pass  # Already deinitialized
        
        # Clear all references
        _spi = None
        _sd = None
        _vfs = None
        
        # Force garbage collection to release pins
        gc.collect()
        
        # Give hardware time to release pins
        time.sleep(0.5)
        
        _mounted = False
        _last_operation_time = 0
        print("✓ SD card unmounted")
        return True
        
    except Exception as e:
        print(f"✗ Unmount failed: {e}")
        # Force cleanup anyway
        _spi = None
        _sd = None
        _vfs = None
        _mounted = False
        gc.collect()
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


def list_files(path=None):  # Add 'path=None' here
    """List all files in a directory (rate-limited)."""
    if not _mounted:
        print("✗ SD card not mounted")
        return []
    
    _check_rate_limit()
    
    # Use the provided path, or default to the config mount point
    search_path = path if path else sd_config.SD_MOUNT
    
    try:
        return os.listdir(search_path)
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


def verify_sd_stability(iterations=10):
    """Loops through all files on the SD card multiple times."""
    for i in range(1, iterations + 1):
        print(f"\n--- Test Loop {i} ---")
        try:
            files = os.listdir("/sd")
            print(f"Found {len(files)} files:")
            
            for filename in files:
                # Check file size to verify it's readable
                stats = os.stat("/sd/" + filename)
                size = stats[6] # Index 6 is the file size in bytes
                print(f" - {filename} ({size} bytes)")
                
            # Small pause between loops to prevent overheating
            time.sleep(0.5) 
            
        except Exception as e:
            print(f"STABILITY ERROR on loop {i}: {e}")
            return False
            
    print("\n[SUCCESS] SD card is stable over 10 read cycles.")
    return True

