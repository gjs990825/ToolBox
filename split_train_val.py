r"""This script takes a label_path image_path pair, split them randomly.

EXAMPLE:
    python split_train_val.py -i path_to_labels path_to_images
    -image_ext .jpg -label_ext .txt
    -output path_to_output
"""

import argparse
import random
from pathlib import Path


def get_paired(image_path: Path, image_ext, label_path: Path, label_ext):
    image_ext, label_ext = image_ext.lower(), label_ext.lower()
    label_files = list(filter(lambda f: f.suffix.lower() == label_ext, label_path.iterdir()))
    image_files = list(filter(lambda f: f.suffix.lower() == image_ext, image_path.iterdir()))

    pairs = []
    for label in label_files:
        image = image_path.joinpath(label.with_suffix(image_ext).name)
        if image.is_file():
            try:
                image_files.remove(image)
                pairs.append((label, image))
            except ValueError:
                print(f'{label} has no matched image')

    if image_files:
        print(f'{image_files} have not matched image')
    return pairs


def write_config(train: list[Path], test: list[Path], output_path: Path):
    train_path, test_path = output_path.joinpath('train.txt'), output_path.joinpath('val.txt')
    with open(train_path, 'w+') as train_file, open(test_path, 'w+') as test_file:
        for t in train:
            train_file.write(f'{t.relative_to(output_path)}\n')
        for t in test:
            test_file.write(f'{t.relative_to(output_path)}\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', type=str, action='extend', nargs='+', metavar=('label_path', 'image_path'), required=True)
    parser.add_argument('-label_ext', type=str, default='.txt', help='label file extension name')
    parser.add_argument('-image_ext', type=str, help='image file extension name')
    parser.add_argument('-training_proportion', type=float, default='0.8', help='training proportion')
    parser.add_argument('-output', type=str, help='output path')
    args = parser.parse_args()

    label_path = Path(args.i[0])
    image_path = Path(args.i[1]) if len(args.i) == 2 else label_path
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    label_ext = args.label_ext
    image_ext = args.image_ext
    train_proportion = args.training_proportion

    paired = get_paired(image_path, image_ext, label_path, label_ext)

    paired_size = len(paired)
    train_size = round(paired_size * train_proportion)
    test_size = paired_size - train_size
    if train_size < 1 or test_size < 1:
        raise ValueError(f'sample too small')

    # use sample instead choice for non-repeated results
    selected_test = random.sample(paired, k=test_size)

    train = [t[1] for t in (list(set(paired) - set(selected_test)))]
    test = [t[1] for t in selected_test]

    write_config(train, test, output_path)

    print('DONE!')
