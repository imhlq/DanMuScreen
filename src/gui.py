import os, sys
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QFileDialog, QInputDialog, QSystemTrayIcon, QMenu,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimer
from PySide6.QtGui import QFont, QFontMetrics, QIcon, QAction
import parser
import settings


class DanMuLabel(QLabel):
    pass

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = 'DanMu Screen'
        self.animations = []
        
        self.init_config()
        self.init_ui()

    def init_config(self):
        self.config = settings.DanMuConfig()
        
        # Initialize playback variables
        self.shift_time = 0  # in seconds
        self.start_time = time.time()
        self.current_danmu_id = 0

    def init_ui(self):
        # Set up the main window
        self.setWindowTitle(self.title)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.screen_geometry = QApplication.instance().primaryScreen().geometry()
        self.setGeometry(self.screen_geometry)
        self.setFixedSize(self.size())

        # Read ASS File
        self.open_file()

    def open_file(self):
        fname = self.open_file_dialog()
        if fname:
            self.style_list, self.danmu_list = parser.read_ass(fname)
            self.danmu_start_times = [danmu.start for danmu in self.danmu_list]
            self.total_time = max(self.danmu_start_times)

            print(f'Total DanMu loaded: {len(self.danmu_list)}')
            
            # Timer setup
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.tick)
            self.timer.start(50)  # Tick every 50 milliseconds
        
            self.init_config()

    def open_file_dialog(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open DanMu File", "", 
            "Ass Files (*.ass);; All Files (*.*)", options=options
        )
        return file_name

    def send_one(self, danmu_item):
        # Constants for positioning
        TOP_MARGIN = -50
        IN_MARGIN = 0.7

        duration = int((danmu_item.end - danmu_item.start) * 1000 / self.config.speed_multiplier)  # Duration in milliseconds

        # Font metrics
        font_size = danmu_item.fontsize * self.config.font_size_multiplier
        font = QFont(danmu_item.fontname, font_size)
        font_metrics = QFontMetrics(font)
        text_width = font_metrics.horizontalAdvance(danmu_item.text)
        text_height = font_metrics.height()

        # Start and end positions
        start_x = danmu_item.start_x * self.screen_geometry.width() - text_width / 2
        end_x = danmu_item.end_x * self.screen_geometry.width() - text_width / 2

        if danmu_item.type != 3:
            start_y = danmu_item.start_y * self.screen_geometry.height() * IN_MARGIN + TOP_MARGIN
            end_y = danmu_item.end_y * self.screen_geometry.height() * IN_MARGIN + TOP_MARGIN
        else:
            start_y = danmu_item.start_y * self.screen_geometry.height()
            end_y = danmu_item.end_y * self.screen_geometry.height()

        # Create label
        label = DanMuLabel(danmu_item.text, self)
        label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        label.setStyleSheet(
            f"font-family: {danmu_item.fontname}; font-size: {font_size}pt; color: {danmu_item.color};"
        )
        label.show()

        # Start animation
        self.fly(label, duration, (start_x, start_y), (end_x, end_y))

    def fly(self, label, duration, start_pos, end_pos):
        anim = QPropertyAnimation(label, b"pos", self)
        anim.setDuration(duration)
        anim.setStartValue(QPoint(*start_pos))
        anim.setEndValue(QPoint(*end_pos))
        anim.setEasingCurve(QEasingCurve.Linear)
        
        def on_finished():
            label.deleteLater()
            self.animations.remove(anim)
            
        anim.finished.connect(on_finished)
        anim.start()
        self.animations.append(anim)  # Keep reference to prevent garbage collection

    def tick(self):
        now = time.time()
        elapsed = now - self.start_time + self.shift_time

        # Send DanMus that are due
        while (
            self.current_danmu_id < len(self.danmu_list) and
            elapsed >= self.danmu_list[self.current_danmu_id].start
        ):
            self.send_one(self.danmu_list[self.current_danmu_id])
            self.current_danmu_id += 1

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.text() == ',':
            # Rewind by 2 seconds
            self.shift_time -= 2
            self.update_current_danmu_id()
            self.clear_DanMu()
        elif event.text() == '.':
            # Fast-forward by 2 seconds
            self.shift_time += 2
            self.update_current_danmu_id()
        elif event.key() == Qt.Key_Space:
            # Jump to a percentage of the video
            percentage, ok = QInputDialog.getInt(
                self, "Please input progress", "Percentage:", 0, 0, 100, 1
            )
            if ok:
                self.current_danmu_id = int(len(self.danmu_list) * (percentage / 100))
                self.shift_time = self.danmu_list[self.current_danmu_id].start - (time.time() - self.start_time)
                self.clear_DanMu()
    
    def get_current_time(self):
        return self.danmu_list[self.current_danmu_id].start

    def get_total_time(self):
        return self.total_time

    def update_current_danmu_id(self):
        # Update current_danmu_id based on the new shift_time
        elapsed = time.time() - self.start_time + self.shift_time
        self.current_danmu_id = next(
            (i for i, danmu in enumerate(self.danmu_list) if danmu.start >= elapsed),
            len(self.danmu_list)
        )

    def clear_DanMu(self):
        # Remove all labels and animations
        for anim in self.animations:
            anim.stop()
        self.animations.clear()
        for widget in self.findChildren(DanMuLabel):
            widget.deleteLater()
    
    def rewind(self, seconds=2):
        self.shift_time -= seconds
        self.update_current_danmu_id()
        self.clear_DanMu()
    
    def fast_forward(self, seconds=2):
        self.shift_time += seconds
        self.update_current_danmu_id()
        self.clear_DanMu()
        
    def play_pause(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start()
        
    def show_settings_dialog(self):
        settings.settings_dialog(self)
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    ex = App()
    ex.show()
    
    # System Tray Icon
    icon = QIcon("./icons.ico")
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
