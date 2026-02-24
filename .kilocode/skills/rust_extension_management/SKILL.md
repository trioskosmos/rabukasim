---
name: rust_extension_management
description: Best practices for building, updating, and troubleshooting the `engine_rust` Python extension.
---

# Rust Extension Management Skill

Use this skill when you encounter:
- **`ValueError` on Enum Deserialization**: E.g., `ValueError: invalid value: 90`, indicating the Python binary doesn't know about a new Rust enum variant.
- **ImportErrors related to DLLs**: E.g., `ImportError: DLL load failed` or `numpy.core.multiarray failed to import`.
- **Segmentation Faults** during engine initialization.

## 1. The Core Problem: Stale Binaries
The `engine_rust` module is a compiled **Python Extension** (`.pyd` on Windows, `.so` on Linux). Unlike pure Python code, modifying the Rust source (`.rs` files) does **NOT** automatically update the running code.

- **Symptom**: You correctly added a variant to `enums.rs`, but Python throws `ValueError` when trying to load data containing it.
- **Cause**: Python is importing an old `.pyd` file from a previous build, often lingering in `site-packages` or the source directory.

## 2. The Clean Build Workflow
To guarantee your environment is using the latest Rust code, **NEVER** trust a simple `pip install`. Always perform a clean build.

### Windows (PowerShell)
```powershell
# 1. Uninstall existing package
uv pip uninstall engine_rust

# 2. BRUTE FORCE REMOVAL of all compiled extensions (Critical step)
Get-ChildItem -Filter *.pyd -Recurse | Remove-Item -Force -Verbose

# 3. Clean Reinstall (from root directory)
uv pip install -v -e ./engine_rust_src
```

## 3. The Numpy ABI Trap
The Rust extension depends on `numpy`'s C API.
- **The Trap**: If you build against `numpy 2.x` but run with `numpy 1.x` (or vice versa), the extension may crash or fail to load.
- **Best Practice**: Pin `numpy` to a stable version known to work with your `pyo3` / `numpy` crate versions.
    - Current Recommendation: `numpy==1.26.4`

### Resolution for Numpy Mismatches
1. Check current version: `uv pip list | findstr numpy`
2. Force install compatible version: `uv pip install numpy==1.26.4`
3. **REBUILD** the extension (using the Clean Build Workflow above) after changing numpy versions.

## 4. Verification
After rebuilding, verify the extension version and exposed constants:

```python
import engine_rust
print(engine_rust.PyCardDatabase.__doc__) 
# Or check specific enums if exposed (currently they are internal to the Rust logic)
```
