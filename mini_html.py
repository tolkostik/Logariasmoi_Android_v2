"""Μικρός αναλυτής HTML χωρίς εξωτερικές βιβλιοθήκες (μόνο Python)."""
import re
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "param", "source", "track", "wbr"}
SKIP = {"script", "style", "noscript", "svg", "template"}
BLOCK = {"div", "p", "li", "ul", "ol", "tr", "table", "section", "article", "h1", "h2", "h3",
         "h4", "h5", "h6", "header", "footer", "dl", "dt", "dd", "br", "td", "th", "a"}


class Node:
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag, attrs=None, parent=None):
        self.tag, self.attrs, self.children, self.parent = tag, dict(attrs or {}), [], parent

    def find_all(self, tag):
        out = []
        for ch in self.children:
            if isinstance(ch, Node):
                if ch.tag == tag:
                    out.append(ch)
                out.extend(ch.find_all(tag))
        return out

    def cells(self):
        """Τα κελιά (th και td) μιας γραμμής πίνακα με τη σειρά τους."""
        out = []
        for ch in self.children:
            if isinstance(ch, Node):
                if ch.tag in ("td", "th"):
                    out.append(ch)
                elif ch.tag not in ("tr", "table"):
                    out.extend(ch.cells())
        return out

    def text(self, lines=False):
        parts = []
        self._collect(parts, lines)
        s = "".join(parts)
        if lines:
            out = [re.sub(r"[ \t\xa0]+", " ", l).strip() for l in s.split("\n")]
            return [l for l in out if l]
        return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()

    def _collect(self, parts, lines):
        for ch in self.children:
            if isinstance(ch, Node):
                if ch.tag in SKIP:
                    continue
                brk = "\n" if (lines and ch.tag in BLOCK) else " "
                parts.append(brk)
                ch._collect(parts, lines)
                parts.append(brk)
            else:
                parts.append(ch)


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)


def parse(html):
    """Ανάλυση σε μικρά κομμάτια με σύντομες παύσεις: η οθόνη της εφαρμογής μένει ελεύθερη (δεν «κολλάει»)."""
    import time
    b = _Builder()
    step = 8192
    for i in range(0, len(html), step):
        b.feed(html[i:i + step])
        time.sleep(0.002)
    b.close()
    return b.root
