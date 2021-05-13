#!/usr/bin/env python3
# vim: filetype=python ts=2 sw=2 sts=2 et :
"""
hall: hierarhical active learning laboratory.     
(c) 2021 Tim Menzies timm@ieee.org, MIT license.     

usage: ./ball.py [OPTIONS]

    Option      |  Notes                    | Default
    ----------- | ------------------------- | ----------------------
     -data S    | input data                | ../etc/data/auto93.csv
     -seed I    | random number seed        | 10023
     -cohen F   | small effect              | .35 
     -k I       | low frequency             | 1
     -cohen F   | min difference delta      | .3
     -size F    | min bin width             | .5
     -min I     | min cluster leaf size     | 10
     -samples I | how samples to find poles | 2
     -p       I | power for distance calcs  | 2
     -far F     | distance for poles        | .9
     -top I     | max number of ranges      | 7
     -show I    | how many rules to report  | 1
     -k I       | low frequency             | 1
     -m I       | low fro ; e.g.            | 2
     -act I     | 1=optimize,2=monitor,3=safety | 1
     -elite     |  fraction of best         | 2
"""
import functools, random,  math, sys, re

# -----------------------------------------------------------------------------
# Simple base class 
# - pretty prints slots, can be easy
# - easily initialized with (e.g.) `x=obj(name='tim',age=21)`,
# - offers get/set slot access; e.g `x.age += 1`.
class obj:
  def __init__(i, **d): i.__dict__.update(d)
  def __repr__(i) : return "{" + ', '.join(
      [f":{k} {v}" for k, v in sorted(i.__dict__.items()) if k[0] != "_"]) + "}"

# -----------------------------------------------------------------------------
# - `col.new` :  is a factory for making and storing different column types.
# - `col.add` : skips missing values, increment counter, add `x`.
# - `col.norm` :  returns things in a standard range
class Col(obj):
  def norm(i, x): return x if x == "?" else i.norm1(x)

  def add(i, x, n=1):
    if x == "?": return x
    i.n += n; return i.add1(x,n)

  def dist(i, x,y):
    if x == "?" and y=="?": return 1
    return i.dist1(x,y)

  @staticmethod
  def new(tab, at, txt):
    if "?" in txt: return Skip(at,txt)
    x = (Num if txt[0].isupper() else Sym)(at, txt)
    (tab.ys if "+" in txt or "!" in txt or "-" in txt else tab.xs).append(x)
    if "!" in txt: tab.klass =x
    tab.names[txt]=at
    return x

# -----------------------------------------------------------------------------
class Skip(Col):
  def __init__(i, at=0, txt="") : i.txt, i.at, i.n = txt,at,0
  def add1(i,x,_)                 : return x
  def mid(i)                    : return "?"

# -----------------------------------------------------------------------------
# - `num.mid` : return mid point
# - `num.add1` : incrementally updates `mu` and `sd`
# - `numl.ike` : returns probability of `x`.
class Num(Col):
  def __init__(i, at=0, txt=""):
    i.txt, i.at, i.n, i.mu, i.m2, i.sd, i._all = txt, at, 0, 0, 0, 0, []
    i.lo, i.hi, i.w = 1E32, -1E32, (-1 if txt[-1] == "-" else 1)

  def mid(i)     : return i.mu
  def norm1(i,x) : return max(0, min(1, (x - i.lo)/(i.hi - i.lo + 1E-32)))
  def dist1(i,x,y):
    if   x=="?" : y   = i.norm1(y); x= 0 if y>.5 else 1
    elif y=="?" : x   = i.norm1(x); y= 0 if x>.5 else 1
    else        : x,y = i.norm1(x), i.norm1(y)
    return abs(x-y)

  def add1(i, x, _):
    i._all += [x]
    d = x - i.mu
    i.mu += d / i.n
    i.m2 += d * (x - i.mu)
    i.sd = (i.m2 / i.n)**0.5
    i.lo = min(x, i.lo)
    i.hi = max(x, i.hi)
    return x

  def like(i, x, *_):
    if not((i.mu - 4 * i.sd) < x < (i.mu + 4 * i.sd)): return 0
    var = i.sd ** 2
    denom = (math.pi * 2 * var) ** .5
    num = math.e ** (-(x - i.mu)**2 / (2 * var + 0.0001))
    return num / (denom + 1E-64)

  def discretize(i, j, my):
    xy = [(better, True)  for better in i._all] + [
          (bad,    False) for bad    in j._all]
    sd = (i.sd*i.n + j.sd*j.n)/(i.n+j.n)
    tmp = div(xy, sd * my.cohen, len(xy)**my.size)
    #print(i.txt,len(tmp),sd*my.cohen)
    tmp=merge(tmp)
    #print(i.txt,len(tmp))
    for bin in tmp:
      for klass, n in bin.also.seen.items():
        if not (bin.down == -math.inf and bin.up == math.inf):
          yield n, klass, (bin.down, bin.up)

