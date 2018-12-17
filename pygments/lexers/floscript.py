# -*- coding: utf-8 -*-
"""
    pygments.lexers.floscript
    ~~~~~~~~~~~~~~~~~~~~~~

    Lexer for FloScript

    :copyright: Copyright 2006-2017 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from pygments.lexer import Lexer, RegexLexer, include, bygroups, using, \
    default, words, combined, do_insertions
from pygments.util import get_bool_opt, shebang_matches
from pygments.token import Text, Comment, Operator, Keyword, Name, String, \
    Number, Punctuation, Generic, Other, Error
from pygments import unistring as uni

__all__ = ['FloScriptLexer',]

class FloScriptLexer(RegexLexer):
    """
    For `FloScript <https://github.com/ioflo/ioflo>`_ configuration language source code.

    .. versionadded:: 2.4
    """

    name = 'FloScript'
    aliases = ['floscript', 'flo']
    filenames = ['*.flo']

    def innerstring_rules(ttype):
        return [
            # the old style '%s' % (...) string formatting
            (r'%(\(\w+\))?[-#0 +]*([0-9]+|[*])?(\.([0-9]+|[*]))?'
             '[hlL]?[E-GXc-giorsux%]', String.Interpol),
            # backslashes, quotes and formatting signs must be parsed one at a time
            (r'[^\\\'"%\n]+', ttype),
            (r'[\'"\\]', ttype),
            # unhandled string formatting sign
            (r'%', ttype),
            # newlines are an error (use "nl" state)
        ]


    tokens = {
        'root': [
            (r'\n', Text),
            (r'[^\S\n]+', Text),

            (r'[]{}:(),;[]', Punctuation),
            (r'\\\n', Text),
            (r'\\', Text),
            (r'(to|by|with|from|per|for|cum|qua|via|as|at|in|of|on|re|is|if|be|into|and|not)\b', Operator.Word),
            (r'!=|==|<<|>>|[-~+/*%=<>&^|.]', Operator),
            (r'(load|init|server|logger|log|loggee|first|over|under|next|done|timeout|repeat|native|benter|enter|recur|exit|precur|renter|rexit|print|put|inc|copy|set|aux|rear|raze|go|let|do|bid|ready|start|stop|run|abort|use|flo|give|take)\b', Name.Builtin),
			(r'(frame|framer|house)\b', Keyword),
            ('"', String, 'string'),

            include('name'),
            include('numbers'),
        	(r'#.+$', Comment.Singleline),
        ],
        'string': [
            ('[^"]+', String),
            ('"', String, '#pop'),
        ],
        'numbers': [
            (r'(\d+\.\d*|\d*\.\d+)([eE][+-]?[0-9]+)?j?', Number.Float),
            (r'\d+[eE][+-]?[0-9]+j?', Number.Float),
            (r'0[0-7]+j?', Number.Oct),
            (r'0[bB][01]+', Number.Bin),
            (r'0[xX][a-fA-F0-9]+', Number.Hex),
            (r'\d+L', Number.Integer.Long),
            (r'\d+j?', Number.Integer)
        ],

        'name': [
            (r'@[\w.]+', Name.Decorator),
            (r'[a-zA-Z_]\w*', Name),
        ],



    }
