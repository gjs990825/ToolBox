import argparse
import shutil
from pathlib import Path

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=str)

    args = parser.parse_args()
    root = Path(args.root)

    print('moving non-root files.')
    for item in root.glob('*/**/*'):
        if item.is_file():
            shutil.move(item, root)
    print('removing folders.')
    for item in root.iterdir():
        if not item.is_dir():
            continue
        if item.is_dir():
            shutil.rmtree(item)

    print('DONE.')
