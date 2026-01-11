#!/usr/bin/env python3
"""
run_patch_clean.py
------------------
1) يزيل كل بقايا pytgcalls من site-packages والمجلد المحلي (مع نسخ احتياطية في /tmp).
2) يثبت py-tgcalls==2.2.8 نظيف (force reinstall).
3) يحقن TelegramServerError في exceptions.py إن لم يكن موجود.
4) يحقن shim لـ Update.chat_id (chat.id) داخل pytgcalls.types.
5) (اختياري) ينفذ الأمر الممرّر بعد الانتهاء.

Usage:
  python3 run_patch_clean.py --patch-only
  python3 run_patch_clean.py python3 run.py
"""
import sys
import os
import shutil
import subprocess
import time
import site
import glob
import traceback
import argparse

PYTGCALLS_VERSION = "2.2.8"
TIMESTAMP = int(time.time())
BACKUP_ROOT = f"/tmp/pytgcalls_backup_{TIMESTAMP}"

# ---------- helpers ----------
def run(cmd, check=False):
    print(">>>", " ".join(cmd))
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr:
        print("ERR>", res.stderr.strip())
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)} (exit {res.returncode})")
    return res

def ensure_dir(p):
    try:
        os.makedirs(p, exist_ok=True)
    except Exception:
        pass

