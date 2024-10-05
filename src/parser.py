from danmu import DanMu, DanMuPool
import ass, xml.etree.ElementTree as ET
import os, re


def RRGGBB(color):
    return f'{int(color):06X}'

def hexAlpha(opacity):
    alpha = f'{int(0xFF * (1 - opacity)):02X}'
    return alpha


def bili_xml(event):
    text = event.text
    attrs = event.get('p').split(',')
    
    time, style, size, color, timestamp, pool, uid_crc32, row_id = attrs
    start = float(time)
    style_name = "R2L"
    match style:
        case "1": # 滚动字幕
            style_name = "R2L"
            end = start + 8
        case "4": # 底部字幕
            style_name = "BOTTOM"
            end = start + 4
        case "5": # 顶部字幕
            style_name = "TOP"
            end = start + 4
        case "6": # 逆向字幕
            style_name = "L2R"
            end = start + 8
        case _:
            pass
        
    if start is None or end is None:
        print(f"Warning: Missing 'start' or 'end' attribute in event. Skipping event.")
        return None
    
    hex_color = RRGGBB(int(color) & 0xFFFFFF)
    return DanMu(style_name, text, float(start), float(end), color=color_format(hex_color), fontsize=int(size))

def read_xml(filename):
    if not os.path.isfile(filename):
        raise FileExistsError(f"Error: Input file '{filename}' does not exist.")
    
    # Parse the XML file
    try:
        tree = ET.parse(filename)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error: Failed to parse XML file '{filename}'. {e}")
        return
    
    danmus = []
    for event in root.iter('d'):
        danmus.append(bili_xml(event))

    print(f"Read {len(danmus)} DanMu from {filename}.")
    return DanMuPool(danmus)

def read_ass(filename):
    if filename.endswith('.ass'):
        with open(filename, 'r', encoding='utf-8-sig') as f:
            doc = ass.parse(f)

        danmu_list = [
            create_by_ass(evt, doc.play_res_x, doc.play_res_y)
            for evt in doc.events
        ]

        return DanMuPool(danmu_list)
    elif filename.endswith('.xml'):
        raise NotImplementedError('Conversion from XML to ASS is not implemented.')
    else:
        raise ValueError(f'Unsupported file format: {filename}')


def create_by_ass(evt, play_res_x, play_res_y):
    instance = DanMu()

    # Extract text after the first '}'
    instance.text = evt.text.partition('}')[2]

    # Time
    instance.start_time = evt.start.total_seconds()
    instance.end_time = evt.end.total_seconds()

    # Style
    color_match = re.search(r'\\c&H([0-9A-Fa-f]{6})&?', evt.text)
    if color_match:
        instance.color = color_format(color_match.group(1))
    else:
        instance.color = (255, 255, 255, 0.8*255)

    # Position and Type
    if evt.style == 'R2L':
        pos = re.findall(r"([-]?[0-9]+(?:\.[0-9]*)?)", evt.text)[0:4]
        instance.start_x = float(pos[0]) / play_res_x
        instance.start_y = float(pos[1]) / play_res_y
        instance.end_x = float(pos[2]) / play_res_x
        instance.end_y = float(pos[3]) / play_res_y
        instance.type = 'R2L'  # Scrolling
    elif evt.style == 'Fix':
        pos = re.findall(r"([-]?[0-9]+(?:\.[0-9]*)?)", evt.text)[0:2]
        instance.start_x = float(pos[0]) / play_res_x
        instance.start_y = float(pos[1]) / play_res_y
        instance.end_x = instance.start_x
        instance.end_y = instance.start_y
        instance.type = 'TOP' if float(pos[1]) < play_res_y * 0.5 else 'BOTTOM'  # Fixed Top or Bottom
    else:
        raise ValueError(f'Undefined Style: {evt.style}')
    
    # print(evt, color_match)
    return instance


def color_format(hex_color):
    # Convert ASS color code to RGBA
    bb, gg, rr = hex_color[0:2], hex_color[2:4], hex_color[4:6]
    return (int(rr, 16), int(gg, 16), int(bb, 16), 0.8*255)

if __name__ == '__main__':
    danmu_list = read_xml("./examples/danmu.xml")
    