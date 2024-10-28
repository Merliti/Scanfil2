from bs4 import BeautifulSoup
import argparse
import shutil
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import logging
from typing import Optional
from enum import Enum
from xml.dom import minidom

# Define the ExitCode Enum
class ExitCode(Enum):
    SUCCESS = 0
    CREATE_DIR_ERROR = 1
    READ_HTML_ERROR = 2
    PARSE_XML_ERROR = 3
    WRITE_XML_ERROR = 4
    ARCHIVE_ERROR = 5

# Directory name for archiving
dir_for_archiv = "arhiiv"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_html_file(file_path: str) -> Optional[str]:
    """
    Reads and returns HTML content from a specified file.

    Parameters:
        file_path (str): Path to the HTML file to read.

    Returns:
        Optional[str]: The HTML content of the file as a string if successful, 
                       or None if the file is empty or not found.
    """
    if not isinstance(file_path, str):
        raise TypeError("file_path must be a string representing the path to the HTML file.")

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            if not content:
                logging.error(f"The HTML file {file_path} is empty.")
                return None
            return content
    except FileNotFoundError as e:
        logging.error(f"Error reading HTML file: {e}")
        return None 

# Function to prettify the XML for human readability
def prettify_xml(element):
    """Formats XML with indentation for readability."""
    rough_string = ET.tostring(element, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def html_to_xml(html_content: str) -> Optional[str]:
    """
    Parses HTML content to extract specific information, validates essential fields,
    and constructs an XML structure from the data. Returns a prettified XML string
    or None if any critical field is missing or parsing errors occur.

    Args:
        html_content (str): HTML content as a string.

    Returns:
        str | None: A formatted XML string if successful, or None if an error occurs.
    """
    # Parse HTML content
    soup = BeautifulSoup(html_content, 'html.parser')
    data: dict[str, str] = {}

    # Extract data from HTML table rows
    for row in soup.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) == 2:
            header = cells[0].text.strip().replace(":", "")
            data[header] = cells[1].text.strip()

    # Retrieve and validate necessary fields
    station_id: str = data.get('Station ID', '')
    serial_number: str = data.get('Serial Number', '')
    sequence_name: str = data.get('Sequence Name', '')
    uut_result: str = data.get('UUT Result', '')
    date_str: str = data.get('Date', '')
    time_str: str = data.get('Time', '')
    execution_time_str: str = data.get('Execution Time', '0 seconds').split()[0]

    # Validate critical fields
    for field in ['Station ID', 'Serial Number', 'Sequence Name', 'UUT Result', 'Date', 'Time']:
        if field not in data:
            logging.error(f"Missing '{field}'")
            return None

    # Extract and parse additional fields
    try:
        execution_time: float = float(execution_time_str)
        status: str = 'PASS' if 'Passed' in uut_result else 'FAIL'
        start_time: datetime = datetime.strptime(f"{date_str.split()[-1]} {time_str.replace('.', ':')}", '%Y %H:%M:%S')
        end_time: datetime = start_time + timedelta(seconds=execution_time)
    except (ValueError, KeyError) as e:
        logging.error(f"Error parsing date, time, or execution time: {e}")
        return None

    # Build XML structure
    root: ET.Element = ET.Element('UGSTesterCom', {
        'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance",
        'xmlns:xsd': "http://www.w3.org/2001/XMLSchema",
        'Version': "2.0",
        'TesterType': "KONE FCT",
        'Testerlocation': "en-US"
    })

    # Populate XML elements with extracted data
    ET.SubElement(root, 'Barcode').text = serial_number
    ET.SubElement(root, 'TesterName').text = station_id
    ET.SubElement(root, 'StationName').text = station_id
    ET.SubElement(root, 'Station').text = station_id
    ET.SubElement(root, 'TestProgram').text = sequence_name
    ET.SubElement(root, 'Status').text = status
    ET.SubElement(root, 'StartTime').text = start_time.isoformat()
    ET.SubElement(root, 'EndTime').text = end_time.isoformat()
    ET.SubElement(root, 'TestSteps')

    # Return prettified XML
    return prettify_xml(root)

