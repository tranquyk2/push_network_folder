import sys
import winreg
from pathlib import Path

# Đường dẫn icon
ICON_PATH = str(Path(__file__).resolve().parent / "folder.ico")

# Top-level menu
MENU_KEY = r"Software\Classes\*\shell\NAS_Uploader"

# Subcommands container (relative to HKCR)
SUBCOMMANDS_KEY = "NAS_Uploader_SubCommands"

# Full path to subcommands container
SUBCOMMANDS_FULL = r"Software\Classes\NAS_Uploader_SubCommands"


def _pythonw() -> str:
    return sys.executable.replace("python.exe", "pythonw.exe")


def _handler_path() -> str:
    return str(Path(__file__).resolve().parent / "shell_handler.py")


def register(destinations: dict) -> bool:
   
    unregister()

    if not destinations:
        return True

    pythonw = _pythonw()
    handler = _handler_path()

    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, MENU_KEY) as key:
            winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, "Gửi lên ổ chung")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, ICON_PATH)
            winreg.SetValueEx(key, "ExtendedSubCommandsKey", 0, winreg.REG_SZ,
                              SUBCOMMANDS_KEY)

        for name, path in destinations.items():
            verb_key = f"{SUBCOMMANDS_FULL}\\shell\\{name}"

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, verb_key) as key:
                display = f"{name}  ({path})" if len(path) < 50 else name
                winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, display)
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, ICON_PATH)

            cmd_key = f"{verb_key}\\command"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cmd_key) as key:
                cmd = f'"{pythonw}" "{handler}" --dest "{name}" "%1"'
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, cmd)

        return True
    except Exception as e:
        print(f"[context_menu] Lỗi khi đăng ký: {e}")
        return False


def unregister() -> bool:
    try:
        _delete_tree_safe(winreg.HKEY_CURRENT_USER, MENU_KEY)

        _delete_tree_safe(winreg.HKEY_CURRENT_USER, SUBCOMMANDS_FULL)

        _cleanup_old_keys()

        return True
    except Exception as e:
        print(f"[context_menu] Lỗi khi xóa: {e}")
        return False


def _cleanup_old_keys():
    prefix = r"Software\Classes\*\shell"
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, prefix, 0,
            winreg.KEY_READ | winreg.KEY_WRITE
        ) as shell_key:
            i = 0
            to_delete = []
            while True:
                try:
                    sub = winreg.EnumKey(shell_key, i)
                    if sub.startswith("NAS_Uploader_"):
                        to_delete.append(sub)
                    i += 1
                except OSError:
                    break

        for sub in to_delete:
            _delete_tree_safe(winreg.HKEY_CURRENT_USER, f"{prefix}\\{sub}")
    except FileNotFoundError:
        pass

    _delete_all_prefixed(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell",
        "NAS_Uploader.",
    )


def _delete_tree_safe(root, path: str):
    """Xóa registry key + toàn bộ subkey."""
    try:
        _delete_recursive(root, path)
    except FileNotFoundError:
        pass
    except OSError:
        pass


def _delete_recursive(root, path: str):
    """Đệ quy xóa key và tất cả subkey con."""
    with winreg.OpenKey(root, path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
        while True:
            try:
                sub = winreg.EnumKey(key, 0)
                _delete_recursive(root, f"{path}\\{sub}")
            except OSError:
                break
    winreg.DeleteKey(root, path)


def _delete_all_prefixed(root, parent: str, prefix: str):
    """Xóa tất cả key con trong parent có tên bắt đầu bằng prefix."""
    try:
        with winreg.OpenKey(root, parent, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            i = 0
            to_delete = []
            while True:
                try:
                    sub = winreg.EnumKey(key, i)
                    if sub.startswith(prefix):
                        to_delete.append(sub)
                    i += 1
                except OSError:
                    break
    except FileNotFoundError:
        return

    for sub in to_delete:
        _delete_tree_safe(root, f"{parent}\\{sub}")



