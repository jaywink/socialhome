import re

import bleach
from bs4 import BeautifulSoup


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


def make_nsfw_safe(text):
    """Make NSFW safer by adding click-to-show class to images."""
    soup = BeautifulSoup(text, "lxml")
    images = soup.find_all("img")

    for image in images:
        if image.get("class"):
            image["class"] = "%s nsfw" % " ".join(image.get("class"))
        else:
            image["class"] = "nsfw"
        image.replace_with(image)

    result = str(soup)
    # We don't want html/body, which BeautifulSoup kindly wraps our new HTML in
    if result.startswith("<html><body>") and result.endswith("</body></html>"):
        result = result[len("<html><body>"):-len("</body></html>")]
    return result
