"""
Subtitle matching tool

Usage:
>> python match_subtitle.py -s "D:\Personal\Desktop\1662326570103\s" "Z:\TV\Rick and Morty [tmdbid-60625]\Rick.and.Morty.S05.1080p.AMZN.WEBRip.DDP5.1.x264-NTb[rartv]"
01.ass  ->  Rick.and.Morty.S05E01.Mort.Dinner.Rick.Andre.1080p.AMZN.WEB-DL.DDP5.1.H.264-NTb.ass
02.ass  ->  Rick.and.Morty.S05E02.Mortyplicity.1080p.AMZN.WEB-DL.DDP5.1.H.264-NTb.ass
03.ass  ->  Rick.and.Morty.S05E03.A.Rickconvenient.Mort.1080p.AMZN.WEB-DL.DDP5.1.H.264-NTb.ass
04.ass  ->  Rick.and.Morty.S05E04.Rickdependence.Spray.1080p.AMZN.WEB-DL.DDP5.1.H.264-NTb.ass
05.ass  ->  Rick.and.Morty.S05E05.Amortycan.Grickfitti.1080p.AMZN.WEB-DL.DDP5.1.H.264-NTb.ass
06.ass  ->  Rick.and.Morty.S05E06.Rick.and.Mortys.Thanksploitation.Spectacular.1080p.AMZN.WEB-DL.DDP5.1.H.264-NTb.ass
07.ass  ->  Rick.and.Morty.S05E07.Gotron.Jerrysis.Rickvangelion.1080p.AMZN.WEB-DL.DDP5.1.H.264-NTb.ass
08.ass  ->  Rick.and.Morty.S05E08.Rickternal.Friendshine.of.the.Spotless.Mort.1080p.AMZN.WEB-DL.DDP5.1.H.264-NTb.ass
09.ass  ->  Rick.and.Morty.S05E09.Forgetting.Sarick.Mortshall.1080p.AMZN.WEB-DL.DDP5.1.H.264-NTb.ass
10.ass  ->  Rick.and.Morty.S05E10.Rickmurai.Jack.1080p.AMZN.WEB-DL.DDP5.1.H.264-NTb.ass
Making subtitles...
DONE
"""

import argparse
import re
import shutil
from pathlib import Path

vid_suffixes = ['.mkv', '.mp4']
sub_suffixes = ['.ass', '.srt', '.mks']

video_match_regx = re.compile('.*(?:\[(\d{2})]|E(\d{2})).*')
# episode with 'E': S01E01
subs_match_regx = re.compile('.*E(?P<id>\d{2}).*?(?:\.(?P<note>[^.]+))?\.(?P<suffix>ass|srt)')
# episode without 'E': [01]
subs_match_regx_no_e = re.compile('.*(?P<id>\d{2}).*?(?:\.(?P<note>[^.]+))?\.(?P<suffix>ass|srt)')


def find_video_id(video_name):
    m = video_match_regx.match(video_name)
    if m is None:
        return None
    for g in m.groups():
        if g is not None:
            return g
    raise Exception('Video name matching error')


def find_sub_info(sub_name):
    m = subs_match_regx.match(sub_name)
    if not m:
        m = subs_match_regx_no_e.match(sub_name)
    if not m:
        raise Exception('Subtitle name matching error')
    return m.groupdict()


def make_subtitle_name(subs_info):
    if subs_info['note'] is None:
        pattern = '{video_name}.{suffix}'
    else:
        pattern = '{video_name}.{note}.{suffix}'
    return pattern.format_map(subs_info)


def make_names(subs, videos):
    sub_names = []
    for sub in subs:
        sub_info = find_sub_info(sub.name)
        for video in videos:
            video_id = find_video_id(video.name)
            if sub_info['id'] != video_id:
                continue
            sub_info['video_name'] = video.stem
            sub_name = make_subtitle_name(sub_info)
            sub_names.append(sub_name)
            break
    return sub_names


from itertools import repeat
from tabulate import tabulate


def preview(subs, sub_names):
    subs = [s.name for s in subs]
    print(tabulate(list(zip(subs, repeat('->'), sub_names)), tablefmt='plain'))


def make_subtitles(subs, sub_names):
    print('Making subtitles...')
    for sub, sub_name in zip(subs, sub_names):
        shutil.copy(sub, videos_folder.joinpath(sub_name))
    print('DONE')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('videos_folder', type=str)
    parser.add_argument('-s', '--subtitle-folder', type=str, default=None)
    parser.add_argument('-p', '--preview-only', action=argparse.BooleanOptionalAction)

    args = parser.parse_args()

    videos_folder = Path(args.videos_folder)
    subs_folder = videos_folder if args.subtitle_folder is None else Path(args.subtitle_folder)

    videos = list(f for f in videos_folder.iterdir() if f.suffix in vid_suffixes)
    subs = list(s for s in subs_folder.iterdir() if s.suffix in sub_suffixes)

    sub_names = make_names(subs, videos)

    preview(subs, sub_names)

    if not args.preview_only:
        make_subtitles(subs, sub_names)
