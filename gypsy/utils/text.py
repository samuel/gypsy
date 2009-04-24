#!/usr/bin/env python

"""Optimized version of django.utils.text"""

def wrap_lines(text, width):
    """
    A word-wrap function that preserves existing line breaks and most spaces in
    the text. Expects that existing line breaks are posix newlines. Returns a
    generator that yields each line one at a time.
    """
    text_len = len(text)
    pos = 0
    eol = text.find('\n')
    if eol < 0:
        eol = text_len
    while pos < text_len:
        wrap_pos = pos + width
        if wrap_pos >= eol:
            if pos <= eol:
                yield text[pos:eol]
            pos = eol + 1
            eol = text.find('\n', pos)
            if eol < 0:
                eol = text_len
        else:
            wrap_pos = text.rfind(' ', pos, wrap_pos + 1)
            if wrap_pos < 0:
                # Handle the case where there's no space to wrap on
                wrap_pos = text.find(' ', pos + width)
                if wrap_pos < 0 or wrap_pos > eol:
                    wrap_pos = eol
            yield text[pos:wrap_pos]
            pos = wrap_pos + 1

def wrap(text, width):
    r"""
    A word-wrap function that preserves existing line breaks and most spaces in
    the text. Expects that existing line breaks are posix newlines.

    >>> wrap('this is a long paragraph of text that really needs to be wrapped I\'m afraid', 14)
    "this is a long\nparagraph of\ntext that\nreally needs\nto be wrapped\nI'm afraid"
    >>> wrap('this is a short paragraph of text.\n  But this line should be indented',14)
    'this is a\nshort\nparagraph of\ntext.\n  But this\nline should be\nindented'
    >>> wrap('this is a short paragraph of text.\n  But this line should be indented',15)
    'this is a short\nparagraph of\ntext.\n  But this line\nshould be\nindented'
    >>> wrap('loooong\nwoooooords', 4)
    'loooong\nwoooooords'
    """
    return '\n'.join(wrap_lines(text, width))

if __name__ == "__main__":
    import doctest
    doctest.testmod()
