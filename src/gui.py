import os, sys
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QFileDialog, QInputDialog, QSystemTrayIcon, QMenu,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimer
from PySide6.QtGui import QFont, QFontMetrics, QIcon, QAction
import parser
import settings
from renderer import DanMuMachine

import cProfile, pstats, io

class App(QMainWindow):
    
    def init_ui(self):
        # Set up the main window
        self.setWindowTitle(self.title)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.screen_geometry = QApplication.instance().primaryScreen().geometry()
        self.setGeometry(self.screen_geometry)
        self.setFixedSize(self.size())
        
    def __init__(self):
        super().__init__()
        self.title = 'DanMu Screen'
        self.init_ui()
        
        self.danmu_machine = DanMuMachine(self)
        
        self.open_file()

    def open_file(self):
        fname = self.open_file_dialog()
        if fname.endswith('.xml'):
            self.danmu_machine.danmu_pool = parser.read_xml(fname)
        elif fname.endswith('.ass'):
            self.danmu_machine.danmu_pool = parser.read_ass(fname)
        else:
            raise Exception(f'Unsupported file type: {fname}')
        print(f'Total DanMu loaded: {len(self.danmu_machine.danmu_pool)}')

        self.danmu_machine.reset_time()

    def open_file_dialog(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open DanMu File", "", 
            "DanMu File (*.xml *.ass);; All File (*.*)", options=options
        )
        return file_name

    def get_current_danmu(self):
        return self.danmu_machine.time

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.text() == ',':
            # Rewind by 2 seconds
            self.danmu_machine.rewind(2)
            self.danmu_machine.update_current_danmu_id()
            
        elif event.text() == '.':
            # Fast-forward by 2 seconds
            self.danmu_machine.fast_forward(2)
            self.danmu_machine.update_current_danmu_id()
            
        elif event.key() == Qt.Key_Space:
            self.show_settings_dialog()
    
    def show_settings_dialog(self):
        settings.settings_dialog(self)


def resource_path(relative_path):
    """ Get the absolute path to resource, works for both development and PyInstaller environments """
    try:
        # PyInstaller creates a temporary folder and stores the path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    ex = App()
    ex.show()
    
    # System Tray Icon
    icon = QIcon(resource_path("icons.ico"))
    tray = QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setVisible(True)
    ex.setWindowIcon(icon)
    
    menu = QMenu()
    open_action = QAction("Open")
    open_action.triggered.connect(ex.open_file)
    settings_action = QAction("Settings")
    settings_action.triggered.connect(ex.show_settings_dialog)
    quit_action = QAction("Quit")
    quit_action.triggered.connect(app.quit)
    menu.addAction(open_action)
    menu.addAction(settings_action)
    menu.addAction(quit_action)
    
    tray.setContextMenu(menu)
    
    app.exec()

if __name__ == "__main__":
    main()