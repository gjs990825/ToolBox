r"""Convert images format in batch, accepts multiple input directories.

NOTE:
    This script takes all files in input directories as image inputs, make sure there is no other file.
    Pillow is required.

EXAMPLE:
    python image_format_convert.py -i path_to_images_1 path_to_images_2
    -o path_to_output
    --image-ext .jpg
    --flags quality=90
    --remove-original
"""

import argparse
import os
from multiprocessing import Pool
from pathlib import Path

from PIL import Image


def parse_flag(s: str):
    if s.isdigit():
        return int(s)
    idx = s.rfind('.')
    if (s[:idx] + s[idx + 1:]).isdigit():
        return float(s)
    return s


def convert_image(image_path: Path, dir_out: Path, image_ext: str, flags: dict):
    output_path = dir_out.joinpath(image_path.with_suffix(image_ext).name)
    try:
        im = Image.open(image_path)
        rgb_im = im.convert('RGB')
        rgb_im.save(output_path, **flags)
    except Exception as e:
        print(f'FAIL: {image_path.stem}, {e}')
        return False

    print(f'OK: {image_path.stem}')
    return True


def run(args):
    input_dirs = [Path(i) for i in args.i]
    dir_out = Path(args.o) if args.o else None
    remove_original = args.remove_original
    image_ext = args.image_ext
    flags = {(k_v := f.split('='))[0]: parse_flag(k_v[1]) for f in args.flags} if args.flags else {}

    if dir_out:
        dir_out.mkdir(parents=True, exist_ok=True)

    works = []
    for input_dir in input_dirs:
        input_path = Path(input_dir)
        out = dir_out if dir_out else input_path
        images = input_path.iterdir()
        works.extend((image, out, image_ext, flags) for image in images)

    # multiprocessing go🚀
    with Pool() as p:
        success = all(p.starmap(convert_image, works))
        if success:
            print('SUCCESS!')
            if remove_original:
                for image, *_ in works:
                    os.remove(image)
                print('Original images deleted')
        else:
            print('OOPS!')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', type=str, action='extend', nargs='+', required=True,
                        help='label directory and video path, multiple input pairs supported')
    parser.add_argument('-o', type=str, default=None,
                        help='output directory, use the same directory(s) if not specified')
    parser.add_argument('-r', '--remove-original', default=False, action=argparse.BooleanOptionalAction,
                        help='remove original images')
    parser.add_argument('-e', '--image_ext', type=str, default='.jpg', help='image file extension name(with dot)')
    parser.add_argument('-f', '--flags', type=str, action='extend', nargs='*', help='flags for image convert')
    args = parser.parse_args()
    print(args)

    run(args)
