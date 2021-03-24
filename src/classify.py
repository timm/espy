#!/usr/bin/env python3
# vim: filetype=python ts=2 sw=2 sts=2 et :

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
    i.db = db; i.rx=rx;
    i.yes = i.no = 0
    i.known = {}; i.a= {}; i.b= {}; i.c= {}; i.d= {}

  def __call__(i,actual=None,predicted=None):
    return i.keep(actual,predicted)

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
