# Copyright 2011-2014 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import print_function

import sre_parse

from unittest import TestCase
from pygments.token import Other

from regexlint.parser import Regex, Node, width, fmttree, \
                             WHITESPACE, DIGITS, WORD
from regexlint.checkers import find_all, find_all_by_type
from regexlint.compat import tobytes

SAMPLE_PATTERNS = [
    r'a|b|',
    r'((a(?:b))|)',
    r'[a-bb]',
    r'x*',
    r'x{1,}',
    r'x{,5}?',
    r'(?P<first_char>.)(?P=first_char)*',
]

CHARCLASS_PATTERNS = [
    r'[aa]',
    r'[ab]',
    r'[a-b]',
    r'[\a-\b]',
    r'[a\-b]',
    r'[a-]',
    r'[][]',
    r'[]]',
    r'[^]]',
    r'[\[\]]',
    r'[\w]',
    r'[\w\s\d]',
    r'[^xx]',
    r'[^x\s]',
    r'[^x\D]',
    r'[^x\S]',
    r'[^x\W]',
]

class BasicTests(TestCase):
    def do_it(self, s):
        # for debugging
        for x in Regex().get_tokens_unprocessed(s):
            print(x)
        r = Regex.get_parse_tree(s)
        return r

    def test_badness(self):
        self.do_it('\\\\([\\\\abfnrtv"\\\'?]|x[a-fA-F0-9]{2,4}|[0-7]{1,3})')
    def test_bracket(self):
        self.do_it('[^(\\[\\])]*')

    def test_singleparens(self):
        self.do_it(r'\(')
        self.do_it(r'\)')

    def test_brackets(self):
        r = self.do_it(r'\[')
        print(r)
        r = self.do_it(r'\]')

    def test_find_by_type(self):
        golden = [Node(t=Other.Directive, start=0, parsed_start=0,
                       data='(?mi)')]
        r = Regex.get_parse_tree(r'(?mi)')
        self.assertEquals(golden, list(find_all_by_type(r, Other.Directive)))

    def test_find_all_by_type(self):
        r = Regex.get_parse_tree(r'(?m)(?i)')
        directives = list(find_all_by_type(r, Other.Directive))
        self.assertEquals(2, len(directives))
        self.assertEquals('(?m)', directives[0].data)
        self.assertEquals('(?i)', directives[1].data)

    def test_char_range(self):
        r = Regex.get_parse_tree(r'[a-z]')
        self.assertEquals(1, len(next(find_all_by_type(r, Other.CharClass)).chars))

    def test_end_set_correctly(self):
        r = Regex.get_parse_tree(r'\b(foo|bar)\b')
        self.assertEquals(0, r.start)
        capture = r.children[1]
        foo = capture.children[0].children[0]
        self.assertEquals(3, foo.start)
        self.assertEquals(6, foo.end)
        bar = capture.children[0].children[1]
        self.assertEquals(7, bar.start)
        self.assertEquals(10, bar.end)
        self.assertEquals(13, r.end)

    def test_comment(self):
        r = Regex.get_parse_tree(r'(?#foo)')
        l = list(find_all_by_type(r, Other.Comment))
        self.assertEquals(1, len(l))
        self.assertEquals('(?#foo)', l[0].data)

    def test_width(self):
        r = Regex.get_parse_tree(r'\s(?#foo)\b')
        l = list(find_all(r))[1:] # skip root
        self.assertEquals([True, False, False],
                          [width(i.type) for i in l])

    def test_repetition_plus(self):
        r = Regex.get_parse_tree(r'x+')
        l = list(find_all(r))[1:] # skip root
        self.assertEquals(2, len(l))
        # l[0] is Repetition, l[1] is Literal(x)
        self.assertEquals(1, l[0].min)
        self.assertEquals(None, l[0].max)
        self.assertEquals(True, l[0].greedy)

    def test_repetition_curly1(self):
        r = Regex.get_parse_tree(r'x{5,5}?')
        print('\n'.join(fmttree(r)))
        l = list(find_all(r))[1:] # skip root
        self.assertEquals(2, len(l))
        # l[0] is Repetition, l[1] is Literal(x)
        self.assertEquals(5, l[0].min)
        self.assertEquals(5, l[0].max)
        self.assertEquals(False, l[0].greedy)

    def test_repetition_curly2(self):
        r = Regex.get_parse_tree(r'x{2,5}')
        l = list(find_all(r))[1:] # skip root
        self.assertEquals(2, len(l))
        # l[0] is Repetition, l[1] is Literal(x)
        self.assertEquals(2, l[0].min)
        self.assertEquals(5, l[0].max)
        self.assertEquals(True, l[0].greedy)

