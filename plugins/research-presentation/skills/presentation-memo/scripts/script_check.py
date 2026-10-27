#!/usr/bin/env python3
"""Measure a presentation script, or emit its plain spoken text.

Usage:
  script_check.py SCRIPT.md            # character count and estimated speaking time
  script_check.py --plain SCRIPT.md    # spoken text only (for a blind syntax read)
  script_check.py --rate 330 SCRIPT.md # characters per minute (default 315)

Only the part under the first "## 講稿" heading (30-second / short versions) or
from the first "##" section to the symbol-reading table (walkthrough) is counted.
Removed before counting: furigana in （かな）, 〔動作：…〕 cues, headings,
markdown tables, and the inline math delimiters (the math itself is kept as one
token per formula, since it is read aloud).
"""
import argparse
import re
import sys

READING_TABLE = re.compile(r'^##\s*(數學記號|数学記号|數學符號|念法)', re.M)
FURIGANA = re.compile(r'（[ぁ-んァ-ヶー・]+）')
CUE = re.compile(r'〔動作[^〕]*〕')
MATH = re.compile(r'\$\$.*?\$\$|\$[^$]+\$', re.S)


def spoken_text(md: str) -> str:
    # drop the front matter bullets: start at the first "##" heading
    first = md.find('\n## ')
    body = md[first:] if first >= 0 else md
    m = READING_TABLE.search(body)
    if m:
        body = body[:m.start()]
    body = CUE.sub('', body)
    body = FURIGANA.sub('', body)
    body = MATH.sub('〈式〉', body)
    lines = [ln for ln in body.splitlines()
             if ln.strip() and not ln.lstrip().startswith(('#', '|', '-'))]
    return '\n'.join(ln.strip() for ln in lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('script')
    ap.add_argument('--plain', action='store_true', help='print spoken text only')
    ap.add_argument('--rate', type=int, default=315, help='characters per minute (default 315)')
    a = ap.parse_args()
    try:
        md = open(a.script, encoding='utf-8').read()
    except OSError as e:
        print(f'cannot read {a.script}: {e}', file=sys.stderr)
        return 1
    text = spoken_text(md)
    if a.plain:
        print(text.replace('〈式〉', '（数式）'))
        return 0
    n = len(re.sub(r'\s', '', text))
    secs = n / a.rate * 60
    print(f'{a.script}: {n} chars spoken, about {secs:.0f} s ({secs / 60:.1f} min) at {a.rate} chars/min')
    return 0


if __name__ == '__main__':
    sys.exit(main())
