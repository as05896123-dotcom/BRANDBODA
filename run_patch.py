#!/usr/bin/env python3
# run_patch.py
"""
Safe patcher for py-tgcalls:
- Removes old installed package (with backup),
- Installs requested version,
- Patches exceptions.py to add TelegramServerError,
- Patches types file to inject Update.chat_id alias -> chat.id,
- Optionally removes repo-level pytgcalls_patch.py.
Usage:
  python3 run_patch.py --patch-only
  python3 run_patch.py python3 run.py
"""

import sys
import subprocess
import site
import os
import shutil
import time
import traceback
import argparse

PYTGCALLS_VERSION = "2.2.8"
TIMESTAMP = int(time.time())
BACKUP_SUFFIX = f".backup-{TIMESTAMP}"

def run(cmd, check=True):
    print(">>> Running:", " ".join(cmd))
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.stdout:
        print(res.stdout)
    if res.stderr:
        print("ERR>", res.stderr)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)} (exit {res.returncode})")
    return res

def pip_uninstall(pkg):
    try:
        run([sys.executable, "-m", "pip", "uninstall", "-y", pkg])
    except Exception as e:
        print(f"[WARN] pip uninstall {pkg} failed or package not present: {e}")

def pip_install(version):
    run([sys.executable, "-m", "pip", "install", f"py-tgcalls=={version}", "--no-cache-dir"])

def find_pytgcalls_path():
    # Try import first
    try:
        import pytgcalls
        pkg_file = getattr(pytgcalls, "__file__", None)
        if pkg_file:
            return os.path.dirname(pkg_file)
    except Exception:
        pass
    # Fallback scan site-packages
    candidates = []
    try:
        candidates.extend(site.getsitepackages())
    except Exception:
        pass
    try:
        candidates.append(site.getusersitepackages())
    except Exception:
        pass
    for base in candidates:
        if not base:
            continue
        candidate = os.path.join(base, "pytgcalls")
        if os.path.isdir(candidate):
            return candidate
    return None

def backup_and_remove_package(pkg_dir):
    if not pkg_dir or not os.path.isdir(pkg_dir):
        print("[INFO] No existing pytgcalls package dir to backup/remove.")
        return True
    backup_dir = pkg_dir + BACKUP_SUFFIX
    try:
        print(f"[INFO] Backing up existing pytgcalls to: {backup_dir}")
        if os.path.exists(backup_dir):
            print("[WARN] Backup dir already exists; removing it first.")
            shutil.rmtree(backup_dir)
        shutil.copytree(pkg_dir, backup_dir)
    except Exception as e:
        print(f"[WARN] backup failed: {e}")
    # Now remove original folder
    try:
        print(f"[INFO] Removing existing pytgcalls directory: {pkg_dir}")
        shutil.rmtree(pkg_dir)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to remove existing pytgcalls dir: {e}")
        return False

