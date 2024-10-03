import re

class DanMu:
    def __init__(self):
        self.text = ''
        self.start = 0.0
        self.end = 0.0
        self.color = 'rgba(255, 255, 255, 0.8)'
        self.fontname = 'Microsoft YaHei UI'
        self.fontsize = 20
        self.start_x = 0.0
        self.start_y = 0.0
        self.end_x = 0.0
        self.end_y = 0.0
        self.type = 0

    @classmethod
    def create_by_ass(cls, evt, play_res_x, play_res_y):
        instance = cls()

        # Extract text after the first '}'
        instance.text = evt.text.partition('}')[2]

        # Time
        instance.start = evt.start.total_seconds()
        instance.end = evt.end.total_seconds()

        # Style
        color_match = re.search(r'\\c&H([0-9A-Fa-f]{6})&?', evt.text)
        if color_match:
            instance.color = cls.color_format(color_match.group(1))
        else:
            instance.color = 'rgba(255, 255, 255, 0.8)'

        # Position and Type
        if evt.style == 'R2L':
            pos = re.findall(r"([-]?[0-9]+(?:\.[0-9]*)?)", evt.text)[0:4]
            instance.start_x = float(pos[0]) / play_res_x
            instance.start_y = float(pos[1]) / play_res_y
            instance.end_x = float(pos[2]) / play_res_x
            instance.end_y = float(pos[3]) / play_res_y
            instance.type = 1  # Scrolling
        elif evt.style == 'Fix':
            pos = re.findall(r"([-]?[0-9]+(?:\.[0-9]*)?)", evt.text)[0:2]
            instance.start_x = float(pos[0]) / play_res_x
            instance.start_y = float(pos[1]) / play_res_y
            instance.end_x = instance.start_x
            instance.end_y = instance.start_y
            instance.type = 2 if float(pos[1]) < play_res_y * 0.5 else 3  # Fixed Top or Bottom
        else:
            raise ValueError(f'Undefined Style: {evt.style}')
        
        print(evt, color_match)
        
        return instance

    @staticmethod
    def color_format(hex_color):
        # Convert ASS color code to RGBA
        bb, gg, rr = hex_color[0:2], hex_color[2:4], hex_color[4:6]
        return f'rgba({int(rr, 16)}, {int(gg, 16)}, {int(bb, 16)}, 0.8)'