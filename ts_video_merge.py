import argparse
import os
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryFile


def find_files(folder, ext):
    if not folder.is_dir():
        return iter(())
    return (f for f in folder.iterdir() if f.suffix == ext)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=str, help='path to ts videos folder')
    parser.add_argument('-e', '--extension', type=str, default='.ts', help='ts video extension, with dot')
    parser.add_argument('-n', '--name', type=str, help='new name, default: folder name')
    parser.add_argument('-r', '--remove', action=argparse.BooleanOptionalAction,
                        help='remove original files after merge')

    args = parser.parse_args()

    folder = Path(args.folder)
    ext = args.extension
    name = Path(args.name) if args.name else folder.with_name(folder.name + '.mp4')
    remove = args.remove is True

    ts_files = find_files(folder, ext)

    with TemporaryFile('w+', suffix='.txt', delete=False) as ts_txt:
        for t in ts_files:
            ts_txt.write(f'file \'{t.as_posix()}\'')
            ts_txt.write('\n')
        ts_txt.close()

        with TemporaryFile('wb', suffix='.ts', delete=False) as merged:
            merged.close()
            # start merging
            subprocess.run(f'ffmpeg -y -safe 0 -f concat -i {ts_txt.name} -c copy {merged.name}'.split())
            # convert to mp4
            subprocess.run(f'ffmpeg -y -i {merged.name} -c copy {name.as_posix()}'.split())

            os.unlink(merged.name)

        os.unlink(ts_txt.name)

    if args.remove:
        shutil.rmtree(folder)
