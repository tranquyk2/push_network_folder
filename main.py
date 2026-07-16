import sys
import atexit

from PyQt6.QtWidgets import QApplication

from database import init_db
from config import load_config
from context_menu import register as register_context_menu, unregister as unregister_context_menu
from widgets.main_window import MainWindow


def main():
   
    if "--dest" in sys.argv:
        from shell_handler import main as shell_main
        shell_main()
        return

    init_db()

    
    cfg = load_config()
    register_context_menu(cfg.get("destinations", {}))
    atexit.register(unregister_context_menu)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  

    
    from pathlib import Path
    from PyQt6.QtGui import QIcon
    app.setWindowIcon(QIcon(str(Path(__file__).resolve().parent / "folder.ico")))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()