# -----------------------------------------------------------------------------
# - `sym.mid` : return mid point
# - `sym.like` : returns probability of `x`.
# - `sym.add1` : incrementally update symbol counts, and the mode.
class Sym(Col):
  def __init__(i, at=0, txt=""):
    i.txt, i.at, i.n, i.seen, i.most, i.mode = txt, at, 0, {}, 0, None

  def mid(i)                : return i.mode
  def norm1(i,x)            : return x
  def like(i, x, prior, my) : return (i.seen.get(x,0) + my.m*prior) / (i.n+my.m)
  def dist1(i,x,y)          : return 0 if x==y else 1
  def ent(i)                : 
    return sum(-v / i.n * math.log(v / i.n) for v in i.seen.values())

  def add1(i, x,n=1):
    tmp = i.seen[x] = i.seen.get(x, 0) + n
    if tmp > i.most: i.most, i.mode = tmp, x
    return x

  def simplified(i, j):
    k = i.merge(j)
    e1, n1 = i.ent(), i.n
    e2, n2 = j.ent(), j.n
    e, n = k.ent(), k.n
    if e1 + e2 < 0.01 or e * .95 < n1 / n * e1 + n2 / n * e2:
      return k

  def merge(i, j):
    k = Sym(at=i.at, txt=i.txt)
    for seen in [i.seen, j.seen]:
      for x, n in seen.items(): k.add(x, n)
    return k

  def discretize(i, j, _):
    for k in (i.seen | j.seen):  # a 23 b 50
      yield i.seen.get(k, 0), True, (k, k)
      yield j.seen.get(k, 0), False, (k, k)

# -----------------------------------------------------------------------------
class Row(obj):
  def __init__(i,lst): 
    i.cells, i.cooked =  lst, None

  def dist(i,j,t,my):
    d,n = 0, 1E-31
    for col in t.xs:
      tmp = col.dist( i.cells[col.at], j.cells[col.at] )
      d  += tmp**my.p
      n  += 1
    return (d/n)**(1/my.p)

  def dominate(i, j, t):
    s1, s2, n = 0, 0, len(t.ys)
    for col in t.ys:
      a   = col.norm(i.cells[col.at])
      b   = col.norm(j.cells[col.at])
      s1 -= math.e**(col.w * (a - b) / n)
      s2 -= math.e**(col.w * (b - a) / n)
    return s1 / n < s2 / n

def ordered(lst):
  return sorted(lst, key=functools.cmp_to_key(
         lambda a,b: 0 if a[0]==b[0] else (-1 if a[0]<b[0] else 1)))


