import argparse
import shutil
import time
import requests
from pathlib import Path
from multiprocessing import Pool
from requests.exceptions import SSLError, ProxyError
from html.parser import HTMLParser
from PIL import Image

MAX_RETRY = 8
PARALLEL_NUM = 8

payload = {}
headers = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "max-age=0",
    "sec-ch-ua": "\"Not/A)Brand\";v=\"99\", \"Google Chrome\";v=\"115\", \"Chromium\";v=\"115\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1"
}

proxies = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890',
}


def get_telegraph_html(url):
    try:
        response = requests.request("GET", url, headers=headers, data=payload, proxies=proxies)
        return response.content
    except SSLError:
        print('telegraph request error!')
        return ''


class TelegraphParser(HTMLParser):
    def __init__(self, *, convert_charrefs: bool = ...) -> None:
        super().__init__(convert_charrefs=convert_charrefs)
        self.title_flag = False
        self.title = None
        self.images = []

    def handle_starttag(self, tag, attrs):
        print("Start tag:", tag)

        og_title_flag = False
        for attr in attrs:
            if tag == 'img':
                self.images.append(attr[1])
            elif attr[1] == 'og:title':
                og_title_flag = True
            elif og_title_flag:
                self.title = attr[1]
            print("     attr:", attr)


def download_img(name, i, path, retry=0):
    print(f'Start:{i} {name}')
    start = time.time()
    url = 'https://telegra.ph' + name
    try:
        response = requests.request("GET", url, headers=headers, data=payload, proxies=proxies)
        with open(path.joinpath(f'{i: 05d}.jpg'), 'wb') as f:
            f.write(response.content)
    except SSLError:
        print(f'Fail: {i}')
        return False
    except ProxyError:
        print(f'Proxy Error:{i}, {name}')
        if retry > MAX_RETRY:
            print('Max retry exceeded!!')
            return False
        return download_img(name, i, path, retry + 1)
    end = time.time()
    print(f'Success: {i}, {end - start:.1f}s used')
    return True


def make_pdf_from_images(images: list[Image], path):
    images[0].save(
        path, "PDF", resolution=100.0, save_all=True, append_images=images[1:]
    )


def make_pdf_from_image_folder(folder, save_path=None):
    if not isinstance(folder, Path):
        folder = Path(folder)
    if save_path is None:
        save_path = folder.with_name(folder.name + '.pdf')
    images = [Image.open(f) for f in folder.iterdir()]
    make_pdf_from_images(images, save_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=str, help='path to save this telegraph')
    parser.add_argument('url', type=str, help='telegraph url')
    parser.add_argument('-c', '--convert-to-pdf', action=argparse.BooleanOptionalAction,
                        help='convert images to pdf file')
    parser.add_argument('-r', '--remove', action=argparse.BooleanOptionalAction,
                        help='remove original files after conversion')

    args = parser.parse_args()
    url = args.url
    folder = args.folder

    telegraph_html = get_telegraph_html(url)
    tg_parser = TelegraphParser()
    tg_parser.feed(telegraph_html.decode('utf-8'))
    print(f'Title:{tg_parser.title}, images:{len(tg_parser.images)}')

    telegraph_dir = Path(folder).joinpath(tg_parser.title)
    telegraph_dir.mkdir(exist_ok=True)

    p = Pool(PARALLEL_NUM)
    results = p.starmap(download_img, [(image, i, telegraph_dir) for i, image in enumerate(tg_parser.images, 1)])
    if all(results):
        print('Done, Success!')
    else:
        print('At least one process failed!')

    if args.convert_to_pdf:
        make_pdf_from_image_folder(telegraph_dir)
        if args.remove:
            shutil.rmtree(telegraph_dir)

    print(args)