# ---------- find candidate site-packages ----------
def get_site_paths():
    paths = []
    try:
        paths += site.getsitepackages()
    except Exception:
        pass
    try:
        paths.append(site.getusersitepackages())
    except Exception:
        pass
    # also include common locations
    paths += [
        sys.prefix and os.path.join(sys.prefix, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages") or None,
        os.path.join(sys.prefix, "lib", "python", "site-packages") if sys.prefix else None,
        "/usr/local/lib/python3.10/site-packages",
        "/usr/lib/python3.10/site-packages",
    ]
    # filter unique and existing
    res = []
    for p in paths:
        if not p:
            continue
        if p not in res:
            res.append(p)
    return res

# ---------- backup & remove matching items ----------
def backup_and_remove(path, backup_root):
    if not os.path.exists(path):
        return False
    ensure_dir(backup_root)
    name = os.path.basename(path.rstrip("/"))
    dst = os.path.join(backup_root, name)
    # if file exists, append timestamp
    if os.path.exists(dst):
        dst = dst + f"_{TIMESTAMP}"
    try:
        print(f"[BACKUP] Copying {path} -> {dst}")
        if os.path.isdir(path):
            shutil.copytree(path, dst)
            print(f"[RM] Removing directory {path}")
            shutil.rmtree(path, ignore_errors=True)
        else:
            shutil.copy2(path, dst)
            print(f"[RM] Removing file {path}")
            os.remove(path)
        return True
    except Exception as e:
        print(f"[WARN] backup_and_remove failed for {path}: {e}")
        return False

def find_and_remove_pytgcalls(backup_root):
    site_paths = get_site_paths()
    removed_any = False
    patterns = [
        "pytgcalls",
        "pytgcalls-*",
        "py_tgcalls-*",
        "py_tgcalls*.dist-info",
        "pytgcalls*.dist-info",
        "py_tgcalls-*.egg-info",
        "pytgcalls-*.egg-info",
    ]
    # Also check local project folder for a 'pytgcalls' directory (user sometimes vendors it)
    candidates = []
    # local vendor
    candidates += [os.path.join(os.getcwd(), "pytgcalls")]
    # site-packages matches
    for base in site_paths:
        for pat in patterns:
            globpath = os.path.join(base, pat)
            for match in glob.glob(globpath):
                candidates.append(match)
    # remove duplicates
    candidates = list(dict.fromkeys(candidates))
    if not candidates:
        print("[INFO] No pytgcalls artifacts found to remove.")
    for c in candidates:
        if os.path.exists(c):
            print(f"[FOUND] {c}")
            success = backup_and_remove(c, backup_root)
            removed_any = removed_any or success
    # also remove __pycache__ or compiled leftovers specifically referencing pytgcalls
    for base in site_paths + [os.getcwd()]:
        for root, dirs, files in os.walk(base):
            for d in dirs:
                if d == "__pycache__":
                    full = os.path.join(root, d)
                    # only remove cache dirs that reference pytgcalls inside name file
                    try:
                        # check files inside for pytgcalls mention
                        remove_cache = False
                        for f in os.listdir(full):
                            if "pytgcalls" in f:
                                remove_cache = True
                                break
                        if remove_cache:
                            print(f"[RM CACHE] {full}")
                            shutil.rmtree(full, ignore_errors=True)
                            removed_any = True
                    except Exception:
                        pass
    return removed_any

# ---------- main operations ----------
def nuke_pytgcalls_completely(backup_root):
    print("[STEP] Uninstalling py-tgcalls via pip (if present)...")
    run([sys.executable, "-m", "pip", "uninstall", "-y", "py-tgcalls"])
    # remove leftovers
    print("[STEP] Searching & removing pytgcalls artifacts (with backup)...")
    any_removed = find_and_remove_pytgcalls(backup_root)
    if any_removed:
        print(f"[INFO] Backups stored under: {backup_root}")
    else:
        print("[INFO] No leftover artifacts removed (none found).")

def install_clean_version(version):
    print(f"[STEP] Installing py-tgcalls=={version} (force reinstall)...")
    run([sys.executable, "-m", "pip", "install", f"py-tgcalls=={version}", "--no-cache-dir", "--force-reinstall"], check=True)

def patch_exceptions(package_dir):
    exc_path = os.path.join(package_dir, "exceptions.py")
    if not os.path.isfile(exc_path):
        print(f"[WARN] exceptions.py not found at {exc_path} — skipping exceptions patch.")
        return False
    try:
        with open(exc_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "TelegramServerError" in content:
            print("[INFO] TelegramServerError already present in exceptions.py")
            return True
        # make backup of file first
        shutil.copy2(exc_path, exc_path + f".backup-{TIMESTAMP}")
        with open(exc_path, "a", encoding="utf-8") as f:
            f.write("\n\n# --- injected TelegramServerError ---\nclass TelegramServerError(Exception):\n    pass\n# --- end injection ---\n")
        print("[OK] exceptions.py patched (TelegramServerError added).")
        return True
    except Exception as e:
        print(f"[ERROR] patch_exceptions failed: {e}")
        return False

def find_types_target(package_dir):
    # try common locations
    candidates = [
        os.path.join(package_dir, "types", "__init__.py"),
        os.path.join(package_dir, "types.py"),
        os.path.join(package_dir, "types", "types.py"),
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    # fallback: any file under package_dir named "__init__.py" inside types folder
    types_dir = os.path.join(package_dir, "types")
    if os.path.isdir(types_dir):
        for root, dirs, files in os.walk(types_dir):
            for fn in files:
                if fn.endswith(".py"):
                    return os.path.join(root, fn)
    return None

def patch_types_chatid(types_file):
    if not types_file or not os.path.isfile(types_file):
        print("[WARN] No types file found to patch chat_id alias.")
        return False
    try:
        with open(types_file, "r", encoding="utf-8") as f:
            content = f.read()
        if "_chat_id_injected" in content or "def _chat_id" in content or "chat_id = property" in content:
            print("[INFO] types file already contains chat_id injection (skipping).")
            return True
        # backup
        shutil.copy2(types_file, types_file + f".backup-{TIMESTAMP}")
        shim = """

# --- injected chat_id alias shim by run_patch_clean.py ---
try:
    from pytgcalls.types import Update as _Update
except Exception:
    _Update = globals().get("Update", None)

if _Update is not None:
    try:
        if not getattr(_Update, "_chat_id_injected", False):
            def _chat_id(self):
                # prefer existing chat_id, otherwise fallback to chat.id
                if hasattr(self, "chat_id") and getattr(self, "chat_id") is not None:
                    return getattr(self, "chat_id")
                if hasattr(self, "chat") and getattr(self, "chat") is not None:
                    return getattr(getattr(self, "chat"), "id", None)
                return None
            setattr(_Update, "chat_id", property(_chat_id))
            setattr(_Update, "_chat_id_injected", True)
    except Exception:
        pass
# --- end shim ---
"""
        with open(types_file, "a", encoding="utf-8") as f:
            f.write(shim)
        print(f"[OK] Patched types file: {types_file} (chat_id alias injected).")
        return True
    except Exception as e:
        print(f"[ERROR] patch_types_chatid failed: {e}")
        return False

def locate_installed_pytgcalls_dir():
    try:
        import importlib
        spec = importlib.util.find_spec("pytgcalls")
        if spec and spec.origin:
            pkg_file = spec.origin
            pkg_dir = os.path.dirname(pkg_file)
            return pkg_dir
    except Exception:
        pass
    # fallback scan site paths
    for base in get_site_paths():
        candidate = os.path.join(base, "pytgcalls")
        if os.path.isdir(candidate):
            return candidate
    return None

# ---------- main ----------
def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--patch-only", action="store_true", help="Run patch steps only and exit.")
    parser.add_argument("--no-backup", action="store_true", help="Do not keep backup copies (will still try to remove).")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to exec after patch (if not --patch-only).")
    args = parser.parse_args(argv)

    backup_root = BACKUP_ROOT if not args.no_backup else None
    if backup_root:
        ensure_dir(backup_root)

    # 1) remove all existing artifacts (with backup)
    try:
        nuke_pytgcalls_completely(backup_root)
    except Exception as e:
        print(f"[WARN] nuke step failed: {e}")
        traceback.print_exc()

    # 2) install clean version
    try:
        install_clean_version(PYTGCALLS_VERSION)
    except Exception as e:
        print(f"[ERROR] Installation failed: {e}")
        traceback.print_exc()

    # 3) locate installed package dir
    pkg_dir = locate_installed_pytgcalls_dir()
    if not pkg_dir:
        print("[ERROR] Could not locate installed pytgcalls package directory after install.")
    else:
        print(f"[INFO] Located pytgcalls package at: {pkg_dir}")
        # 4) patch exceptions.py
        patch_exceptions(pkg_dir)
        # 5) patch types file
        types_file = find_types_target(pkg_dir)
        patch_types_chatid(types_file)

    print("[DONE] patching operations complete.")

    if args.patch_only:
        print("[INFO] --patch-only requested: exiting now.")
        return 0

    # Exec provided command (require at least one)
    if not args.command:
        print("No command provided to execute after patch. Exiting.")
        return 2

    cmd = args.command
    # remove leading '--' if present
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    try:
        print("[STEP] Executing:", " ".join(cmd))
        os.execvp(cmd[0], cmd)
    except Exception as e:
        print(f"[ERROR] exec failed: {e}")
        traceback.print_exc()
        return 3

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
