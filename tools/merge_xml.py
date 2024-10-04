import os
import sys
import xml.etree.ElementTree as ET
import argparse

def format_value(value):
    if value >= 1E3:
        return f"{value//1000}k"
    elif value >= 1E6:
        return f"{value//1E6}M"
    else:
        return str(value)

def merge_xml_files(input_dir, output_file):
    # Check if the input directory exists
    if not os.path.isdir(input_dir):
        raise ValueError(f"The specified directory '{input_dir}' does not exist.")

    # Create root element for the merged XML
    root = ET.Element('root')
    seen_elements = set()  # To store unique identifiers of elements
    elements_set = []  # To keep a list of elements for sorting

    # Iterate through XML files in the directory
    xml_files = [f for f in os.listdir(input_dir) if f.endswith('.xml')]

    # Check if there are XML files in the input directory
    if not xml_files:
        raise ValueError(f"No XML files found in the specified directory '{input_dir}'.")

    total_xml_files = len(xml_files)
    merged_count = 0  # Counter for merged `<d>` elements
    for i, xml_file in enumerate(xml_files):
        print(f"Merging XML file {i+1} of {total_xml_files}: {xml_file}", end='\r')
        xml_path = os.path.join(input_dir, xml_file)
        try:
            tree = ET.parse(xml_path)
            root_element = tree.getroot()
            for elem in root_element.findall(".//d"):
                elem_id = ET.tostring(elem, encoding='unicode')
                if elem_id not in seen_elements:
                    seen_elements.add(elem_id)
                    elements_set.append(elem)   # Store the element itself
                    merged_count += 1

        except ET.ParseError:
            print(f"Warning: '{xml_file}' is not a valid XML file and was skipped.")

    sorted_elements = sorted(elements_set, key=lambda x: float(x.attrib['p'].split(',')[0]))
    for elem in sorted_elements:
        root.append(elem)

    # Write the merged XML to the output file
    merged_tree = ET.ElementTree(root)
    merged_tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    print(f'\nSuccessfully merged {len(xml_files)} XML files into {output_file}.')
    print(f'{format_value(merged_count)} elements were merged.')

def main(args):
    parser = argparse.ArgumentParser(description='Merge multiple XML files into a single XML file.')
    parser.add_argument('-i', '--input_dir', type=str, required=True, help='Directory containing XML files to merge.')
    parser.add_argument('-o', '--output_file', type=str, required=True, help='Path for the output merged XML file.')
    args = parser.parse_args(args)

    # Call the function to merge XML files
    merge_xml_files(args.input_dir, args.output_file)

if __name__ == '__main__':
    main(sys.argv[1:])
