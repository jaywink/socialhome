import re
import functools
from io import BytesIO

from babel.messages.extract import extract_javascript
from babel.messages.extract import DEFAULT_KEYWORDS

del(DEFAULT_KEYWORDS['_'])
del(DEFAULT_KEYWORDS['N_'])

def extract_extrajs(fileobj, keywords, comment_tags, options):
    """Extract template literal placeholders and filters from Javascript files.

    :param fileobj: the file-like the messages should be extracted from
    :param keywords: a list of keywords (i.e. function names) that should be recognize as translation functions
    :param comment_tags: a list of translator tags to search for and include in the results
    :param options: a dictionary of additional options (optional)
    :return: an iterator over ``(lineno, funcname, message, comments)``
    :rtype: ``iterator``
    """
    encoding = options.get('encoding', 'utf-8')
    c = fileobj.read().decode(encoding=encoding)

    filtpat = re.compile('t\._f\("gettext"\)', re.UNICODE)
    c = filtpat.sub('gettext', c)

    comppat = re.compile(r'(\$\{gettext\((.*?)\)\})', re.UNICODE)
    c = comppat.sub(r'`+gettext(\g<2>)+`', c, re.UNICODE)

    for i in extract_javascript(
            BytesIO(c.encode(encoding=encoding)),
            DEFAULT_KEYWORDS.keys(),
            comment_tags,
            options):
        if i:
            yield (i[0], i[1], i[2], i[3])
    

if __name__ == '__main__':
  import sys
  print(sys.argv[1])
  with open(sys.argv[1], 'rb') as f:
    for i in extract_extrajs(f, ['gettext'], [], {}):
      print(i)
