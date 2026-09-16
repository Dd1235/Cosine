"""directorymanagement: pure simulation.  Keep the tree with a sorted child map per node, a cached
subtree size updated along the path to the root on every MKDIR/RM (<= 5000 of them), and a LIFO stack
of undo records (MKDIR -> detach the node, RM -> re-attach the saved subtree, CD -> restore the old
current pointer).  LS/TREE only ever need 5 lines from each end, so TREE walks the leftmost chain for
the head and the rightmost chain for the tail instead of materialising the traversal.
Two independent implementations are compared: the incremental one above and a naive reference that
deep-copies the whole state before every undoable command and restores the copy on UNDO."""
import random, copy

class Node:
    __slots__ = ('name','par','ch','sz')
    def __init__(s, name, par):
        s.name, s.par, s.ch, s.sz = name, par, {}, 1

def fmt_ls(names):
    if not names: return ["EMPTY"]
    if len(names) <= 10: return list(names)
    return list(names[:5]) + ["..."] + list(names[-5:])

def preorder(node):
    out = [node.name]
    for k in sorted(node.ch): out += preorder(node.ch[k])
    return out

class Fast:
    """incremental implementation (the intended one)"""
    def __init__(s):
        s.root = Node("root", None); s.cur = s.root; s.undo = []
    def bump(s, node, d):
        while node: node.sz += d; node = node.par
    def run(s, cmd):
        op = cmd[0]
        if op == 'MKDIR':
            name = cmd[1]
            if name in s.cur.ch: return ["ERR"]
            nd = Node(name, s.cur); s.cur.ch[name] = nd; s.bump(s.cur, 1)
            s.undo.append(('MKDIR', nd)); return ["OK"]
        if op == 'RM':
            name = cmd[1]
            if name not in s.cur.ch: return ["ERR"]
            nd = s.cur.ch.pop(name); s.bump(s.cur, -nd.sz)
            s.undo.append(('RM', s.cur, nd)); return ["OK"]
        if op == 'CD':
            name = cmd[1]
            if name == '..':
                if s.cur.par is None: return ["ERR"]
                old = s.cur; s.cur = s.cur.par; s.undo.append(('CD', old)); return ["OK"]
            if name not in s.cur.ch: return ["ERR"]
            old = s.cur; s.cur = s.cur.ch[name]; s.undo.append(('CD', old)); return ["OK"]
        if op == 'SZ': return [str(s.cur.sz)]
        if op == 'LS': return fmt_ls(sorted(s.cur.ch))
        if op == 'TREE':
            if not s.cur.ch: return ["EMPTY"]
            lines = preorder(s.cur)          # <= 5000 nodes; the real solution walks only the ends
            if len(lines) <= 10: return lines
            return lines[:5] + ["..."] + lines[-5:]
        if op == 'UNDO':
            if not s.undo: return ["ERR"]
            rec = s.undo.pop()
            if rec[0] == 'MKDIR':
                nd = rec[1]; del nd.par.ch[nd.name]; s.bump(nd.par, -nd.sz)
            elif rec[0] == 'RM':
                _, par, nd = rec; par.ch[nd.name] = nd; s.bump(par, nd.sz)
            else:
                s.cur = rec[1]
            return ["OK"]
        raise ValueError(cmd)

class Ref:
    """naive reference: full deep copy before each successful undoable command"""
    def __init__(s):
        s.root = Node("root", None); s.cur = s.root; s.snaps = []
    def size(s, node):
        return 1 + sum(s.size(c) for c in node.ch.values())
    def path(s, node):
        p = []
        while node.par is not None: p.append(node.name); node = node.par
        return p[::-1]
    def snapshot(s):
        pth = s.path(s.cur)
        s.snaps.append((copy.deepcopy(s.root), pth))
    def run(s, cmd):
        op = cmd[0]
        if op == 'MKDIR':
            name = cmd[1]
            if name in s.cur.ch: return ["ERR"]
            s.snapshot()
            s.cur.ch[name] = Node(name, s.cur); return ["OK"]
        if op == 'RM':
            name = cmd[1]
            if name not in s.cur.ch: return ["ERR"]
            s.snapshot(); del s.cur.ch[name]; return ["OK"]
        if op == 'CD':
            name = cmd[1]
            if name == '..':
                if s.cur.par is None: return ["ERR"]
                s.snapshot(); s.cur = s.cur.par; return ["OK"]
            if name not in s.cur.ch: return ["ERR"]
            s.snapshot(); s.cur = s.cur.ch[name]; return ["OK"]
        if op == 'SZ': return [str(s.size(s.cur))]
        if op == 'LS': return fmt_ls(sorted(s.cur.ch))
        if op == 'TREE':
            if not s.cur.ch: return ["EMPTY"]
            lines = preorder(s.cur)
            if len(lines) <= 10: return lines
            return lines[:5] + ["..."] + lines[-5:]
        if op == 'UNDO':
            if not s.snaps: return ["ERR"]
            root, pth = s.snaps.pop()
            s.root = root; s.cur = root
            for nm in pth: s.cur = s.cur.ch[nm]
            return ["OK"]
        raise ValueError(cmd)

sample = """MKDIR dira|CD dirb|CD dira|MKDIR a|MKDIR b|MKDIR c|CD ..|MKDIR dirb|CD dirb|MKDIR x|CD ..|
MKDIR dirc|CD dirc|MKDIR y|CD ..|SZ|LS|TREE|RM dira|TREE|UNDO|TREE""".replace("\n", "").split("|")
f = Fast(); out = []
for c in sample: out += f.run(c.split())
expected = (["OK","ERR"] + ["OK"]*13 + ["9"] + ["dira","dirb","dirc"] +
            ["root","dira","a","b","c","dirb","x","dirc","y"] + ["OK"] +
            ["root","dirb","x","dirc","y"] + ["OK"] +
            ["root","dira","a","b","c","dirb","x","dirc","y"])
assert out == expected, (out, expected)

random.seed(41)
names = ['a','b','c','d']
bad = 0
for t in range(200):
    f, r = Fast(), Ref()
    for step in range(120):
        op = random.choices(['MKDIR','RM','CD','SZ','LS','TREE','UNDO'],
                            weights=[25,10,25,8,8,8,16])[0]
        if op in ('MKDIR','RM'): cmd = [op, random.choice(names)]
        elif op == 'CD': cmd = ['CD', random.choice(names + ['..','..'])]
        else: cmd = [op]
        a, b = f.run(cmd), r.run(cmd)
        if a != b:
            bad += 1; print("MISMATCH", cmd, a, b); break
print("sample transcript reproduced exactly; random cross-check mismatches =", bad)
