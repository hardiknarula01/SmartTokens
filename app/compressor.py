import re

FILLER_PHRASES = [
    (r'\bin order to\b',              'to'),
    (r'\bso as to\b',                 'to'),
    (r'\bat this point in time\b',    'now'),
    (r'\bat the present time\b',      'now'),
    (r'\bdue to the fact that\b',     'because'),
    (r'\bowing to the fact that\b',   'because'),
    (r'\bin the event that\b',        'if'),
    (r'\bin spite of the fact that\b','although'),
    (r'\bfor the purpose of\b',       'to'),
    (r'\bwith regard to\b',           'about'),
    (r'\bwith respect to\b',          'about'),
    (r'\bin relation to\b',           'about'),
    (r'\bthe fact that\b',            'that'),
    (r'\ba large number of\b',        'many'),
    (r'\ba majority of\b',            'most'),
    (r'\bat the same time\b',         'simultaneously'),
    (r'\bin the near future\b',       'soon'),
    (r'\bon a daily basis\b',         'daily'),
    (r'\bon a regular basis\b',       'regularly'),
    (r'\bplease could you please\b',  'please'),
    (r'\bplease can you please\b',    'please'),
    (r'\bkindly please\b',            'please'),
    (r'\bI would like you to\b',      'Please'),
    (r'\bI was wondering if you could\b', 'Could you'),
    (r'\bI was hoping you could\b',   'Could you'),
    (r'\bwould you be able to\b',     'can you'),
    (r'\bwould you mind\b',           'please'),
    (r'\bbasically\b',                ''),
    (r'\bessentially\b',              ''),
    (r'\bfundamentally\b',            ''),
    (r'\bliterally\b',                ''),
    (r'\bactually\b',                 ''),
    (r'\bsimply\b',                   ''),
    (r'\bjust\b(?= \w)',              ''),
    (r'\bif that makes sense\b',      ''),
    (r'\bif you know what I mean\b',  ''),
    (r'\bdo you understand\b',        ''),
    (r'\bhope this helps\b',          ''),
    (r'\bthank you in advance\b',     ''),
    (r'\bthanks in advance\b',        ''),
    (r'\bplease and thank you\b',     'please'),
]

COMPILED_PATTERNS = [
    (re.compile(pattern, re.IGNORECASE), replacement)
    for pattern, replacement in FILLER_PHRASES
]

def remove_filler_phrases(text: str) -> str:
    for pattern, replacement in COMPILED_PATTERNS:
        text = pattern.sub(replacement, text)
    return text

def deduplicate_sentences(text: str) -> str:
    sentences = text.split('.')
    seen = set()
    unique = []
    for sentence in sentences:
        clean = sentence.strip().lower()
        if not clean:
            continue
        if clean in seen:
            continue
        seen.add(clean)
        unique.append(sentence.strip())
    return '. '.join(unique)

def clean_up_spaces(text: str) -> str:
    text = re.sub(r'  +', ' ', text)
    text = re.sub(r' ([,.!?;:])', r'\1', text)
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(line for line in lines if line)
    return text.strip()

def compress(text: str, deduplicate: bool = True) -> str:
    if not text or not text.strip():
        return text
    text = remove_filler_phrases(text)
    if deduplicate:
        text = deduplicate_sentences(text)
    text = clean_up_spaces(text)
    return text