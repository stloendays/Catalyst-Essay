"""LaTeX to native Word equations (OMML) for the manuscript and SI builders.

LaTeX is converted to MathML with latex2mathml and the MathML tree is mapped onto the OMML elements Word uses
(m:f, m:sSub, m:sSup, m:sSubSup, m:rad, m:r). Inline \\( ... \\) fragments become m:oMath inside the paragraph,
display $$ ... $$ blocks a centred m:oMathPara.

    add_math(paragraph, latex, size_pt)          inline equation at the end of a python-docx paragraph
    add_display_math(paragraph, latex, size_pt)  the paragraph becomes a centred display equation
"""
import html
import re

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from latex2mathml.converter import convert_to_element

MATH_FONT = "Cambria Math"
INLINE = re.compile(r"\\\((.+?)\\\)", re.S)
DISPLAY = re.compile(r"^\$\$(.+?)\$\$$", re.S)
FUNCTIONS = {"ln", "log", "exp", "sin", "cos", "tan", "max", "min", "lim"}


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _el(tag, *children):
    e = OxmlElement(tag)
    for c in children:
        e.append(c)
    return e


def _run(text, size, upright=False):
    r = OxmlElement("m:r")
    if upright:
        rpr = OxmlElement("m:rPr")
        sty = OxmlElement("m:sty")
        sty.set(qn("m:val"), "p")
        rpr.append(sty)
        r.append(rpr)
    w = OxmlElement("w:rPr")
    fonts = OxmlElement("w:rFonts")
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(a), MATH_FONT)
    w.append(fonts)
    for t in ("w:sz", "w:szCs"):
        sz = OxmlElement(t)
        sz.set(qn("w:val"), str(int(round(2 * size))))
        w.append(sz)
    r.append(w)
    t = OxmlElement("m:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text.replace("~", "∼")
    r.append(t)
    return r


def _arg(tag, node, size):
    """An OMML argument element (m:e, m:num, m:sub, ...) holding the converted MathML node."""
    out = OxmlElement(tag)
    for c in _convert(node, size):
        out.append(c)
    return out


def _text(node):
    return html.unescape(node.text or "")       # latex2mathml writes characters as numeric references


def _convert(node, size):
    """MathML node -> list of OMML elements."""
    tag = _local(node.tag)
    kids = list(node)
    if tag in ("math", "mrow", "mstyle", "mpadded", "semantics"):
        return [c for k in kids for c in _convert(k, size)]
    if tag == "mi":
        text = _text(node)
        # upright: \mathrm{...} (a single \mathrm letter arrives as a character reference), function names and
        # capital Greek; other letters are math italic
        upright = (node.get("mathvariant") == "normal" or len(text) > 1 or text in FUNCTIONS
                   or ((node.text or "").startswith("&#x") and text.isascii()) or "Α" <= text <= "Ω")
        return [_run(text, size, upright)]
    if tag in ("mn", "mo"):
        text = _text(node).replace("-", "−").replace("~", "∼")
        return [_run(text, size, True)]
    if tag == "mtext":
        return [_run(_text(node), size, True)]
    if tag == "mspace":
        width = node.get("width", "")
        return [_run(" " if width.startswith("0.16") else " ", size, True)]
    if tag == "mfrac":
        return [_el("m:f", _arg("m:num", kids[0], size), _arg("m:den", kids[1], size))]
    if tag == "msub":
        return [_el("m:sSub", _arg("m:e", kids[0], size), _arg("m:sub", kids[1], size))]
    if tag == "msup":
        return [_el("m:sSup", _arg("m:e", kids[0], size), _arg("m:sup", kids[1], size))]
    if tag == "msubsup":
        return [_el("m:sSubSup", _arg("m:e", kids[0], size), _arg("m:sub", kids[1], size),
                    _arg("m:sup", kids[2], size))]
    if tag == "msqrt":
        deg_hide = OxmlElement("m:degHide")
        deg_hide.set(qn("m:val"), "1")
        e = OxmlElement("m:e")
        for k in kids:
            for c in _convert(k, size):
                e.append(c)
        return [_el("m:rad", _el("m:radPr", deg_hide), OxmlElement("m:deg"), e)]
    if tag in ("munder", "mover", "munderover"):
        return [c for k in kids for c in _convert(k, size)]
    raise ValueError(f"unsupported MathML element <{tag}> in equation")


def omath(latex, size):
    m = OxmlElement("m:oMath")
    for c in _convert(convert_to_element(latex.strip()), size):
        m.append(c)
    return m


def add_math(paragraph, latex, size=12):
    paragraph._p.append(omath(latex, size))


def add_display_math(paragraph, latex, size=12):
    para = OxmlElement("m:oMathPara")
    ppr = OxmlElement("m:oMathParaPr")
    jc = OxmlElement("m:jc")
    jc.set(qn("m:val"), "center")
    ppr.append(jc)
    para.append(ppr)
    para.append(omath(latex, size))
    paragraph._p.append(para)
