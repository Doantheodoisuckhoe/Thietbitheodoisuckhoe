# Bộ đọc/ghi s-expression tối giản cho file KiCad
import re

class Q(str):
    """Chuỗi có ngoặc kép trong file gốc."""
    pass

_tok = re.compile(r'\s*(\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+)', re.S)

def parse(text):
    pos = 0
    stack = [[]]
    n = len(text)
    while True:
        m = _tok.match(text, pos)
        if not m:
            break
        t = m.group(1)
        pos = m.end()
        if t == '(':
            stack.append([])
        elif t == ')':
            x = stack.pop()
            stack[-1].append(x)
        elif t.startswith('"'):
            s = t[1:-1].replace('\\"', '"').replace('\\\\', '\\').replace('\\n', '\n')
            stack[-1].append(Q(s))
        else:
            stack[-1].append(t)
    return stack[0]

def q(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'

def dump(x, ind=0):
    if isinstance(x, list):
        if all(not isinstance(e, list) for e in x):
            return '\t' * ind + '(' + ' '.join(atom(e) for e in x) + ')'
        head = []
        rest = []
        for i, e in enumerate(x):
            if isinstance(e, list):
                rest = x[i:]
                break
            head.append(atom(e))
        s = '\t' * ind + '(' + ' '.join(head) + '\n'
        for e in rest:
            if isinstance(e, list):
                s += dump(e, ind + 1) + '\n'
            else:
                s += '\t' * (ind + 1) + atom(e) + '\n'
        return s + '\t' * ind + ')'
    return '\t' * ind + atom(x)

def atom(e):
    if isinstance(e, Q):
        return q(e)
    return str(e)

def find(x, key):
    for e in x:
        if isinstance(e, list) and e and e[0] == key:
            return e
    return None

def findall(x, key):
    return [e for e in x if isinstance(e, list) and e and e[0] == key]
