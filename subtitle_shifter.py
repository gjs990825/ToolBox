"""
Subtitle Shifter

Usages:

from subtitle_shifter import AssSubtitle

ass_sub = AssSubtitle(path=sub_file)
(ass_sub << 2).save(keep_name=False)

for path in root.rglob('*.ass'):
    print(path)
    AssSubtitle(path).scaled('00:00:00.40', '00:00:00', '00:22:02.20', '00:22:00').save(keep_name=False)

"""

from datetime import timedelta


def string_to_seconds(time_string: str):
    # Split the string into hours, minutes, and seconds
    hours, minutes, seconds = time_string.split(':')
    # Convert each part to the appropriate type
    hours = int(hours)
    minutes = int(minutes)
    seconds = float(seconds)  # Seconds can include fractions
    # Create and return a timedelta object
    return timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()


def seconds_to_string(total_seconds: float):
    # Calculate hours, minutes, and seconds
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds % 60
    # Format as a string with two decimal places for seconds
    # return "{}:{:02}:{:05.2f}".format(hours, minutes, seconds)
    return f"{hours}:{minutes:02}:{seconds:05.2f}"


def get_linear_scaler(p1, p1_new, p2, p2_new):
    """
    Calculates the new position of a point after a linear scaling operation.
    """
    # Calculate the scaling factor between the original and new scales
    scale = (p2_new - p1_new) / (p2 - p1)

    def scaler(p):
        # Calculate the new position of the original point
        return p1_new + scale * (p - p1)

    return scaler


from copy import deepcopy
from typing import Any, Callable, Optional
from attr import dataclass


@dataclass
class SubtitleElement:
    start: float
    end: float
    parser: Optional[Callable[[float, float], Any]]

    @property
    def content(self):
        if self.parser:
            return self.parser(self.start, self.end)
        return None

    def __str__(self):
        return super().__str__() if not self.parser else self.content


class Subtitle(list[SubtitleElement]):
    def __init__(self, name=None, elements=None):
        super().__init__()
        if elements:
            self.extend(elements)
        self.name = name

    def __ilshift__(self, offset: timedelta):
        for e in self:
            e.start -= offset
            e.end -= offset
        return self

    def __irshift__(self, offset: timedelta):
        return self.__ilshift__(-offset)

    def __lshift__(self, offset: timedelta):
        cp = deepcopy(self)
        cp <<= offset
        return cp

    def __rshift__(self, offset: timedelta):
        return self << -offset

    def scaled(self, t1, t1_new, t2, t2_new):
        type_set = set(map(type, [t1, t1_new, t2, t2_new]))
        assert len(type_set) == 1

        if str in type_set:
            t1, t1_new, t2, t2_new = map(
                lambda t: string_to_seconds(t),
                (t1, t1_new, t2, t2_new)
            )
        elif timedelta in type_set:
            t1, t1_new, t2, t2_new = map(
                lambda t: timedelta.total_seconds(t),
                (t1, t1_new, t2, t2_new)
            )

        assert isinstance(t1, float)

        cp = deepcopy(self)
        scaler = get_linear_scaler(t1, t1_new, t2, t2_new)
        for e in cp:
            e.start = scaler(e.start)
            e.end = scaler(e.end)
        return cp

    def __repr__(self):
        return '<Subtitle \"{}\": {}>'.format(self.name, super().__repr__())

    def __str__(self):
        return '\"{}\":\n'.format(self.name) + ''.join(map(str, self))


from itertools import chain
from pathlib import Path


class AssSubtitle(Subtitle):
    def __init__(self, path, encoding='utf-8', name=None):
        path = Path(path)
        assert path.is_file()

        if not name:
            name = path.name
        self.path = path

        with open(path, encoding=encoding) as f:
            self.lines = f.readlines()

        self.contents = []
        elements = []
        for line in self.lines:
            if line.startswith('Dialogue:'):
                parser, start, end = self.get_ass_dialogue_parser(line)
                ele = SubtitleElement(string_to_seconds(start), string_to_seconds(end), parser)
                elements.append(ele)
                self.contents.append(ele)
            else:
                self.contents.append(line)

        self.encoding = encoding
        super().__init__(name=name, elements=elements)

    @staticmethod
    def get_ass_dialogue_parser(line):
        segments = line.split(sep=',')

        def parser(start, end):
            return ','.join(chain((segments[0], seconds_to_string(start), seconds_to_string(end)), segments[3:]))

        return parser, segments[1], segments[2]

    def parse(self):
        return ''.join(((c.content if isinstance(c, SubtitleElement) else c) for c in self.contents))

    def save(self, name=None, keep_name=False):
        if keep_name:
            name = self.path.stem
        if name is None:
            name = self.path.stem + '_shifted'
        with open(self.path.with_stem(name), 'w', encoding=self.encoding) as f:
            f.write(self.parse())