def patch_exceptions_file(pytgcalls_dir):
    exc_path = os.path.join(pytgcalls_dir, "exceptions.py")
    if not os.path.isfile(exc_path):
        print(f"[WARN] exceptions.py not found at {exc_path}")
        return False
    # Backup file
    try:
        shutil.copy2(exc_path, exc_path + BACKUP_SUFFIX)
    except Exception as e:
        print(f"[WARN] couldn't backup exceptions.py: {e}")
    with open(exc_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "class TelegramServerError" in content or "TelegramServerError =" in content:
        print("[INFO] TelegramServerError already defined in exceptions.py")
        return True
    shim = """

# --- Compatibility shim injected by run_patch.py ---
class TelegramServerError(Exception):
    \"\"\"Compatibility alias injected for older code expecting TelegramServerError.\"\"\"
    pass

# End of compatibility shim
"""
    try:
        with open(exc_path, "a", encoding="utf-8") as f:
            f.write(shim)
        print("[OK] exceptions.py patched (TelegramServerError added).")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to append shim to exceptions.py: {e}")
        return False

def patch_types_chatid(pytgcalls_dir):
    """
    Append a small shim to the types module (types.py or types/__init__.py)
    to add Update.chat_id property aliasing to chat.id
    """
    # Try common locations
    candidates = [
        os.path.join(pytgcalls_dir, "types.py"),
        os.path.join(pytgcalls_dir, "types", "__init__.py"),
        os.path.join(pytgcalls_dir, "types", "types.py"),
    ]
    target = None
    for c in candidates:
        if c and os.path.isfile(c):
            target = c
            break
    if not target:
        print("[WARN] Could not find pytgcalls types file to patch. Skipping chat_id patch.")
        return False
    # Backup
    try:
        shutil.copy2(target, target + BACKUP_SUFFIX)
    except Exception as e:
        print(f"[WARN] couldn't backup types file: {e}")
    shim = """

# --- chat_id alias shim injected by run_patch.py ---
try:
    # Ensure Update class exists
    from pytgcalls.types import Update as _Update  # try absolute import
except Exception:
    _Update = globals().get("Update", None)

if _Update is not None:
    try:
        if not hasattr(_Update, "_chat_id_injected"):
            def _chat_id(self):
                try:
                    if hasattr(self, "chat") and getattr(self, "chat"):
                        return getattr(self.chat, "id", None)
                except Exception:
                    pass
                return None
            setattr(_Update, "chat_id", property(_chat_id))
            setattr(_Update, "_chat_id_injected", True)
    except Exception:
        pass
# End of shim
"""
    try:
        with open(target, "a", encoding="utf-8") as f:
            f.write(shim)
        print(f"[OK] Patched types file: {target} (injected chat_id alias).")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to append shim to types file {target}: {e}")
        return False

def remove_repo_patch_file(repo_core_path="BrandrdXMusic/core", filename="pytgcalls_patch.py"):
    target = os.path.join(repo_core_path, filename)
    if os.path.exists(target):
        try:
            print(f"[INFO] Removing repo-level patch file: {target}")
            os.remove(target)
            return True
        except Exception as e:
            print(f"[WARN] Failed to remove repo patch file: {e}")
            return False
    else:
        print("[INFO] No repo-level pytgcalls_patch.py found.")
        return True

def do_all_patching():
    # 1) Try pip uninstall to clean possible leftovers
    try:
        print("[STEP] Uninstalling existing py-tgcalls (if any)...")
        pip_uninstall("py-tgcalls")
    except Exception:
        pass

    # 2) Find any installed package dir and remove it (with backup)
    existing = find_pytgcalls_path()
    if existing:
        ok = backup_and_remove_package(existing)
        if not ok:
            print("[WARN] Could not fully remove existing package dir; continuing anyway.")

    # 3) Install requested version
    try:
        print(f"[STEP] Installing py-tgcalls=={PYTGCALLS_VERSION} ...")
        pip_install(PYTGCALLS_VERSION)
    except Exception as e:
        print(f"[ERROR] pip install failed: {e}")
        # proceed to try patching whatever exists
    # 4) Locate installed dir
    installed = find_pytgcalls_path()
    if not installed:
        print("[ERROR] Could not locate pytgcalls after install. Aborting patch steps.")
        return False
    # 5) Patch exceptions.py
    try:
        patch_exceptions_file(installed)
    except Exception as e:
        print(f"[WARN] exceptions patch failed: {e}")
    # 6) Patch types to inject chat_id alias
    try:
        patch_types_chatid(installed)
    except Exception as e:
        print(f"[WARN] types patch failed: {e}")
    # 7) remove repo-level patch file
    try:
        remove_repo_patch_file()
    except Exception as e:
        print(f"[WARN] remove repo patch failed: {e}")
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--patch-only", action="store_true", help="Run patch steps only and exit.")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to exec after patch (if not --patch-only).")
    args = parser.parse_args()

    try:
        ok = do_all_patching()
    except Exception:
        ok = False
        traceback.print_exc()

    if args.patch_only:
        if ok:
            print("[DONE] Patch-only completed successfully.")
            sys.exit(0)
        else:
            print("[DONE] Patch-only completed with errors.")
            sys.exit(2)

    if not args.command:
        print("No command provided to execute after patch.")
        print("Usage: python3 run_patch.py [--patch-only] <command...>")
        sys.exit(1)

    command = args.command
    if command and command[0] == "--":
        command = command[1:]

    print("[STEP] Executing application command now:", " ".join(command))
    try:
        os.execvp(command[0], command)
    except Exception as e:
        print(f"[WARN] execvp failed: {e}")
        subprocess.run(command)

if __name__ == "__main__":
    main()
