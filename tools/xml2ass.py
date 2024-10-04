import os
import sys
import xml.etree.ElementTree as ET
import argparse


def format_time_ass(seconds):
    """Helper function to format seconds to ASS time format H:MM:SS.CS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    centiseconds = int((seconds - int(seconds)) * 100)  # Extract centiseconds
    return f"{hours:01}:{minutes:02}:{int(seconds):02}.{centiseconds:02}"

def bilibili_ass(event, log):
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
            style_name = "Bottom"
            end = start + 4
            log["last_bottom"] = end
        case "5": # 顶部字幕
            style_name = "Top"
            end = start + 4
            log["last_top"] = end
        case "6": # 逆向字幕
            style_name = "L2R"
            end = start + 8
        case _:
            pass
        
    if start is None or end is None:
        print(f"Warning: Missing 'start' or 'end' attribute in event. Skipping event.")
        return None
    
    start_time = format_time_ass(float(start))
    end_time = format_time_ass(float(end))
    
    return f"Dialogue: 0,{start_time},{end_time},{style_name},,20,20,2,,{text}"


def convert_xml_to_ass(input_file, output_file, style_name="Default"):
    # Check if the input file exists
    if not os.path.isfile(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        return
    
    # Parse the XML file
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error: Failed to parse XML file '{input_file}'. {e}")
        return
    
    # Create the header for the ASS file
    header = f"""
[Script Info]
Title: Converted from XML
ScriptType: v4.00+
Collisions: Normal
PlayDepth: 0
Timer: 100.0000
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: {style_name},黑体,25,&H66FFFFFF,&H66FFFFFF,&H66000000,&H66000000,1,0,0,0,100,100,0,0,1,2,0,2,20,20,2,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    # List to hold formatted dialogue lines
    dialogues = []
    
    for event in root.iter('d'):
        # Get the 'text' element
        text_elem = event.text or ''
        if text_elem is None:
            print(f"Warning: No 'text' element found in the 'event' element. Skipping event.")
            continue

        # Get attributes
        pos_log = {"last_top": None, "last_bottom": None}
        dialogue = bilibili_ass(event, pos_log)

        # Create a dialogue line for ASS
        dialogues.append(dialogue)

    # Write the header and dialogue lines to the output ASS file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(header.strip() + '\n' + '\n'.join(dialogues))

    print(f"Successfully converted '{input_file}' to '{output_file}'.")


def main(args):
    parser = argparse.ArgumentParser(description='Convert XML file to ASS format.')
    parser.add_argument('-i', '--input_file', type=str, required=True, help='Path to the input XML file.')
    parser.add_argument('-o', '--output_file', type=str, required=True, help='Path to the output ASS file.')
    parser.add_argument('-s', '--style', type=str, default='Default', help='Style name to use for the output ASS file.')
    args = parser.parse_args(args)

    convert_xml_to_ass(args.input_file, args.output_file, args.style)

if __name__ == '__main__':
    main(sys.argv[1:])
