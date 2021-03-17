#!/usr/bin/env python3
# vim: filetype=python ts=2 sw=2 sts=2 et :
"""
ball: a Bayesian active learning laboratory.    
(c) 2021 Tim Menzies timm@ieee.org, MIT license.

usage: ./ball.py [OPTIONS]
"""
import functools, random, math, sys, re
from types import FunctionType as fun

OPTIONS = dict(data=("../opt/data/auto93.csv",
                     "input data. Defaults to standard input"),
               do=("?", "some start up function(s) to run"),
               seed=(10023, "random number seed"),
               k=(1, "low frequency"),
               m=(2, "low fro"))
"""
Option         |  Notes
---------------|:----------------------------------------------
 -data S       | input data. Defaults to standard input; e.g. []
 -do S         | some start up function(s) to run; e.g. [?]
 -seed I       | random number seed; e.g. [10023]
 -k I          | low frequency ; e.g. [1]
 -m I          | low fro ; e.g. [2]
 -h            | show help text
"""


class obj:
  """Simple base class that  pretty prints slots, that can be easy
  initialized with (e.g.) `x=obj(name='tim',age=21)`,
  with names slots we can get or set; e.g `x.age += 1`."""
  def __init__(i, **d): i.__dict__.update(d)
  def __getitem__(i, k): return i.__dict__[k]
  def __setitem__(i, k, v): i.__dict__[k] = v
  def __contains__(i, k): return k in i.__dict__
  def __repr__(i): return "{" + ', '.join(
      [f":{k} {v}" for k, v in sorted(i.__dict__.items()) if k[0] != "_"]) + "}"


class Col(obj):
  @staticmethod
  def new(tab, at, txt):
    "Factory for making and storing different column types."
    x = (Num if txt[0].isupper() else Sym)(at, txt)
    if "?" not in txt:
      (tab.ys if Col.goalp(txt) else tab.xs).append(x)
    return x

  @staticmethod
  def goalp(txt):
    "Goal names end in `+` or `-`."
    return "+" == txt[-1] or "-" == txt[-1]

  def add(i, x):
    "Skip missing values, increment counter, add `x`."
    if x == "?": return x
    i.n += 1
    return i.add1(x)


class Num(Col):
  def __init__(i, at=0, txt=""):
    i.txt, i.at, i.n, i.mu, i.m2, i.sd = txt, at, 0, 0, 0, 0

  def mid(i):
    "Return mid point"
    return i.mu

  def add1(i, x):
    "Incrementally update `mu` and `sd`."
    d = x - i.mu
    i.mu += d / i.n
    i.m2 += d * (x - i.mu)
    i.sd = (i.m2 / i.n)**0.5
    return x

  def like(i, x, *_):
    "Returns probability of `x`."
    if not((i.mu - 4 * i.sd) < x < (i.mu + 4 * i.sd)): return 0
    var = i.sd ** 2
    denom = (math.pi * 2 * var) ** .5
    num = math.e ** (-(x - i.mu)**2 / (2 * var + 0.0001))
    return num / (denom + 1E-64)


class Sym(Col):
  def __init__(i, at=0, txt=""):
    i.txt, i.at, i.n, i.seen, i.most, i.mode = txt, at, 0, {}, 0, None

  def mid(i):
    "Returns mid point."
    return i.mode

  def like(i, x, prior, my):
    "Returns probability of `x`."
    return (i.seen.get(x, 0) + my.m * prior) / (i.n + my.m)

  def add1(i, x):
    "Incrementally update symbol counts, and the mode."
    tmp = i.seen[x] = i.seen.get(x, 0) + 1
    if tmp > i.most: i.most, i.mode = tmp, x
    return x


