#!/usr/bin/env python3
# vim: filetype=python ts=2 sw=2 sts=2 et :
"""
hall: hierarhical active learning laboratory.     
(c) 2021 Tim Menzies timm@ieee.org, MIT license.     

usage: ./ball.py [OPTIONS]

    Option      |  Notes                    | Default
    ----------- | ------------------------- | ----------------------
     -data S    | input data                | ../opt/data/auto93.csv
     -seed I    | random number seed        | 10023
     -cohen F   | small effect              | .35 
     -k I       | low frequency             | 1
     -cohen F   | min difference delta      | .3
     -size F    | min bin width             | .5
     -min I     | min cluster leaf size     | 80
     -samples I | how samples to find poles | 20
     -p       I | power for distance calcs  | 2
     -far F     | distance for poles        | .75
     -k I       | low frequency             | 1
     -m I       | low fro ; e.g.            | 2
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

  def add(i, x):
    if x == "?": return x
    i.n += 1; return i.add1(x)

  def dist(i, x,y):
    if x == "?" and y=="?": return 1
    return i.dist1(x,y)

  @staticmethod
  def new(tab, at, txt):
    if "?" in txt: return Skip(at,txt)
    x = (Num if txt[0].isupper() else Sym)(at, txt)
    (tab.ys if "+" in txt or "!" in txt or "-" in txt else tab.xs).append(x)
    if "!" in txt: tab.klass =x
    return x

# -----------------------------------------------------------------------------
class Skip(Col):
  def __init__(i, at=0, txt="") : i.txt, i.at, i.n
  def add1(i,x)                 : return x
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

  def add1(i, x):
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
    tmp = div(xy, small=i.sd * my.cohen, width=len(xy)**my.size)
    for bin in merge(tmp):
      for klass, n in bin.also.seen.items():
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
    k = Sym(pos=i.pos, txt=i.txt)
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

# -----------------------------------------------------------------------------
def cluster(all, my):
  def do(here, lvl=0):
    if my.min > 2*len(here.rows): return None
    print(f"{len(here.rows):>5}" + '|.. '*lvl)
    poles=[]
    for _ in range(my.samples):
      r1, r2  = random.choice(here.rows), random.choice(here.rows)
      poles  += [(r1.dist(r2, *at), r1,r2)]
    poles.sort(key=functools.cmp_to_key(
                    lambda a,b: 0 if a[0]==b[0] else (-1 if a[0]<b[0] else 1)))
    c, l, r   = poles[ int(len(poles)*my.far) ]
    tmp       = []
    for row in here.rows:
      a       = row.dist(r, *at)
      b       = row.dist(l, *at)
      x       = (a**2 + c**2 - b**2)/(2*c)
      tmp    += [(x,row)]
    tmp.sort()
    mid = tmp[ len(tmp) // 2 ][0]
    rs, ls = all.clone(), all.clone()
    for x,row in tmp:
      (rs if x < mid else ls).add(row)
    return obj(c=c, here=here, mid=mid, l=l, r=r, 
               ls= do(ls, lvl+1), rs= do(rs, lvl+1))
  at = all,my
  return do(all)

def nodes(here,lvl=0):
  if here:
    yield lvl, t
    for y in nodes(here.ls, lvl+1): yield lvl,y
    for y in nodes(here.rs, lvl+1): yield lvl,y

def treep(here):
  for lvl,node in nodes(here):
    print(node.ys(), ("|.. " * lvl) + " " + len(node.rows))

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
    i.txt, i.rows, i.cols, i.xs, i.ys, i.klass=txt, [], [], [], [], None
    [i.add(lst) for lst in rows]

  def x(i)                : return [col.mid() for col in i.xs]
  def y(i)                : return [col.mid() for col in i.ys]
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
  def __init__(i, down=-math.inf, up=math.inf,col=None): 
     i.down, i.up, i.col, i.also = down, up, col, Sym()

def div(xy, epsilon=0.01, width=20, bin=Bin,col=None):
  while width < 4 and width < len(xy) / 2:
    width *= 1.2
  xy = sorted(xy)
  now = bin(down=xy[0][0], up=xy[0][0],col=col)
  out = [now]
  for j, (x, y) in enumerate(xy):
    if j < len(xy) - width:
      if now.also.n >= width:
        if x != xy[j + 1][0]:
          if now.up - now.down > epsilon:
            now = bin(down=now.up, up=x,col=col)
            out += [now]
    now.up = x
    now.also.add(y)
  out[0].down = -math.inf
  out[-1].up = math.inf
  return out

def merge(b4):
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
  
# Run an example.
def eg(f,d):
  print(d)
  print("\n### " + f.__name__)
  if f.__doc__: print("# " + re.sub(r"\n[\t ]*", "\n# ", f.__doc__))
  my=obj(**d)
  random.seed(my.seed)
  f(my)
