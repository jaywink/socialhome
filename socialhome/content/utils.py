import re

import bleach


def safe_text_for_markdown_code(text):
    """Clean the text using bleach but keep content within Markdown code sections ie ` or ``` combos."""
    # Regexp match all ` and ``` pairs
    codes = re.findall(r"`(?!`).*`(?!`)", text, flags=re.DOTALL) + re.findall(r"```.*```", text, flags=re.DOTALL)
    # Store to safety, replacing with markers
    safety = []
    for counter, code in enumerate(codes, 1):
        safety.append(code)
        text = text.replace(code, "%%safe_text_for_markdown_code codes in safety %s%%" % counter, 1)
    # Nuke all html, scripts, etc
    text = bleach.clean(text)
    # Return ` and ``` pairs from safety
    for counter, code in enumerate(safety, 1):
        text = text.replace("%%safe_text_for_markdown_code codes in safety %s%%" % counter, code, 1)
    return text


def safe_text(text):
    """Clean text, stripping all tags, attributes and styles."""
    return bleach.clean(text, tags=[], attributes=[], styles=[], strip=True)
