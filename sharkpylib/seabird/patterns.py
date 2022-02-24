import re

FILE_STEM_PATTERNS = [
        # Current Expedition
        re.compile('^{}{}_{}_{}{}{}_{}{}_{}_{}{}.{}$'.format('(?P<prefix>u|d)?',
                                                        '(?P<instrument>sbe\d{2})',
                                                        '(?P<instrument_number>\d{4})',
                                                        '(?P<year>\d{4})',
                                                        '(?P<month>\d{2})',
                                                        '(?P<day>\d{2})',
                                                        '(?P<hour>\d{2})',
                                                        '(?P<minute>\d{2})',
                                                        '(?P<ship>\d{2}_\w{2})',
                                                        '(?P<serno>\d{4})',
                                                        '(?P<tail>[a-z1-9\-_]*)?',
                                                        '(?P<suffix>\w*)?'
                                                        )
                   ),
        # New standard format
        re.compile('^{}{}_{}_{}{}{}_{}{}_{}_{}_{}{}.{}$'.format('(?P<prefix>u|d)?',
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
                                                           '(?P<tail>[a-z1-9\-_]*)?',
                                                           '(?P<suffix>\w*)?'
                                                           )
                   ),
        # Early utsjön
        re.compile('^{}{}{}{}.{}$'.format('(?P<ship>\w{2})',
                                       '(?P<year>\d{2})',
                                       '(?P<midfix>u|d)',
                                       '(?P<serno>\d{4})',
                                       '(?P<suffix>\w*)?'
                                       )
                   ),
        # DV Profile: ctd_profile_20151007_7798_0001.txt
        re.compile('^ctd_profile_{}{}{}_{}_{}.{}$'.format('(?P<year>\d{4})',
                                                       '(?P<month>\d{2})',
                                                       '(?P<day>\d{2})',
                                                       '(?P<ship>.{4})',
                                                       '(?P<serno>\d{4})',
                                                       '(?P<suffix>\w*)?'
                                                       )
                   ),
        # MVP: mvp_2021-10-17_071640_a13-a17.cnv
        re.compile('^{}{}_{}-{}-{}_{}{}{}_{}.{}$'.format('(?P<prefix>u|d)?',
                                                    '(?P<instrument>mvp)',
                                                     '(?P<year>\d{4})',
                                                     '(?P<month>\d{2})',
                                                     '(?P<day>\d{2})',
                                                     '(?P<hour>\d{2})',
                                                     '(?P<minute>\d{2})',
                                                     '(?P<second>\d{2})',
                                                     '(?P<transect>[a-z1-9\-_]*)',
                                                     '(?P<suffix>cnv)?'
                                                    )
                    ),
        # MVP: MVP_2021-10-17_071640_xedited
        re.compile('^{}_{}-{}-{}_{}{}{}{}.{}$'.format('(?P<instrument>mvp)',
                                                    '(?P<year>\d{4})',
                                                    '(?P<month>\d{2})',
                                                    '(?P<day>\d{2})',
                                                    '(?P<hour>\d{2})',
                                                    '(?P<minute>\d{2})',
                                                    '(?P<second>\d{2})',
                                                    '(?P<tail>[a-z1-9\-_]*)?',
                                                    '(?P<suffix>\w*)?'
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
