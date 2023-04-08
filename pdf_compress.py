r"""Compress PDF using PyMuPDF

EXAMPLE
---
    Compress RGB image with jpeg of quality 30, compress greyscale image with otsu method, skip page 1, 2, 3, 24:

    python pdf_tool.py path_to_input.pdf path_to_output.pdf --quality 30 --otsu --pages skip 1-3 24
"""

import argparse
import io
import fitz

import cv2
import numpy as np
from PIL import Image


def get_page_config(parameters: list[str]):
    """return page number starts from 0"""
    pages = []
    for s in parameters[1:]:
        ss = [int(n) - 1 for n in s.split(sep='-')]
        match len(ss):
            case 2:
                pages.extend(range(ss[0], ss[1] + 1))
            case 1:
                pages.append(ss[0])
            case _:
                raise SyntaxError(f'page parameter error:{s}')
    match parameters[0]:
        case 'process':
            return lambda x: x in pages
        case 'skip':
            return lambda x: x not in pages
        case _:
            raise SyntaxError('no {process, skip} keyword')


def parse_flag(s: str):
    if s.isdigit():
        return int(s)
    idx = s.rfind('.')
    if (s[:idx] + s[idx + 1:]).isdigit():
        return float(s)
    return s


# bad effect, just use jpeg with lower quality
def quantize(source: Image.Image, colors):
    return source.quantize(colors)


def threshold_otsu(source):
    image_size = source.size
    if source.mode == 'L':
        source_grey = np.array(source)
    elif source.mode == 'RGB':
        source_grey = cv2.cvtColor(np.array(source), cv2.COLOR_RGB2GRAY)
    else:
        raise TypeError(f'not supported mode: {source.mode}')

    ret, th = cv2.threshold(source_grey, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    image = Image.frombuffer('L', image_size, th, 'raw', 'L', 0, 1)
    return image.convert('1')


def threshold_normal(source: Image.Image, threshold=127):
    return source.convert('L').point(lambda x: x > threshold, mode='1')


# noinspection PyUnresolvedReferences
def compress(in_file, out_file, handle_types, otsu, binary, page_filter, threshold, quality):
    doc = fitz.Document(in_file)
    print(doc.metadata)

    for page_idx, page in enumerate(doc.pages()):
        print(page_idx, page)

        if not page_filter(page_idx):
            print(f'skip page: {page_idx}')
            continue

        for image_info in page.get_images():
            # (xref, smask, width, height, bpc, colorspace, alt.colorspace, name, filter, referencer)
            # image_info: (7, 0, 1222, 1680, 8, 'DeviceRGB', '', 'I0', 'DCTDecode')
            print(image_info)
            xref = image_info[0]

            # image = {'ext': 'jpeg', 'smask': 0, 'width': 1222, 'height': 1680, 'colorspace': 3, 'bpc': 8, 'xres': 96,
            #          'yres': 96, 'cs-name': 'DeviceRGB', 'image': b''}
            image = doc.extract_image(xref)

            image_original = Image.open(io.BytesIO(image['image']))
            if image_original.mode not in handle_types:
                print(f'skip image: xref[{xref}]: {image_original.mode}')
                continue

            image_new_bytes = io.BytesIO()

            if binary or image_original.mode == 'L':
                image_new = threshold_otsu(image_original) if otsu else threshold_normal(image_original, threshold)
                image_new.save(image_new_bytes, 'png', compress_level=0)
            else:
                # image_new = quantize(image_original, colors)
                image_original.save(image_new_bytes, 'jpeg', quality=quality)

            new_xref = page.insert_image(page.rect, stream=image_new_bytes)
            doc.xref_copy(new_xref, xref)
            doc._deleteObject(new_xref)

    # fix permission problem
    out_file.write(doc.tobytes(garbage=4, clean=True, deflate=True))


def run(args):
    in_file = args.input
    out_file = args.output
    # flags = {(k_v := f.split('='))[0]: parse_flag(k_v[1]) for f in args.flags} if args.flags else {}
    page_filter = get_page_config(args.pages) if args.pages else lambda x: True
    handle_type = args.handle_type if args.handle_type else ['RGB', 'L']
    otsu = bool(args.otsu)
    binary = bool(args.binary_image)
    threshold = args.threshold
    quality = args.quality

    compress(in_file, out_file, handle_type, otsu, binary, page_filter, threshold, quality)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=argparse.FileType('rb'), help='input file')
    parser.add_argument('output', type=argparse.FileType('wb'), help='output file')
    parser.add_argument('--pages', type=str, action='extend', nargs='*',
                        help='pages to process/skip, "{process, skip} 1 2-4" means to {process, skip} page [1, 2, 3, 4]')
    parser.add_argument('--handle_type', type=str, action='extend', nargs='*',
                        help='image color types to convert, default:["RGB", "L"]')
    parser.add_argument('-q', '--quality', type=int, default=30, help='jpeg image quality setting')
    parser.add_argument('-t', '--threshold', type=int, default=127, help='binary image threshold, when not using otsu')
    parser.add_argument('--otsu', action=argparse.BooleanOptionalAction, help='use otsu method to handle binary image')
    # parser.add_argument('--flags', type=str, action='extend', nargs='*', help='flags for image convert')
    parser.add_argument('--binary_image', action=argparse.BooleanOptionalAction,
                        help='process all images to "black and white"')

    args = parser.parse_args()
    print(args)
    run(args)
