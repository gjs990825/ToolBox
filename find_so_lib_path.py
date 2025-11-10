import argparse
import pathlib
import subprocess


def find_so_libs(root_path):
    """
    Finds all shared library (.so) files within a given root directory
    and prints their unique parent directories, separated by colons.

    Args:
        root_path (str): The root directory to search for .so files.
    """
    command = ['find', root_path, '-type', 'f', '-name', '*.so']

    print(f"Executing command: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True, check=True)

    so_lib_files = result.stdout.splitlines()
    so_lib_folders = [pathlib.Path(file).parent for file in so_lib_files]

    unique_folders = sorted(list(set(so_lib_folders)))  # Sort for consistent output

    if not unique_folders:
        print(f"No .so files found in '{root_path}'")
        return

    # Print folders separated by colons
    for i, folder in enumerate(unique_folders):
        print(folder.as_posix(), end=":" if i < len(unique_folders) - 1 else "")
    print()  # Newline at the end


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Finds unique directories containing .so files under a given ROOT directory."
    )
    parser.add_argument(
        'root',
        nargs='?',  # Makes the argument optional
        default='.',  # Defaults to current working directory
        help="The root directory to search for .so files (defaults to current directory)."
    )

    args = parser.parse_args()

    find_so_libs(args.root)
