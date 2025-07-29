"""
python extract_argument_flags.py flag_prefix arg1 arg2

powershell:
python extract_argument_flags.py --% flag_prefix arg1 arg2
"""

import sys


def extract_flags_with_prefix(args, prefix):
    return [arg.removeprefix(prefix) for arg in args if arg.startswith(prefix)]


def main():
    args = sys.argv[1:]

    assert len(args) > 1

    print(args)

    define_flags = extract_flags_with_prefix(args[1:], args[0])

    if define_flags:
        print("Extracted flags:")
        for flag in define_flags:
            print(f"  {flag}")
    else:
        print("No matched flags found in the provided arguments.")


if __name__ == "__main__":
    main()
