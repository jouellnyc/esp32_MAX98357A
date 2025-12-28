# Python Module Import Behavior

Understanding how (Micro-)Python modules are loaded, cached, and shared across imports.

---

## Key Concept: Modules Load Once

**Python loads each module only once per session.** Subsequent imports return a reference to the already-loaded module.

---

## Example Setup

```python
# sdcard_helper.py
_mounted = False

def mount():
    global _mounted
    _mounted = True
    return True

def is_mounted():
    return _mounted
```

```python
# test_simple.py
import sdcard_helper

sdcard_helper.mount()  # Sets _mounted = True
```

---

## Import Behavior

### Scenario 1: Import test_simple

```python
>>> import test_simple
>>> dir()
['test_simple', '__name__', ...]  # Only test_simple is in REPL namespace
```

**What happened:**
1. Python loaded `test_simple.py`
2. Inside `test_simple.py`, Python loaded `sdcard_helper.py` (first time)
3. `sdcard_helper.mount()` set `_mounted = True`
4. `sdcard_helper` is in `test_simple`'s namespace, **not** the REPL's

---

### Scenario 2: Import sdcard_helper in REPL

```python
>>> import sdcard_helper
>>> dir()
['test_simple', 'sdcard_helper', '__name__', ...]  # Now both are visible
```

**What happened:**
1. Python checks: "Is `sdcard_helper` already loaded?"
2. **YES** - it was loaded by `test_simple`
3. Python gives you a **reference** to the same module object
4. Does **NOT** reload or re-execute `sdcard_helper.py`

---

### Scenario 3: Check _mounted variable

```python
>>> sdcard_helper._mounted
True
>>> test_simple.sdcard_helper._mounted
True
```

Both return `True` because they point to the **same module object**.

---

## Proof: Memory Addresses

```python
>>> id(sdcard_helper._mounted)
62
>>> id(test_simple.sdcard_helper._mounted)
62
>>> # Same memory address = same object!
```

All references point to the **exact same module object in memory**.

---

## How Python Tracks Modules

Python uses `sys.modules` to cache loaded modules:

```python
>>> import sys
>>> 'sdcard_helper' in sys.modules
True
>>> id(sys.modules['sdcard_helper'])
<address_A>
>>> id(sdcard_helper)
<address_A>  # Same!
>>> id(test_simple.sdcard_helper)
<address_A>  # Same!
```

All three are references to the **one module object** stored in `sys.modules`.

---

## Namespaces Explained

### REPL Namespace
After `import test_simple`:
```python
test_simple  # ✅ Visible
sdcard_helper  # ❌ Not visible (until you import it)
```

### test_simple's Namespace
```python
sdcard_helper  # ✅ Visible (imported inside test_simple.py)
os  # ✅ Visible (imported inside test_simple.py)
count  # ✅ Visible (defined inside test_simple.py)
```

### sdcard_helper's Namespace
```python
_mounted  # ✅ Module-level variable
mount  # ✅ Function
is_mounted  # ✅ Function
```

---

## Why This Matters

### 1. Module State Persists

```python
# First import (in test_simple.py)
import sdcard_helper
sdcard_helper.mount()  # Sets _mounted = True

# Later import (in REPL)
import sdcard_helper
sdcard_helper.is_mounted()  # Returns True (state persisted!)
```

### 2. Singleton Pattern Works

Module-level variables act as singletons:
```python
# config.py
DATABASE_URL = "postgres://..."

# Multiple files import config
# All see the SAME DATABASE_URL
```

### 3. Prevents Duplicate Execution

```python
# expensive_module.py
print("Loading expensive module...")
data = load_huge_dataset()  # Slow!

# First import: prints message, loads data
import expensive_module

# Second import: does nothing, returns cached module
import expensive_module  # Fast! No reload!
```

---

## Common Pitfall

**Accessing nested imports:**

```python
>>> import test_simple
>>> test_simple.sdcard_helper._mounted  # ✅ Works
True

# But sdcard_helper is NOT in REPL namespace yet:
>>> sdcard_helper._mounted  # ❌ NameError
NameError: name 'sdcard_helper' is not defined

# Must import it first:
>>> import sdcard_helper
>>> sdcard_helper._mounted  # ✅ Now it works
True
```

---

## Key Takeaways

1. **Modules load once** - Python caches them in `sys.modules`
2. **All imports share the same object** - Changes persist everywhere
3. **Namespaces are separate** - Importing in one module doesn't add it to another's namespace
4. **Module state is global** - Module-level variables are shared across all imports
5. **Memory efficient** - One module object, many references

---

## See Also

- [Python Import System](https://docs.python.org/3/reference/import.html)
- [sys.modules Documentation](https://docs.python.org/3/library/sys.html#sys.modules)
- [Python Namespaces Guide](https://docs.python.org/3/tutorial/classes.html#python-scopes-and-namespaces)
