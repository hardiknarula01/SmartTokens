import re
import ftfy

def preprocess(text: str) -> str:
    # Fix broken unicode characters
    text = ftfy.fix_text(text)

    # Remove HTML tags like <b>, <p>, <div>
    text = re.sub(r'<[^>]+>', ' ', text)

    # Collapse 3+ newlines into 2
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Collapse multiple spaces/tabs into one space
    text = re.sub(r'[ \t]{2,}', ' ', text)

    # Remove lines that are just dashes, equals, or asterisks
    text = re.sub(r'^[=\-\*]{3,}$', '', text, flags=re.MULTILINE)

    # Strip whitespace from each line
    lines = [line.strip() for line in text.split('\n')]

    # Remove completely empty lines that are back-to-back
    text = '\n'.join(line for line in lines if line)

    return text.strip()