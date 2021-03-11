#!/usr/bin/env python3
# vim: filetype=python ts=2 sw=2 sts=2 et :
"""
es.py /əˈspī/ verb LITERARY see something that is hidden, or obscure.
Optimizer, written as a data miner.  
  
Break the data up into regions of 'bad' and 'better'. 'Interesting'
things occur at very different frequencies in 'bad' and 'better'.
Find interesting bits. Combine them. Repeat. Nearly all this
processing takes log linear time.
   
     :-------:                 explore  = better==bad
     | Ba    | Bad <----.      planning = max(better - bad)
     |    56 |          |      monitor  = max(bad - better)
     :-------:------:   |      tabu     = min(bad + better)
             | B    |   v
             |    5 | Better
             :------:
"""
import math,sys,re

HELP   = dict(   
           k     = (1,  "k Bayes low frequency control"),
           m     = (2,  "m Bayes low frequency control"),
           best  = (.5, "size of best set"), 
           size  = (.5, "min size of breaks"),
           cohen = (.2, "var min"),
           dir   = "opt/data/",
           data  = "auto93.csv"
           )

LO     = -math.inf
HI     =  math.inf
TINY   = 1E-32
NO     = "?"
BAD    = "bad"
BETTER = "better"
class A:
  def __init__(i, **d): i.__dict__.update(d)
  def __repr__(i): 
    lst=sorted(i.__dict__.items())
    return "{"+ ', '.join( [f":{k} {v}" for k,v in lst if k[0] != "_"])+"}"

class Bin(A):
  def __init__(i,down=LO, up=HI): i.down, i.up, i.also= down,up,Sym()
  def has(i,x): return (x==i.down) if (i.down==i.up) else (i.down <= x < i.up)
  def __repr__(i):  return (
    f"={i.up}"    if  i.down == i.up           else (
    f"anything"   if i.down == LO and i.up==HI else (
    f"<{i.up}"    if i.down == LO              else (
    f">={i.down}" if i.up == HI                else (
    f"[{i.down}..{i.up})")))))

class Tab(A):
  def __init__(i,src):
    i.rows,i.cols,i.xs,i.ys = [],[],[],[]
    for row in src:
      row = row.cells if type(row)==Row else row
      if    i.cols: i.rows += [Row([col.add(x) for col,x in zip(i.cols,row)],i)]
      else: 
         i.cols = [(Num(pos,txt) if txt[0].isupper() else Sym(pos,txt)) 
                    for pos,txt in enumerate(row)]
         i.ys   = [col for col in i.cols if     col.goalp]
         i.xs   = [col for col in i.cols if not col.goalp]
  def clone(i,inits=[]): return Tab([[col.txt for col in i.cols]] + inits)
  def goals(i):          return [col.mid() for col in i.ys]
 
class Row(A):
  def __init__(i,cells,tab): i.cells, i.tab= cells,tab
  def __lt__(i,j):
    s1,s2,n = 0,0,len(i.tab.ys)
    for col in i.tab.ys:
      pos,w = col.pos, col.w
      a,b   = i.cells[pos], j.cells[pos]
      a,b   = col.norm(a), col.norm(b)
      s1   -= math.e**(w*(a-b)/n)
      s2   -= math.e**(w*(b-a)/n)
    return s1/n < s2/n

class Sym(A):
  def __init__(i,pos=0,txt=""): 
    i.pos,i.txt,i.n,i.goalp = pos,txt,0,False
    i.seen, i.mode, i.most = {},None,0
  def add(i,x,n=1):
    if x != NO:
      i.n += n
      tmp = i.seen[x] = n + i.seen.get(x,0)
      if tmp > i.most:
        i.most, i.mode = tmp, x
    return x
  def ent(i): return sum(-v/i.n * math.log(v/i.n) for v in i.seen.values())
  def discretize(i,j,_): 
    out = [Bin(k,k) for k in (i.seen | j.seen)]
    for b in out: 
      b.also[BETTER] = i.n
      b.also[BAD] = j.n
    return out
  def simplified(i,j):
    k     = i.merge(j)
    e1,n1 = i.ent(), i.n
    e2,n2 = j.ent(), j.n
    e,n   = k.ent(), k.n
    if e1+e2<0.01 or e*.95 < n1/n*e1 + n2/n*e2:
      return k
  def merge(i, j):
    k = Sym(pos=i.pos, txt=i.txt)
    for seen in [i.seen, j.seen]:
      for x,n in seen.items(): k.add(x,n)
    return k

class Num(A):
  def __init__(i,pos=0,txt=""): 
    i.pos,i.txt,i.n = pos,txt,0
    i.w     = -1 if "-"==txt[-1] else 1
    i.goalp = "+" == txt[-1] or "-" == txt[-1] 
    i._all, i.ok = [],False
  def add(i,x,**_):
    if x == NO: return x
    i.n += 1
    x    = float(x)
    i._all += [x]
    i.ok    = False
    return x
  def _alls(i):
    i._all = i._all if i.ok else sorted(i._all)
    i.ok = True
    return i._all
  def sd(i):     return (i._per(.9) - i._per(.1))/2.56
  def mid(i)   : return i._per(.5) if i._all else None 
  def _per(i,p): a= i._alls(); return a[int(p*len(a))]
  def norm(i,x): a= i._alls(); return (x-a[0])/(a[-1] - a[0] + TINY)
  def discretize(i,j,THE):
    yes,no="better","bad"
    xy  = [(better,yes) for better in i._all] + [
           (bad,no)     for bad    in j._all]
    tmp = div(xy, tooSmall=i.sd()*THE.cohen, width=len(xy)**THE.size)
    return merge(tmp)

def div(xy, tooSmall=0.01, width=20):
  while width < 4 and width < len(xy) / 2: width *= 1.2
  xy = sorted(xy)
  now = Bin(down=xy[0][0], up=xy[0][0])
  out = [now]
  for j,(x,y) in enumerate(xy):
    if j < len(xy) - width:
      if now.also.n >= width:
        if x != xy[j+1][0]:
          if now.up - now.down > tooSmall:
            now  = Bin(down=now.up, up=x)
            out += [now]
    now.up = x
    now.also.add(y)
  out[ 0].down = LO
  out[-1].up   = HI
  return out
 
def merge(b4):
  j, tmp, n = 0, [], len(b4)
  while j < n:
    a = b4[j]
    if j < n - 1:
      b  = b4[j+1]
      if c := a.also.simplified(b.also):
        a = Bin(a.down, b.up)
        a.also = c
        j += 1
    tmp += [a]
    j   += 1
  return merge(tmp) if len(tmp) < len(b4) else b4
 
def csv(file):
  with open(file) as fp:
    for line in fp: 
      line = re.sub(r'([\n\t\r ]|#.*)','',line)
      if line:
        yield  line.split(",")