# -----------------------------------------------------------------------------
def cluster(all, my):
  def do(tab,lvl=0):
    if stop > 2*len(tab.rows): return None
    #if  len(tab.rows) > 2048:
     # tab = all.clone(random.sample(tab.rows, 2048))
    print("|.. " * lvl)
    poles=[]
    for _ in range(my.samples):
      l0,r0 = random.choice(tab.rows),random.choice(tab.rows)
      poles += [(l0.dist(r0, *at), l0,r0)]
    poles = ordered(poles)
    c, l, r   = poles[ int(len(poles)*my.far) ]
    tmp       = []
    rs, ls = all.clone(), all.clone()
    for row in tab.rows:
      a       = row.dist(r, *at)
      b       = row.dist(l, *at)
      x       = (a**2 + c**2 - b**2)/(2*c)
      tmp    += [(x,row)]
    tmp = ordered(tmp)
    mid = tmp[ len(tmp) // 2 ][0]
    for z,row in tmp: (rs if z < mid else ls).add(row)
    out=  obj(c=c,here=tab,mid=mid,l=l,r=r,ls=None,rs=None)
    print(len(rs.rows), len(ls.rows))
    report=[]
    for rule in contrast(rs,ls,my):
      selected, n, effect, txt = canonical(tab, rule)
      if effect[0] != None:
        report += [[txt, n] + [round(x,2) for x in effect]]
    printm(report)
    print("")
    out.rs = do(rs, lvl+1)
    out.ls = do(ls, lvl+1)
    #if r.dominate(l,all): out.rs = do(rs, lvl+1)
    #else:                 out.ls = do(ls, lvl+1)
    return out

  at = all,my
  stop = max(my.min, len(all.rows)**0.5)
  print(1)
  return do(all)

def printm(matrix):
  s = [[str(e) for e in row] for row in matrix]
  lens = [max(map(len, col)) for col in zip(*s)]
  fmt = ' | '.join('{{:>{}}}'.format(x) for x in lens)
  for row in [fmt.format(*row) for row in s]:
    print(row)


def nodes(tree, lvl=0):
  if tree:
    yield lvl, tree
    for x in nodes(tree.ls, lvl+1): yield x
    for x in nodes(tree.rs, lvl+1): yield x

def leaves(tree):
  for _,node in nodes(tree):
    if not node.ls:
      yield node

def treep(tree, tab):
  def r(x):    return round(x,2)
  def rs(lst): return ', '.join([f"{r(x):>8}" for x in lst])
  for lvl,node in nodes(tree):
    tab = node.here
    n = len(tab.rows)
    mid = tab.y()
    print(rs([n]+ mid), ("|.. " * lvl)) # + f" {len(tab.rows)}")

# -----------------------------------------------------------------------------
# - Given a rows of data, and row0 defines column name and type, store the 
#   rows, summarized in the headers.
# - Header names starting with upper case letters are numerics 
#   (others are symbols).
# - Names ending in '+-' are goals to be maximized or minimized.
# - Names containing '?' are ignored in the reasoning.
# - `tab.x` :          returns mid point of the independent variables
# - `tab.y` :          returns mid point of the dependent variables
# - `tab.rowy` :       returns dependent variables of a row
# - `tab.clone` :      return a new table with the same structure as this one.
# - `tab.add1`  :      if this is row0, create the headers. 
#                      Else update the headers with 'row' 
#                      then store the 'row' in 'rows'
# - `tab.like` :       report how much this table likes 'row'
# - `tab.classify` :   For a set of tables, including this one, find 
#                      which one mostlikes 'row'. Returns a tuple (mostlike,tab
# - `tab.dominate` :   Does row1 win over row2"
# - `tab.domianates` : Return rows sorted by domination score."
class Tab(obj):
  def __init__(i, rows=[],txt=""):
    i.names,i.txt, i.rows, i.cols, i.xs, i.ys, i.klass={}, txt, [], [], [], [], None
    [i.add(lst) for lst in rows]

  def x(i)                : return [col.mid() for col in i.xs]
  def y(i)                : return [col.mid() for col in i.ys]
  def mid(i)              : return Row([col.mid() for col in i.cols])
  def rowy(i, row)        : return [row.cells[col.at] for col in i.ys]
  def clone(i,a=[],txt=""): return Tab(txt=txt,rows=[[c.txt for c in i.cols]] + a)
  def like(i, row, my)    : return i.classify(row, my)[0]
  def add(i, row):
    row = row.cells if type(row)==Row else row
    if    i.cols : i.rows += [Row([col.add(x) for col, x in zip(i.cols,row)])]
    else: i.cols = [Col.new(i, at, txt) for at, txt in enumerate(row)]

  def dominates(i,rows=None):
    gt= lambda a,b: 0 if id(a)==id(b) else (-1 if a.dominate(b,i) else 1)
    return sorted(rows or i.rows, key=functools.cmp_to_key(gt))

  def classify(i, row, my, tabs=[]):
    tabs = [i] + tabs
    n = sum(len(t.rows) for t in tabs)
    mostlike,out = -math.inf,None
    for t in tabs:
      out = out or t
      prior = (len(t.rows) + my.k) / (n + my.k * len(tabs))
      tmp = math.log(prior)
      for col in t.xs:
        v = row[col.at]
        if v != "?":
          if inc := col.like(v, prior, my): tmp += math.log(inc)
      if tmp > mostlike:
        mostlike, out = tmp, t
    return math.e**mostlike, out

# -----------------------------------------------------------------------------
class Bin(obj):
  def __init__(i, down=-math.inf, up=math.inf): 
     i.down, i.up, i.also = down, up, Sym()

def div(xy, epsilon, width):
  while width < 4 and width < len(xy) / 2:
    width *= 1.2
  xy = sorted(xy)
  now = Bin(down=xy[0][0], up=xy[0][0])
  out = [now]
  for j, (x, y) in enumerate(xy):
    if j < len(xy) - width:
      if now.also.n >= width:
        if x != xy[j + 1][0]:
          if now.up - now.down > epsilon:
            now = Bin(down=now.up, up=x)
            out += [now]
    now.up = x
    now.also.add(y)
  out[0].down = -math.inf
  out[-1].up = math.inf
  return out

def merge(b4):
  #print("\nmerge", len(b4),[x.also.seen for x in b4])
  j, tmp, n = 0, [], len(b4)
  while j < n:
    a = b4[j]
    if j < n - 1:
      b = b4[j + 1]
      if c := a.also.simplified(b.also):
        a = Bin(a.down, b.up)
        a.also = c
        j += 1
    tmp += [a]
    j += 1
  return merge(tmp) if len(tmp) < len(b4) else b4
     
# -----------------------------------------------------------------------------
def classify(row, my, tabs): return tabs[0].classify(row,my,tabs[1:])

def classifier(src, my, wait=20):
  all, tabs,seen, results = None, [], {}, Abcd()
  for pos,row in enumerate(src):
    if pos:
      klass = row[all.klass.at]
      if pos > wait:
        _,what = classify(row,my,tabs)
        results.tell(klass, what.txt)
      if klass not in seen: 
        new = all.clone(txt=klass)
        tabs += [new]
        seen[klass] = new
      seen[klass].add(row)
    else:
      all= Tab(rows=[row])
  results.header()
  results.ask()
 
"""

Sym   Num
happy age   alive
y     0     y
y     1     y
y     2     y
y     3     y
y     8     y
n     19    n
n     40    y
n     50    y
y     80    n
y     90    y
y     110   n
y     120   y
n     130 n
n     140 n
n     150 n 
n     2000 n

Bins for Nums
lo <= x < hi

1. bin.lo =   0  bin.hi = 19      
2  bin.lo =  19  bin.hi=130      
3. bin.lo = 130, bin.hi = 2000 

1. bin.lo = -inf  bin.hi = 19    also: #y=5 #n=0
2  bin.lo =  19  bin.hi=130      also: #y=4 #n=3
3. bin.lo = 130, bin.hi = inf    also: #y=0 #n=4

Bins for Sym
lo = x = hi

4. bin.lo = n  bin.hi = n    also: #y=2 #n=5
5  bin.lo = y  bin.hi=y      also: #y=7 #n=2


"""
def contrast(here, there, my):
  def seen():
    return {(kl, (col1.txt, col1.at, span)): f
            for col1, col2 in zip(here.xs, there.xs)
            for f, kl, span in col1.discretize(col2, my)}

  def like(lst, kl):
    prod = math.prod
    prior = (hs[kl] + my.k) / (n + my.k * 2)
    fs = {}
    for txt, pos, span in lst:
      fs[txt] = fs.get(txt, 0) + f.get((kl, (txt, pos, span)), 0)
    like = prior
    for val in fs.values(): 
      like *= (val + my.m*prior) / (hs[kl] + my.m)
    return like

  def value(lst):
    b = like(lst, True)
    r = like(lst, False)
    if my.act ==3:
      return 1/(b+r)
    if my.act ==2:
      return r**2 / (b + r) if (b+r) > 0.01 and r > b else 0
    else: 
      return b**2 / (b + r) if (b+r) > 0.01 and b > r else 0

  def solos():
    pairs=[]
    for kl, x in f:
      if kl == True:
        if s := value([x]):  # if zero, then skip x
          pairs += [(s, x)]
    return pairs

  def top(n,pairs): 
     return [x for _, x in sorted(pairs, reverse=True)[:n]] #my.top]]

  f = seen()
  n = len(here.rows) + len(there.rows)
  hs = {True: len(here.rows), False: len(there.rows)}
  ranges= sorted(solos(),reverse=True)
  for val, (col,_,(lo,hi)) in ranges:
    most,least= ranges[0][0], ranges[-1][0]
    val= int(100*(val-least)/(most-least))
    print(f"{1 if val==0 else val:>3}", col, showSpan((lo,hi)))
  print("")
  # ignore dull ranges
  goodRanges = top(my.top, ranges)
  # find all combinations of good ranges
  combos     = subsets(goodRanges)
  # score those combinations
  scores     = [(value(combo),combo) for combo in combos]
  # grad the top scoring ranges
  rules      = top(my.show,scores)
  # look for ranges taht can be pruned e.g. (-inf,n) and  (n,inf)
  tidied     = [tidy(rule) for rule in rules]
  # with pruned ranges removed, now we must prune repeated rules.
  uniques    = {str(rule): rule for rule in tidied}
  # from the dictionary of uniques, return the unique rules
  return list(uniques.values())

def subsets(l):
  out = [[]]
  for x in l:
    out += [sub + [x] for sub in out]
  return out[1:]

def parts(d):
  for col,_,spans in d:
    spans = [showSpan(span) for span in spans]
    yield f"{col} {spans}"

def selects(tab, rule):
  def any(val, spans):
    for lo, hi in spans:
      if lo == hi:
        if lo == val:
          return True
      elif lo <= val < hi:
        return True
    return False

  def all(rule, row):
    print(">>>",rule)
    for _,col,spans in rule:
      val = row.cells[col]
      if val != "?":
        if not any(val, spans):
          return False
    return True
  return tab.clone([row for row in tab.rows if all(rule, row)])

def showSpan(x):
    return (f"={x[0]}" if x[0] == x[1] else (
        f"<={x[1]}"if x[0] == -math.inf else (
            f">={x[0]}"if x[1] == math.inf else (f"[{x[0]}..{x[1]})"))))

def combineRanges(b4):
    if len(b4) == 1 and b4 == [(-math.inf, math.inf)]:
      return None
    j, tmp = 0, []
    while j < len(b4):
      a = b4[j]
      if j < len(b4)-1:
        b = b4[j+1]
        if a[1] == b[0]:
          a = (a[0], b[1])
          j += 1
      tmp += [a]
      j += 1
    return tmp if len(tmp) == len(b4) else combineRanges(tmp)

def showRule(d):
    return ' and '.join([k + ' (' + (' or '.join(map(showSpan, v)) + ')')
                         for k, v in d.items()])

# XXX recreate the rule with culled ranges
def tidy(rule):
  cols = {}
  where={}
  for col, at, span in rule:
    where[col]=at
    cols[col] = cols.get(col, []) + [span]
  d = {}
  for k, v in cols.items():
    s = f"{k}"
    if v1 := combineRanges(sorted(v)):
      d[k] = v1
  #return [len(found.rules)] +  found.y() + [showRule(d)]
  return [(k,where[k],d[k])  for k in d]


def canonical(tab, rule):
  cols = {}
  for col, _, span in rule:
    cols[col] = cols.get(col, []) + [span]
  d = {}
  for k, v in cols.items():
    s = f"{k}"
    if v1 := combineRanges(sorted(v)):
      d[k] = v1
  found = selects(tab, d)
  #return [len(found.rules)] +  found.y() + [showRule(d)]
  return found, len(found.rows), found.y(), showRule(d)
# --------------------------------------
# Throw actual and predicted at an Abcd, accumulating
# precision, recall, etc
class Abcd: 
  def __init__(i,db="all",rx="all"):
    i.db = db; i.rx=rx; i.yes = i.no = 0
    i.known = {}; i.a= {}; i.b= {}; i.c= {}; i.d= {}

  def tell(i,actual,predict):
    i.knowns(actual)
    i.knowns(predict)
    if actual == predict: i.yes += 1 
    else                : i.no += 1
    for x in  i.known:
      if actual == x:
        if  predict == actual: i.d[x] += 1 
        else                 : i.b[x] += 1
      else:
        if  predict == x     : i.c[x] += 1 
        else                 : i.a[x] += 1

  def knowns(i,x):
    if not x in i.known: i.known[x]= i.a[x]= i.b[x]= i.c[x]= i.d[x]= 0.0
    i.known[x] += 1
    if (i.known[x] == 1): i.a[x] = i.yes + i.no

  def header(i):
    print("#",('{0:20s} {1:11s}  {2:4s}  {3:4s} {4:4s} '+ \
           '{5:4s}{6:4s} {7:3s} {8:3s} {9:3s} '+ \
           '{10:3s} {11:3s}{12:3s}{13:10s}').format(
      "db", "rx", "n", "a","b","c","d","acc","pd","pf","prec", "f","g","class"))
    print('-'*100)

  def ask(i):
    def p(y) : return int(100*y + 0.5)
    def n(y) : return int(y)
    pd = pf = pn = prec = g = f = acc = 0
    for x in i.known:
      a= i.a[x]; b= i.b[x]; c= i.c[x]; d= i.d[x]
      if (b+d)    : pd   = d     / (b+d)
      if (a+c)    : pf   = c     / (a+c)
      if (a+c)    : pn   = (b+d) / (a+c)
      if (c+d)    : prec = d     / (c+d)
      if (1-pf+pd): g    = 2*(1-pf)*pd / (1-pf+pd)
      if (prec+pd): f    = 2*prec*pd/(prec+pd)
      if (i.yes + i.no): acc= i.yes/(i.yes+i.no)
      print("#",('{0:20s} {1:10s} {2:4d} {3:4d} {4:4d} '+ \
          '{5:4d} {6:4d} {7:4d} {8:3d} {9:3d} '+ \
         '{10:3d} {11:3d} {12:3d} {13:10s}').format(i.db,
          i.rx,  n(b + d), n(a), n(b),n(c), n(d), 
          p(acc), p(pd), p(pf), p(prec), p(f), p(g),x))

# --------------------------------------
# From files or standard input or a string, return an iterator for the lines.
def csv(src=None):
  def lines(src):
    for line in src:
      line = re.sub(r'([\n\t\r ]|#.*)', '', line)
      if line: 
        line = line.split(",")
        line = [coerce(x) for x in line]
        yield line
  if src and src[-4:] == ".csv":
    with open(src) as fp:  
      for out in lines(fp): yield out
  else:
    src = src.split("\n") if src else sys.stdin
    for out in lines(src):
      yield out

# If appropriate, coerce `string` into an integer or a float.
def coerce(string):
  try: return int(string)
  except Exception:
    try: return float(string)
    except Exception: return string
  
import cProfile
import io
import  pstats 
from pstats import SortKey

def profile(func):
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        retval = func(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        sortby = SortKey.CUMULATIVE  # 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
        return retval
    return wrapper

from contextlib import contextmanager
import time


@contextmanager
def watch():
  start = time.perf_counter()
  yield
  print(time.perf_counter() - start)


# Run an example.
def eg(f,d):
  print("\n### " + f.__name__)
  if f.__doc__: print("# " + re.sub(r"\n[\t ]*", "\n# ", f.__doc__))
  my=obj(**d)
  random.seed(my.seed)
  f(my)


    
