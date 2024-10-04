# Base Class for DanMu
from collections import deque

class DanMu:
    __slots__ = ('type', 'text', 'start_time', 'end_time', 'color', 'fontsize', 'start_x', 'start_y', 'end_x', 'end_y')
    
    fontname = 'Microsoft YaHei UI'
    
    def __init__(self, type=0, text='', start_time=0.0, end_time=0.0,
                 color=(255, 255, 255, 0.8), fontsize=25):
        self.type = type
        self.text = text
        self.start_time = start_time
        self.end_time = end_time
        self.start_x: float = 0
        self.start_y: float = 0
        self.end_x: float = 0
        self.end_y: float = 0

        # Styles
        self.color = color
        self.fontsize = fontsize

    def __repr__(self) -> str:
        return f"DanMu({self.type}, {self.text}, {self.start_time}, {self.start_x}, {self.start_y}, {self.end_x}, {self.end_y})"


class DanMuPool:
    def __init__(self, danmu_list):
        self.danmu_list = deque(sorted(danmu_list, key=lambda danmu: danmu.start_time))
        self.fixed_top_available_rows = set()
        self.fixed_bottom_available_rows = set()

    def __len__(self):
        return len(self.danmu_list)

if __name__ == "__main__":
    pass