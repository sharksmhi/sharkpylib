import re

FILE_STEM_PATTERNS = [
        re.compile('^{}{}_{}_{}{}{}_{}{}_{}_{}{}$'.format('(?P<prefix>u|d)?',
                                                        '(?P<instrument>sbe\d{2})',
                                                        '(?P<instrument_number>\d{4})',
                                                        '(?P<year>\d{4})',
                                                        '(?P<month>\d{2})',
                                                        '(?P<day>\d{2})',
                                                        '(?P<hour>\d{2})',
                                                        '(?P<minute>\d{2})',
                                                        '(?P<ship>\d{2}_\w{2})',
                                                        '(?P<serno>\d{4})',
                                                        '(?P<tail>.*)?'
                                                        )
                   ),
        re.compile('^{}{}_{}_{}{}{}_{}{}_{}_{}_{}{}$'.format('(?P<prefix>u|d)?',
                                                           '(?P<instrument>sbe\d{2})',
                                                           '(?P<instrument_number>\d{4})',
                                                           '(?P<year>\d{4})',
                                                           '(?P<month>\d{2})',
                                                           '(?P<day>\d{2})',
                                                           '(?P<hour>\d{2})',
                                                           '(?P<minute>\d{2})',
                                                           '(?P<ship>\d{2}\w{2})',
                                                           '(?P<cruise>\d{2})',
                                                           '(?P<serno>\d{4})',
                                                           '(?P<tail>.*)?'
                                                           )
                   ),
        re.compile('^{}{}{}{}$'.format('(?P<ship>\w{2})',
                                       '(?P<year>\d{2})',
                                       '(?P<midfix>u|d)',
                                       '(?P<serno>\d{4})',
                                       )
                   ),
    ]

CRUISE_PATTERNS = [
    # 77SE-2022-02
    re.compile('^{}-{}-{}$'.format('(?P<ship>\d{2}\w{2})',
                                   '(?P<year>\d{4})',
                                   '(?P<cruise>\d{2})')
               ),
    re.compile('^SMHI-{}-{}$'.format('(?P<cruise>\d{2})',
                                     '(?P<year>\d{4})')
               )
]


def get_file_stem_match(string):
    for PATTERN in FILE_STEM_PATTERNS:
        name_match = PATTERN.search(string.lower())
        if name_match:
            return name_match


def get_cruise_match(string):
    for PATTERN in CRUISE_PATTERNS:
        name_match = PATTERN.search(string)
        if name_match:
            return name_match


def get_cruise_match_dict(string):
    name_match = get_cruise_match(string)
    if not name_match:
        return {}
    return name_match.groupdict()
