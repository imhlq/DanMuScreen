import math
import sys
import re
import argparse
import xml.etree.ElementTree as ET
from tqdm import tqdm
from collections import deque
from heapq import heappush, heappop

# Configuration dictionary
config = {
    'playResX': 560,
    'playResY': 420,
    'fontlist': [
        'Microsoft YaHei UI',
        'Microsoft YaHei',
        'WenQuanYi Zen Hei',
        'STHeitiSC',
        'HeiTi'
    ],
    'font_size': 1.0,
    'r2ltime': 8,
    'fixtime': 4,
    'opacity': 0.6,
    'space': 0,
    'max_delay': 6,
    'bottom': 50,
    'use_canvas': None,
    'debug': False
}

def debug(msg, *args):
    if config['debug']:
        print(msg % args)

def RRGGBB(color):
    return f'{int(color):06X}'

def hexAlpha(opacity):
    alpha = f'{int(0xFF * (1 - opacity)):02X}'
    return alpha

def hypot(*args):
    return math.hypot(*args)

def calc_width(text, fontsize):
    # Simplistic assumption: each character width = fontsize
    return len(text) * fontsize

def chose_font(fontlist):
    # Placeholder function since font availability check requires GUI or specific libraries.
    return fontlist[0] if fontlist else 'Default Font'

