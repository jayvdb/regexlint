import unittest

from regexlint.indicator import *

fakemod = \
r'''# line 1
class foo(object):
    flags = re.MULTILINE
    tokens = {
        'root': [
            (r'grr', Token.Root),
        ],
        'other': [
            (r'bar', String),
            (r'baz'
             u'\x00hi', Other),
            (r"""foo
newlines1
newlines2""", Other),
        ],
    }
'''

class IndicatorTests(unittest.TestCase):
    def test_find_offending_line_1(self):
        ret = find_offending_line(fakemod, 'foo', 'root', 0, 0)
        self.assertEquals((6, 15, 16, "            (r'grr', Token.Root),"), ret)
    def test_find_offending_line_more_complex1(self):
        ret = find_offending_line(fakemod, 'foo', 'other', 1, 3)
        self.assertEquals((11, 15, 19, r"             u'\x00hi', Other),"), ret)
        self.assertEquals(r"\x00", ret[3][ret[1]:ret[2]])
    def test_find_offending_line_more_complex2(self):
        ret = find_offending_line(fakemod, 'foo', 'other', 1, 4)
        self.assertEquals((11, 19, 20, r"             u'\x00hi', Other),"), ret)
        self.assertEquals("h", ret[3][ret[1]:ret[2]])
    def test_find_offending_line_newline_triplequote1(self):
        ret = find_offending_line(fakemod, 'foo', 'other', 2, 0)
        self.assertEquals((12, 17, 18, '            (r"""foo'), ret)
    def test_find_offending_line_newline_triplequote2(self):
        ret = find_offending_line(fakemod, 'foo', 'other', 2, 3)
        self.assertEquals((12, 20, 21, '            (r"""foo'), ret)
    def test_find_offending_line_newline_triplequote3(self):
        ret = find_offending_line(fakemod, 'foo', 'other', 2, 4)
        self.assertEquals((13, 0, 1, 'newlines1'), ret)




class SubstrPosTests(unittest.TestCase):
    def test_find_pos1(self):
        r = find_substr_pos('u"abc"', 0)
        self.assertEquals((0, 2, 3), r)
    def test_find_pos2(self):
        r = find_substr_pos('u"abc"', 1)
        self.assertEquals((0, 3, 4), r)
    def test_find_pos3(self):
        r = find_substr_pos('u"abc"', 2)
        self.assertEquals((0, 4, 5), r)
    def test_find_pos_escapes(self):
        r = find_substr_pos(r'u"a\u1234b"', 1)
        self.assertEquals((0, 3, 9), r)
    def test_find_pos_octal(self):
        s = r'"\000b"'
        r = find_substr_pos(s, 0)
        print s[r[0]:r[1]]
        self.assertEquals((0, 1, 5), r)
    def test_find_pos_end(self):
        r = find_substr_pos('"a"', 0)
        self.assertEquals((0, 1, 2), r)
    def test_find_impossible(self):
        self.assertRaises(ValueError, find_substr_pos, '"a"', 1)
    def test_trailing_newline(self):
        r = find_substr_pos(r'"a\n"', 1)
        self.assertEquals((0, 2, 4), r)
    def test_unicode_difference(self):
        r = find_substr_pos(r'u"\u1234foo"', 1)
        self.assertEquals((0, 8, 9), r)
        r = find_substr_pos(r'"\u1234foo"', 1)
        self.assertEquals((0, 2, 3), r)
    def test_named(self):
        r = find_substr_pos(r'u"\N{space}foo"', 0)
        self.assertEquals((0, 2, 11), r)
        r = find_substr_pos(r'u"\N{space}foo"', 1)
        self.assertEquals((0, 11, 12), r)
        r = find_substr_pos(r'"\N{space}foo"', 1)
        self.assertEquals((0, 2, 3), r)
    def test_tripled(self):
        r = find_substr_pos(r'"""a\x00"""', 1)
        self.assertEquals((0, 4, 8), r)