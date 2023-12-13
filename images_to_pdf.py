import argparse
from pathlib import Path

import fitz


def image_to_pdf(image):
    img_doc = fitz.open(image)
    pdf_bytes = img_doc.convert_to_pdf()
    img_pdf = fitz.open("pdf", pdf_bytes)
    return img_pdf


def image_folder_to_pdf(root, out_path=None):
    if not isinstance(root, Path):
        root = Path(root)
    if out_path is None:
        out_path = root.with_suffix('.pdf')
    if not isinstance(out_path, Path):
        out_path = Path(out_path)

    images = list(filter(lambda f: f.is_file(), root.iterdir()))
    if len(images) == 0:
        print('Warning: ', root, ' has no files in it.')
        return

    pdf = fitz.open()

    for image in images:
        img_pdf = image_to_pdf(image)
        pdf.insert_pdf(img_pdf)
    pdf.save(out_path, garbage=4, clean=True, deflate=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help='images/image_folders path')
    parser.add_argument('-o', '--output', type=str, default=None, required=False, help='output file name')
    parser.add_argument('--image_folders', action=argparse.BooleanOptionalAction,
                        help='input is a folder contains image folders?')

    args = parser.parse_args()
    output = args.output
    print(args)

    # TODO: multiprocessing this
    root = Path(args.input)
    if args.image_folders:
        for item in root.iterdir():
            if item.is_file():
                continue
            image_folder_to_pdf(item)
    else:
        image_folder_to_pdf(root, output)