def parse_args() -> argparse.Namespace:
    """
    Parses command-line arguments for input and output directories, as well as an optional archive path.

    Returns:
        argparse.Namespace: Parsed command-line arguments with attributes:
            - dir1 (str): Path to the UUT report HTML file.
            - dir2 (str): Directory to save the generated XML file.
            - archive (str | None): Optional path to store processed files if specified.
    """
    # Initialize argument parser with a description
    parser = argparse.ArgumentParser(description='Parse UUT report from HTML to XML')

    # Define input/output file argument group
    file_group = parser.add_argument_group("Input/Output Files")
    file_group.add_argument(
        '-d1', '--dir1',
        required=True,
        help="Path to the UUT report HTML file."
    )
    file_group.add_argument(
        '-d2', '--dir2',
        required=True,
        help="Directory to save the XML file."
    )
    file_group.add_argument(
        '-a','--archive',
        required=False,
        help="Optional archive path to store processed files."
    )

    # Parse and return arguments
    return parser.parse_args()


def main(args: argparse.Namespace) -> ExitCode:
    """
    Main function for processing HTML to XML conversion and archiving.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.

    Returns:
        ExitCode: ExitCode.SUCCESS if successful, other ExitCode values if an error occurred.
    """
    # Set up output directory
    output_dir = args.dir2
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
            logging.info(f"Created directory: {output_dir}")
        except (PermissionError, OSError) as e:
            logging.error(f"Failed to create directory {output_dir}: {e}")
            return ExitCode.CREATE_DIR_ERROR

    # Prepare paths and file names
    base_name = os.path.splitext(os.path.basename(args.dir1))[0]
    output_xml_file = os.path.join(output_dir, f"{base_name}.xml")

    # Read and convert HTML
    html_content = read_html_file(args.dir1)
    if html_content is None:
        return ExitCode.READ_HTML_ERROR

    xml_content = html_to_xml(html_content)
    if xml_content is None:
        return ExitCode.PARSE_XML_ERROR
    
    # Check if the file already exists
    if os.path.exists(output_xml_file):
        logging.info(f"The file {output_xml_file} already exists and will be overwritten.")

    # Write XML to output file
    try:
        with open(output_xml_file, 'w', encoding='utf-8') as xml_file:
            xml_file.write(xml_content)
        logging.info(f"XML written to {output_xml_file}")
    except PermissionError as e:
        logging.error(f"Permission denied for writing {output_xml_file}: {e}")
        return ExitCode.WRITE_XML_ERROR

    # Set up archive directory
    archive_dir = args.archive or os.path.join(os.path.dirname(os.path.dirname(args.dir1)), dir_for_archiv)
    if not os.path.exists(archive_dir):
        try:
            os.makedirs(archive_dir, exist_ok=True)
            logging.info(f"Created archive directory: {archive_dir}")
        except (PermissionError, OSError) as e:
            logging.error(f"Failed to create archive directory {archive_dir}: {e}")
            return ExitCode.CREATE_DIR_ERROR

    # Move HTML to archive
    target_file_path = os.path.join(archive_dir, os.path.basename(args.dir1))
    try:
        if os.path.exists(target_file_path):
            os.remove(target_file_path)
            logging.info(f"Overwriting existing archive file: {target_file_path}")

        shutil.move(args.dir1, archive_dir)
        logging.info(f"Archived {args.dir1} to {archive_dir}")
    except (PermissionError, FileNotFoundError) as e:
        logging.error(f"Failed to archive HTML file {args.dir1}: {e}")
        return ExitCode.ARCHIVE_ERROR

    return ExitCode.SUCCESS

# Run the script
if __name__ == "__main__":
    args = parse_args()
    exit_code = main(args)
    exit(exit_code)