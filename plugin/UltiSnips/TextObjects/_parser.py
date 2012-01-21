#!/usr/bin/env python
# encoding: utf-8

from UltiSnips.Geometry import Position
from ._lexer import tokenize, EscapeCharToken, VisualToken, \
    TransformationToken, TabStopToken, MirrorToken, PythonCodeToken, \
    VimLCodeToken, ShellCodeToken

from ._escaped_char import EscapedChar
from ._mirror import Mirror
from ._python_code import PythonCode
from ._shell_code import ShellCode
from ._tabstop import TabStop
from ._transformation import Transformation
from ._viml_code import VimLCode
from ._visual import Visual

__all__ = ["TOParser"]

class TOParser(object):
    TOKEN2TO = {
        EscapeCharToken: EscapedChar,
        VisualToken: Visual,
        ShellCodeToken: ShellCode,
        PythonCodeToken: PythonCode,
        VimLCodeToken: VimLCode,
    }

    def __init__(self, parent_to, text, indent):
        """
        The parser is responsible for turning tokens into Real TextObjects
        """
        self._indent = indent
        self._parent_to = parent_to
        self._text = text

    def parse(self, add_ts_zero = False):
        seen_ts = {}
        all_tokens = []

        self._do_parse(all_tokens, seen_ts)

        self._resolve_ambiguity(all_tokens, seen_ts)
        self._create_objects_with_links_to_tabs(all_tokens, seen_ts)

        if add_ts_zero and 0 not in seen_ts:
            mark = all_tokens[-1][1].end # Last token is always EndOfText
            m1 = Position(mark.line, mark.col)
            self._parent_to._add_tabstop(TabStop(self._parent_to, 0, mark, m1))

        self._replace_initial_texts()

    #####################
    # Private Functions #
    #####################
    def _resolve_ambiguity(self, all_tokens, seen_ts):
        for parent, token in all_tokens:
            if isinstance(token, MirrorToken):
                if token.no not in seen_ts:
                    ts = TabStop(parent, token)
                    seen_ts[token.no] = ts
                    parent._add_tabstop(ts)
                else:
                    Mirror(parent, seen_ts[token.no], token)

    def _create_objects_with_links_to_tabs(self, all_tokens, seen_ts):
        for parent, token in all_tokens:
            if isinstance(token, TransformationToken):
                if token.no not in seen_ts:
                    raise RuntimeError("Tabstop %i is not known but is used by a Transformation" % token.no)
                Transformation(parent, seen_ts[token.no], token)

    def _replace_initial_texts(self):
        def _place_initial_text(obj):
            obj.overwrite()

            for c in obj._childs: # TODO: private parts!
                _place_initial_text(c)

        _place_initial_text(self._parent_to)

    def _do_parse(self, all_tokens, seen_ts):
        tokens = list(tokenize(self._text, self._indent, self._parent_to.start))

        for token in tokens:
            all_tokens.append((self._parent_to, token))

            if isinstance(token, TabStopToken):
                ts = TabStop(self._parent_to, token)
                seen_ts[token.no] = ts
                self._parent_to._add_tabstop(ts)

                k = TOParser(ts, token.initial_text, self._indent)
                k._do_parse(all_tokens, seen_ts)
            else:
                klass = self.TOKEN2TO.get(token.__class__, None)
                if klass is not None:
                    klass(self._parent_to, token)