def format_time(time):
    """
    Convert a time in seconds to the ASS format (hh:mm:ss.ms).
    If time is not a valid number, return a default time '0:00:00.00'.
    """
    if time == float('inf'):
        return '0:00:00.00'
    
    hours = int(time // 3600)
    minutes = int((time % 3600) // 60)
    seconds = int(time % 60)
    milliseconds = int((time * 100) % 100)
    return f'{hours:01}:{minutes:02}:{seconds:02}.{milliseconds:02}'

def escape_ass_text(s):
    """Escape specific characters to be compatible with ASS format."""
    return s.replace("{", "｛").replace("}", "｝").replace("\r", "").replace("\n", "")

def convert2Ass(line):
    """
    Convert a danmu line to ASS dialogue format.
    """
    # Escape text and set initial ASS string
    ass_text = escape_ass_text(line['text'])

    # Determine color and styling
    common_styles = ''
    rgb = [int(line['color'][i:i+2], 16) for i in range(0, len(line['color']), 2)]  # Convert RRGGBB to [R, G, B]
    if line['color'] != 'FFFFFF':  # Default white
        common_styles += f'\\c&H{line["color"][4:6]}{line["color"][2:4]}{line["color"][0:2]}&'  # Change color to &HBBGGRR

    # Check if color is considered dark, and set white border for dark colors
    dark = rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114 < 0x30
    if dark:
        common_styles += '\\3c&HFFFFFF'  # White border color
    if line['size'] != 25:
        common_styles += f'\\fs{line["size"]}'  # Font size override

    # Determine the movement or positioning of the danmu
    if line['type'] == 'R2L':
        effect_styles = f'\\move({line["poss"]["x"]},{line["poss"]["y"]},{line["posd"]["x"]},{line["posd"]["y"]})'
    elif line['type'] == 'Fix':
        effect_styles = f'\\pos({line["poss"]["x"]},{line["poss"]["y"]})'
    else:
        effect_styles = ''

    # Combine all styles
    styles = effect_styles + common_styles

    # Generate the final ASS dialogue line
    return f'Dialogue: 0,{format_time(line["stime"])},{format_time(line["dtime"])},{line["type"]},,20,20,2,,{{{styles}}}{ass_text}'

def generate_ass(danmu):
    config['font'] = chose_font(config['fontlist'])
    ass_header_template = """[Script Info]
Title: DanMuScreen
Original Script: xHou.me
ScriptType: v4.00+
Collisions: Normal
PlayResX: {playResX}
PlayResY: {playResY}
Timer: 10.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Fix,{font},25,&H{alpha}FFFFFF,&H{alpha}FFFFFF,&H{alpha}000000,&H{alpha}000000,1,0,0,0,100,100,0,0,1,2,0,2,20,20,2,0
Style: R2L,{font},25,&H{alpha}FFFFFF,&H{alpha}FFFFFF,&H{alpha}000000,&H{alpha}000000,1,0,0,0,100,100,0,0,1,2,0,2,20,20,2,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    header_values = {**config, 'alpha': hexAlpha(config['opacity'])}
    ass_header = ass_header_template.format(**header_values)
    danmu = set_position(danmu)
    
    # Create the ASS content, showing a progress bar while processing
    ass_lines = []
    print("Generating ASS content with visual progress:")
    for line in tqdm(danmu, desc="Processing danmu", unit="line"):
        ass_lines.append(convert2Ass(line))

    return ass_header + '\n' + '\n'.join(ass_lines)

def normal_danmu(screen_width, screen_height, bottom_margin, duration, max_r):
    """
    Optimized function to handle right-to-left scrolling danmu placement.
    """
    # Track active danmu as a heap-based priority queue for quick removals and additions
    active_danmu = []

    def add_danmu(appearance_time, width, height, is_bottom_aligned):
        exit_time = screen_width / (width + screen_width) * duration + appearance_time
        deactivate_time = duration + appearance_time

        # Clean up expired danmu before adding new ones
        while active_danmu and active_danmu[0][0] <= appearance_time:
            heappop(active_danmu)

        # Find the best position by scoring all potential options
        best_score, best_position = float('-inf'), None
        for i in range(0, screen_height - height - bottom_margin, height + 5):
            conflict = any(
                (danmu_start <= exit_time and appearance_time <= danmu_end and pos <= i < pos + height)
                for (danmu_end, danmu_start, pos) in active_danmu
            )
            if not conflict:
                # Calculate distance and score
                distance = abs(screen_height / 2 - i) / screen_height
                score = 1 - math.sqrt(distance ** 2 / 2)
                if score > best_score:
                    best_score, best_position = score, i

        if best_position is not None:
            heappush(active_danmu, (deactivate_time, appearance_time, best_position))
            return {'top': best_position, 'time': appearance_time}
        return None

    return add_danmu

def side_danmu(screen_height, bottom_margin, duration, max_r):
    """
    Optimized function to handle fixed danmu placement at the top or bottom of the screen.
    """
    # Track active danmu in a deque for efficient insertions and deletions
    active_danmu = deque()

    def add_danmu(appearance_time, height, is_top, is_bottom_aligned):
        exit_time = appearance_time + duration

        # Clean up expired danmu
        while active_danmu and active_danmu[0][0] <= appearance_time:
            active_danmu.popleft()

        # Try to place the danmu at either the top or bottom
        best_score, best_position = float('-inf'), None
        positions = range(0, screen_height - height - bottom_margin, height + 5)
        if not is_top:
            positions = reversed(positions)

        for i in positions:
            conflict = any(pos <= i < pos + height for _, _, pos in active_danmu)
            if not conflict:
                # Calculate score based on distance and alignment
                distance = abs(screen_height / 2 - i) / screen_height
                alignment_score = 1 if is_top else 0.5
                score = 1 - math.sqrt(distance ** 2 * alignment_score)
                if score > best_score:
                    best_score, best_position = score, i

        if best_position is not None:
            active_danmu.append((exit_time, appearance_time, best_position))
            return {'top': best_position, 'time': appearance_time}
        return None

    return add_danmu

def set_position(danmu):
    normal = normal_danmu(config['playResX'], config['playResY'], config['bottom'], config['r2ltime'], config['max_delay'])
    side = side_danmu(config['playResY'], config['bottom'], config['fixtime'], config['max_delay'])

    danmu = sorted(danmu, key=lambda x: x['time'])
    for line in tqdm(danmu, desc="Setting danmu position", unit="line"):
        font_size = round(line['size'] * config['font_size'])
        width = calc_width(line['text'], font_size)
        if line['mode'] == 'R2L':
            pos = normal(line['time'], width, font_size, line['bottom'])
            if not pos:
                continue
            line['type'] = 'R2L'
            line['stime'] = pos['time']
            line['poss'] = {'x': config['playResX'] + width / 2, 'y': pos['top'] + font_size}
            line['posd'] = {'x': -width / 2, 'y': pos['top'] + font_size}
            line['dtime'] = config['r2ltime'] + line['stime']
        elif line['mode'] in ['TOP', 'BOTTOM']:
            is_top = line['mode'] == 'TOP'
            pos = side(line['time'], font_size, is_top, line['bottom'])
            if not pos:
                continue
            line['type'] = 'Fix'
            line['stime'] = pos['time']
            line['posd'] = line['poss'] = {'x': config['playResX'] / 2, 'y': pos['top'] + font_size}
            line['dtime'] = config['fixtime'] + line['stime']

    filtered = [line for line in danmu if 'dtime' in line and line['dtime'] != float('inf')]
    return [line for line in filtered if 'stime' in line]

def parse_xml(content):
    """
    Parse XML content and return a list of dictionaries representing danmu.
    """
    root = ET.fromstring(content)
    danmu_list = []

    mode_mapping = {1: 'R2L', 2: 'R2L', 3: 'R2L', 4: 'BOTTOM', 5: 'TOP'}

    for elem in root.findall('d'):
        p_attr = elem.get('p')
        if not p_attr:
            continue

        attributes = p_attr.split(',')
        if len(attributes) < 6:
            continue

        try:
            time = float(attributes[0])
            mode_index = int(attributes[1])
            mode = mode_mapping.get(mode_index, 'UNKNOWN')
            size = int(attributes[2])
            color_int = int(attributes[3])
            color = RRGGBB(color_int & 0xFFFFFF)
            timestamp = int(attributes[4])
            pool = int(attributes[5])
            bottom = pool > 0
        except (ValueError, IndexError):
            continue

        text = elem.text or ""

        line = {
            'text': text,
            'time': time,
            'mode': mode,
            'size': size,
            'color': color,
            'bottom': bottom,
        }

        danmu_list.append(line)

    return danmu_list

def write_file(data, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(data)

def main(args):
    parser = argparse.ArgumentParser(description='Convert XML file to ASS format.')
    parser.add_argument('-i', '--input_file', type=str, required=True, help='Path to the input XML file.')
    parser.add_argument('-o', '--output_file', type=str, required=True, help='Path to the output ASS file.')
    args = parser.parse_args(args)

    with open(args.input_file, 'r', encoding='utf-8') as f:
        danmu_xml = f.read()
    danmu = parse_xml(danmu_xml)
    print(f'Parsed {len(danmu)} lines.')
    ass_content = generate_ass(danmu)
    print(f"Generated {len(ass_content)} lines.")
    write_file(ass_content, args.output_file)
    print('Done.')

if __name__ == '__main__':
    main(sys.argv[1:])
