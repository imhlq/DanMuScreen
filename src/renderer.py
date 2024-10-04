from PySide6.QtGui import QFont, QColor, QPainter, QFontMetrics
from PySide6.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimer
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsTextItem, QGraphicsItem
)
# from PySide6.QtOpenGLWidgets import QOpenGLWidget
import time
from parser import read_xml
from danmu import DanMu, DanMuPool
import heapq
import random


class DanMuLabel(QGraphicsTextItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class DanMuMachine():
    """Base class for DanMu rendering. Manager Timer, and DanMu Rendering."""
    
    label_pool = []  # Keep track of labels to reuse when possible.
    animations = []
    animation_pool = []
    font_metrics_cache = {}
    danmu_pool: DanMuPool

    def __init__(self, parent, n_workers=1):
        self.parent = parent
        self.view = QGraphicsView(self.parent)
        # self.view.setViewport(QOpenGLWidget()) not work.
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.view.setStyleSheet("background: transparent; border: none;")
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.max_danmu_count = 200
        self.n_workers: int = n_workers
        self.current_index = 0
        self.timer = None
        self.screen_geometry = self.parent.screen_geometry.width(), self.parent.screen_geometry.height()
        self.parent.setCentralWidget(self.view)
        self.scene.setSceneRect(0, 0, self.screen_geometry[0], self.screen_geometry[1])
        
        self.row_height = 25
        
        self.speed_multiplier = 1.0
        self.font_size_multiplier = 1.0
        
        # Overlapping management
        self.max_scroll_rows = min(self.screen_geometry[1] // self.row_height - 1, 50)

        
    def reset_time(self):
        self.shift_time = 0  # in seconds
        self.start_time = time.time()
        self.current_danmu_id = 0
        self.scroll_overlap_heap = [(0, i) for i in range(self.max_scroll_rows)]
        self.fixed_top_rows = [(0, i) for i in range(self.max_scroll_rows)]
        self.fixed_bottom_rows = [(0, i) for i in range(self.max_scroll_rows)]
        heapq.heapify(self.scroll_overlap_heap)
        self.active_danmus = 0
        
        # Timer setup
        if not self.timer:
            self.timer = QTimer(self.parent)
        self.timer.timeout.connect(self.tick)
        self.timer.start(26)  # ~30 fps
    
    def tick(self):
        now = time.time()
        elapsed = now - self.start_time + self.shift_time

        # Send DanMus that are due
        while (
            self.current_danmu_id < len(self.danmu_pool) and
            elapsed >= self.danmu_pool.danmu_list[self.current_danmu_id].start_time
        ):
            self.send_one(self.danmu_pool.danmu_list[self.current_danmu_id], now)
            self.current_danmu_id += 1
        
    def calculate_initial_position(
        self, danmu, screen_width, screen_height, text_width, text_height, current_time, duration_in_seconds
    ):
        """Calculate the initial position for DanMu to avoid overlap."""
        # Constants for positioning
        TOP_MARGIN = 25
        BOTTOM_MARGIN = 50
        
        if danmu.type in ['R2L', 'L2R']:  # Scrolls
            available_time, n_row = heapq.heappop(self.scroll_overlap_heap)
            danmu.start_y = n_row * self.row_height + TOP_MARGIN
            danmu.end_y = danmu.start_y
            # Update the available time for this row
            new_available_time = current_time + duration_in_seconds / 5
            heapq.heappush(self.scroll_overlap_heap, (new_available_time, n_row))
            
            if danmu.type == 'R2L':  # Right to Left
                danmu.start_x = screen_width
                danmu.end_x = - text_width
            else:
                danmu.start_x = -text_width
                danmu.end_x = screen_width            

        elif danmu.type == 'TOP':  # Fixed Top
            # Allocate the next available row for fixed top
            if self.fixed_top_rows:
                available_time, row = heapq.heappop(self.fixed_top_rows)
            else:
                row = 0
            danmu.start_x = (screen_width - text_width) / 2
            danmu.end_x = danmu.start_x  # Fixed position
            danmu.start_y = row * self.row_height + TOP_MARGIN
            danmu.end_y = danmu.start_y
            new_available_time = current_time + duration_in_seconds
            heapq.heappush(self.fixed_top_rows, (new_available_time, row))
            
        elif danmu.type == 'BOTTOM':  # Fixed Bottom
            if self.fixed_bottom_rows:
                available_time, row = heapq.heappop(self.fixed_bottom_rows)
            else:
                row = 0
            danmu.start_x = (screen_width - text_width) / 2
            danmu.end_x = danmu.start_x  # Fixed position
            danmu.start_y = screen_height - BOTTOM_MARGIN - ((row + 1) * self.row_height)
            danmu.end_y = danmu.start_y
            new_available_time = current_time + duration_in_seconds
            heapq.heappush(self.fixed_bottom_rows, (new_available_time, row))

        # Ensure rows don't exceed screen height or become negative
        danmu.start_y = max(0, min(danmu.start_y, screen_height - BOTTOM_MARGIN - self.row_height))


    def get_font_metrics(self, fontname, fontsize: int):
        key = (fontname, fontsize)
        if key not in self.font_metrics_cache:
            font = QFont(fontname, fontsize)
            self.font_metrics_cache[key] = QFontMetrics(font)
        return self.font_metrics_cache[key]
    
    def create_label(self, text, text_width, text_height):
        if self.label_pool:
            label = self.label_pool.pop()
            label.setPlainText(text)
        else:
            label = QGraphicsTextItem(text)
            label.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
            self.scene.addItem(label)
        return label
    
    def send_one(self, danmu_item: DanMu, current_time):
        acceptance_prob = 2.0 - (self.active_danmus / self.max_danmu_count)
        # print(f"{self.active_danmus} ({acceptance_prob})")
        if random.random() > acceptance_prob:
            return # soft reject
            
        duration = int(
            (danmu_item.end_time - danmu_item.start_time) * 1000 / self.speed_multiplier
        )  # Duration in milliseconds
        duration_in_seconds = duration / 1000.0
        # Font metrics
        font_size = int(danmu_item.fontsize * self.font_size_multiplier)
        font_metrics = self.get_font_metrics(danmu_item.fontname, font_size)
        text_width = font_metrics.horizontalAdvance(danmu_item.text)
        text_height = font_metrics.height()
        
        # Start and end positions
        self.calculate_initial_position(
            danmu_item, self.screen_geometry[0], self.screen_geometry[1], text_width, text_height,
            current_time, duration_in_seconds,
        )

        # Create label
        label = self.create_label(danmu_item.text, text_width, text_height)
        label.setDefaultTextColor(QColor(danmu_item.color[0], danmu_item.color[1], danmu_item.color[2], danmu_item.color[3]))
        label.setFont(QFont(danmu_item.fontname, font_size))
        label.show()

        # Start animation
        self.fly(label, duration, (danmu_item.start_x, danmu_item.start_y), (danmu_item.end_x, danmu_item.end_y))

    def fly(self, label, duration, start_pos, end_pos):
        if len(self.animation_pool) > 3:
            anim = self.animation_pool.pop()
            if anim.state() != QPropertyAnimation.Stopped: anim.stop()
            anim.setTargetObject(label)
        else:
            anim = QPropertyAnimation(label, b"pos", self.parent)
        
        anim.setDuration(duration)
        anim.setStartValue(QPoint(*start_pos))
        anim.setEndValue(QPoint(*end_pos))
        anim.setEasingCurve(QEasingCurve.Linear)
        
        def on_finished():
            if label.isVisible(): label.hide()
            label.update()
            self.label_pool.append(label)
            self.animation_pool.append(anim)
            self.active_danmus -= 1
            anim.finished.disconnect()
        
        anim.finished.connect(on_finished)
        anim.start()
        self.active_danmus += 1

    def rewind(self, seconds=2):
        self.shift_time -= seconds
        self.update_current_danmu_id()
        self.clear_danmu()
    
    def fast_forward(self, seconds=2):
        self.shift_time += seconds
        self.update_current_danmu_id()
        self.clear_danmu()
        
    def play_pause(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start()
        
    def jump_to_percentage(self, percentage):
        self.current_danmu_id = int(len(self.danmu_list) * (percentage / 100))
        self.shift_time = self.danmu_list[self.current_danmu_id].start - (time.time() - self.start_time)
        self.clear_danmu()

    def update_current_danmu_id(self):
        # Update current_danmu_id based on the new shift_time
        elapsed = time.time() - self.start_time + self.shift_time
        self.current_danmu_id = next(
            (i for i, danmu in enumerate(self.danmu_list) if danmu.start >= elapsed),
            len(self.danmu_list)
        )

    def clear_danmu(self):
        # Remove all labels and animations
        for anim in self.animation_pool:
            anim.stop()
        self.animation_pool.clear()
        for label in self.label_pool:
            label.deleteLater()
        self.label_pool.clear()
        self.scene.clear()
    

if __name__ == '__main__':
    pool = read_xml("./examples/danmu.xml")
    