class VerboseModeTests(TestCase):
    def test_basic_verbose_parsing(self):
        r = Regex.get_parse_tree(r'''(?x)  a   b # comment
                        c
                        d''')
        l = list(find_all(r))[1:] # skip root
        print('\n'.join(fmttree(r)))
        self.assertEquals(5, len(l))
        self.assertEquals((4, 6), (l[1].parsed_start, l[1].start))
        self.assertEquals('d', l[-1].data)
        self.assertEquals((7, 72), (l[-1].parsed_start, l[-1].start))

    def test_escaped_space_parsing(self):
        r = Regex.get_parse_tree(r'\ a')
        l = list(find_all(r))[1:] # skip root
        print('\n'.join(fmttree(r)))
        self.assertEquals(2, len(l))
        self.assertEquals(r'\ ', l[0].data)
        self.assertEquals(Other.Suspicious, l[0].type)

    def test_charclass_parsing(self):
        r = Regex.get_parse_tree(r'[ a]')
        l = list(find_all(r))[1:] # skip root
        print('\n'.join(fmttree(r)))
        self.assertEquals(3, len(l))
        self.assertEquals(r' ', l[1].data)
        self.assertEquals(r'a', l[2].data)

    def test_complex_charclass(Self):
        r = Regex.get_parse_tree(r'[]\[:_@\".{}()|;,]')
        l = list(find_all(r))[1:] # skip root
        print('\n'.join(fmttree(r)))
        #self.assertEquals(3, len(l))



def reconstruct_runner(pat):
    r = Regex.get_parse_tree(pat)
    rec = r.reconstruct()
    assert pat == rec

def test_reconstruct():
    for p in SAMPLE_PATTERNS:
        yield reconstruct_runner, p

SRE_CATS = {'category_space': list(map(ord, WHITESPACE)),
            'category_digit': list(map(ord, DIGITS)),
            'category_word': list(map(ord, WORD)),
            'category_not_space': sorted(set(range(256)) -
                                         set(map(ord, WHITESPACE))),
            'category_not_digit': sorted(set(range(256)) -
                                         set(map(ord, DIGITS))),
            'category_not_word': sorted(set(range(256)) -
                                        set(map(ord, WORD))),
           }

def expand_sre_in(x):
    for (typ, value) in x:
        if typ in ('literal', 'not_literal'):
            yield value
        elif typ == 'range':
            for i in range(value[0], value[1]+1):
                yield i
        elif typ == 'category':
            for i in SRE_CATS[value]:
                yield i
        elif typ == 'negate':
            pass
        else:
            raise NotImplementedError("Unknown type %s" % typ)

def charclass_runner(pat):
    r = Regex().get_parse_tree(pat)
    regexlint_version = r.children[0].matching_character_codes
    sre_parsed = sre_parse.parse(tobytes(pat))
    print(sre_parsed)
    if isinstance(sre_parsed[0][1], int):
        sre_chars = sre_parsed
    else:
        sre_chars = sre_parsed[0][1]
    print('inner', sre_chars)
    golden = list(expand_sre_in(sre_chars))
    order_matters = True
    try:
        if (sre_parsed[0][0] == 'not_literal' or
            sre_parsed[0][1][0][0] == 'negate'):
            golden = [i for i in range(256) if i not in golden]
            order_matters = False
    except TypeError:
        pass

    print('sre_parse', golden)
    print('regexlint', regexlint_version)
    if order_matters:
        assert golden == regexlint_version
    else:
        print('extra:', sorted(set(regexlint_version) - set(golden)))
        print('missing:', sorted(set(golden) - set(regexlint_version)))

        assert sorted(golden) == sorted(regexlint_version)

def test_charclass():
    for i in CHARCLASS_PATTERNS:
        yield charclass_runner, i
