import pathlib
import re
import sys

import xml.etree.ElementTree as ET


def extract_episode_info(filename):
    """
    Extracts episode information from a given filename string.

    Args:
        filename (str): The filename string to parse.

    Returns:
        str or None: The extracted episode information string if found,
                     otherwise None.
    """
    # Regex to capture the team, then the show name, then the episode info
    # We are specifically looking for the third square bracketed group.
    # The pattern is:
    # \[.*?\]        -> Non-greedy match for the first bracketed team name
    # \s*            -> Optional whitespace
    # (.+?)          -> Non-greedy match for the show name
    # \s*            -> Optional whitespace
    # \[(.*?)\]      -> The episode information, non-greedy
    # .*             -> Any remaining characters
    match = re.search(r'\[.*?]\s*(.+?)\s*\[(.*?)]', filename)

    if match:
        # The episode information is in the second capturing group of this specific regex
        return match.group(2)
    else:
        return None


def modify_xml(xml_path, title_text, out_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    title = root.find('title')
    title.text = title_text
    tree.write(out_path, encoding='utf-8', xml_declaration=True)


import argparse
import os


def parse_arguments():
    """
    Parses command-line arguments for directory processing.

    Returns:
        argparse.Namespace: An object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Process files within a directory.\n"
                    "By default, operations are performed in-place unless an output directory is specified.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Positional Argument: Input Directory Path
    parser.add_argument(
        'input_directory',  # Renamed for clarity
        type=str,
        help="Path to the input directory to be processed."
    )

    # Flag Argument: Inplace Operation
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',  # This makes it a boolean flag: True if present, False otherwise
        help="Search recursively. "
    )

    # Optional Argument: Output Directory Path (replaces 'inplace' flag)
    parser.add_argument(
        '-o', '--output',
        type=str,
        metavar='OUTPUT_DIR',
        default=None,  # Default to None, meaning inplace if not given
        help="Optional path to a directory where processed files will be saved.\n"
             "If not specified, the operation will be performed in-place in the input directory.\n"
             "If the directory does not exist, it will be created."
    )

    # Optional Argument: Ignore List
    parser.add_argument(
        '-e', '--exclude',
        nargs='*',
        metavar='PATTERN',
        default=['tvshow', 'season'],
        help="Space-separated list of patterns (e.g., file names or extensions) "
             "to ignore during processing. "
    )

    args = parser.parse_args()

    # 1. Validate input_directory
    if not os.path.isdir(args.input_directory):
        parser.error(f"Error: Input directory not found or is not a directory: '{args.input_directory}'")

    # 2. Determine if it's an inplace operation
    # It's an inplace operation if --output was NOT provided
    args.inplace = (args.output is None)

    # 3. Create output directory if specified and doesn't exist
    if not args.inplace:
        # Ensure the output directory either exists or can be created
        try:
            os.makedirs(args.output, exist_ok=True)
        except OSError as e:
            parser.error(f"Error creating output directory '{args.output}': {e}")

        # Optional: Prevent output directory from being the same as input if not desired for non-inplace
        if os.path.abspath(args.input_directory) == os.path.abspath(args.output):
            print("Warning: Output directory is the same as input. This will effectively be an inplace operation.",
                  file=sys.stderr)
            # You might want to error out here depending on strictness
            # parser.error("Output directory cannot be the same as input directory for non-inplace operations.")

    return args


def main():
    args = parse_arguments()

    print(f"Directory Path: {args.input_directory}")
    print(f"Inplace Operation: {args.inplace}")
    print(f"Ignore List: {args.exclude}")

    input_directory = pathlib.Path(args.input_directory)
    output_directory = pathlib.Path(args.output if args.output else input_directory)

    nfo_files = list(input_directory.rglob('*.nfo') if args.recursive else input_directory.glob('*.nfo'))
    extracted = [extract_episode_info(file.name) for file in nfo_files if file.name not in args.exclude]

    for e, f in zip(extracted, nfo_files):
        if e is None:
            continue
        output_path = f if args.inplace else output_directory.joinpath(f.name)
        modify_xml(f, e, output_path)
        print(f"Writing to {output_path}")


if __name__ == "__main__":
    main()