class Tab(obj):
  """
   - Given a rows of data, and row0 defines column name and type, store the rows, summarized in the headers.
   - Header names starting with upper case letters are numerics (others are symbols).
   - Names ending in '+-' are goals to be maximized or minimized.
   - Names containing '?' are ignored in the reasoning."""
  def __init__(i, rows=[]):
    i.rows, i.cols, i.xs, i.ys = [], [], [], []
    [i.add(lst) for lst in rows]

  def x(i):
    "Return mid values of the independent variables"
    return [col.mid() for col in i.xs]

  def y(i):
    "Return mid values of the dependent variables"
    return [col.mid() for col in i.ys]

  def clone(i, lst=[]):
    "Return a new table with the same structure as this one."
    return Tab([[col.txt for col in i.cols]] + lst)

  def add(i, row):
    """If this is row0, create the headers. Else update the headers with 'row'
    then store the 'row' in 'rows'."""
    if i.cols: i.rows += [[col.add(x) for col, x in zip(i.cols, row)]]
    else: i.cols = [Col.new(i, at, txt) for at, txt in enumerate(row)]

  def like(i, row, my):
    "Report how much this table likes 'row'"
    return i.classify(row, my)[0]

  def classify(i, row, my, tabs=[]):
    """For a set of tables, including this one, find which one mostlikes 'row'.
     Returns a tuple (mostlike,tab)"""
    tabs = [i] + tabs
    n = sum(len(t.rows) for t in tabs)
    mostlike = -1E64
    out = tabs[0]
    for t in tabs:
      prior = (len(t.rows) + my.k) / (n + my.k * len(tabs))
      tmp = math.log(prior)
      for col in i.xs:
        v = row[col.at]
        if v != "?":
          if inc := col.like(v, prior, my):
            tmp += math.log(inc)
      if tmp > mostlike:
        mostlike, out = tmp, t
    return mostlike, out


def coerce(string):
  "If appropriate, coerce `string` into an integer or a float."
  try: return int(string)
  except Exception:
    try: return float(string)
    except Exception: return string


def csv(file=None):
  """From `file` (or standard input) return lists of values from
  comma-separated lines(skipping over whitespace and comments)."""
  def lines(src):
    for lst in src:
      lst = re.sub(r'([\n\t\r ]|#.*)', '', lst)
      if lst: yield [coerce(x) for x in lst.split(",")]
  if file:
    with open(file) as fp:
      for lst in lines(fp): yield lst
  else:
    for lst in lines(sys.stdin): yield lst


def cli(options, doc="", funs=[], eg="eg_"):
  """
  - Drives command-line from `options= `dict(flag=(default, help), ..)`.
  - Command-line values must be of the same type as `default`.
  - Command-line flags must be one `-flag X` (for setting `flag`)
    or `+flag` (for enabling booleans).
  - For a list of functions `funs`, `-do S` will run all functions
    containing `S`, passing in the updated values.  """
  def say():
    if doc: print(doc)
    print("Option          |Notes")
    print("----------------|:-----------------------")
    for k, (v, help) in options.items():
      m = " F " if type(v) == float else (" I " if type(v) == int else " S ")
      print(f" +{k:13}" if v == False else f" -{k+m:13}",
            "|", help, f"; e.g. [{v}]   ")
    print(f" -{'dos':13}", "|", "list everything we can 'do'")
    print(f" -{'h':13}", "|", "show help text")

  def update(prefix, flag, after):
    assert flag in my
    now = True  # for '+' just google the value
    if prefix == "-":
      assert len(after) >= 1
      now = coerce(after[0])
    assert type(now) == type(my[flag])
    my[flag] = now
  # --------------
  funs = {f: v for f, v in funs.items() if type(v) == fun and eg == f[:len(eg)]}
  my = obj(**{k: v for k, (v, _) in options.items()})
  args = sys.argv
  while args:
    arg, *args = args
    if arg == "-h": say()
    elif arg == "-dos": [print(f"{k:>13} : {v.__doc__}")for k, v in funs.items()]
    elif arg[0] in "+-": update(arg[0], arg[1:], args)
  for f, v in funs.items():
    if my.do and my.do in f:
      print("\n### " + f)
      if v.__doc__: print("# " + re.sub(r"\n[\t ]*", "\n# ", v.__doc__))
      random.seed(my.seed)
      v(my)


class Verify:
  def eg_two(my):
    """function with  lots of comments lines"""
    print(my)

  def eg_one(my):
    "table1"
    def r2(x): return round(x, 2)
    t = Tab()
    [t.add(lst) for lst in csv(my.data)]
    t.rows.sort(key=lambda r: t.like(r, my))
    n = 50
    t1 = t.clone(t.rows[: n])
    t2 = t.clone(t.rows[-n:])
    print("lo  ", [r2(col.mid()) for col in t1.xs])
    print("hi  ", [r2(col.mid()) for col in t2.xs])
    print("mid ", [r2(col.mid()) for col in t.xs])


if __name__ == "__main__":
  cli(OPTIONS, __doc__, vars(Verify))
#  def better(i, r1, r2):
#     s1, s2, n = 0, 0, len(i.cols.y)
#     for col in i.cols.y:
#       a, b = r1[col.at], r2[col.at]
#       a, b = col.norm(a), col.norm(b)
#       s1 -= math.e**(at.w*(a-b)/n)
#       s2 -= math.e**(at.w*(b-a)/n)
#     return s1/n < s2/n
#
#   def ordered(i, THE):
#
#
