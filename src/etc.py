#!/usr/bin/env python3
# vim: filetype=python ts=2 sw=2 sts=2 et :
# misc python code.
import random
import sys
import re
from types import FunctionType as fun


class obj:
  def __init__(i, **d): i.__dict__.update(d)

  def __repr__(i):
    lst = sorted(i.__dict__.items())
    return "{" + ', '.join([f":{k} {v}" for k, v in lst if k[0] != "_"])+"}"


def csv(file):
  with open(file) as fp:
    for line in fp:
      line = re.sub(r'([\n\t\r ]|#.*)', '', line)
      if line:
        yield line.split(",")


def printm(matrix):
  s = [[str(e) for e in row] for row in matrix]
  lens = [max(map(len, col)) for col in zip(*s)]
  fmt = ' | '.join('{{:>{}}}'.format(x) for x in lens)
  for row in [fmt.format(*row) for row in s]:
    print(row)


def subsets(l):
  out = [[]]
  for x in l:
    out += [sub + [x] for sub in out]
  return out[1:]


def eg(k, f, MY):
  random.seed(MY.seed)
  print(flair(HEADER=("# " + k + " : " + (f.__doc__ or ""))))
  try:
    f(MY)
  except Exception:
    ok(False, "function ran?")
  return f


def ok(x, txt=""):
  if x:
    print("\t" + txt + flair(OKGREEN=" PASS"))
  else:
    print("\t" + txt + flair(FAIL=" FAIL"))


def flair(**d):
  c = dict(
      HEADER='\033[95m', OKBLUE='\033[94m', OKCYAN='\033[96m',
      OKGREEN='\033[92m', WARNING='\033[93m', FAIL='\033[91m',
      ENDC='\033[0m',  BOLD='\033[1m',  UNDERLINE='\033[4m')
  for k, v in d.items():
    return c[k] + c["BOLD"] + str(v) + c["ENDC"]


def help_txt(doc, xpect):
  print(flair(OKCYAN=doc))
  print(f" -{'h':12} show help   ")
  print(f" -{'egs':12} run all examples   ")
  print(f" -{'eg S':12} run examples matching 'S'  ")
  print(f" -{'ls':12} list all examples   ")
  for k, (v, help) in xpect.items():
    m = ("  " if v == False else (
         " I" if type(v) == int else (
             " F" if type(v) == float else (
                 " S"))))
    print(f" +{k:12} {help}   " if v == False else f" -{k+m:12} {help}  ")


def cli(doc, xpect, funs=[]):
  """Takes a dictionary (k1:(default1,help1))+, valid cli keys are one of the 
  `default` symbols and `-h` shows the `help` text. Also, new arguments to
  those flags need to be same type as `default1`."""
  want = {k: v for k, (v, _) in xpect.items()}  # all the key, defaults
  def elp(k, v): return print(f"{k[3:]:>15} :", v.__doc__)
  got, args, out = {}, sys.argv, {k: want[k] for k in want}
  do = []
  while args:
    arg, *args = args
    mark = arg[0]
    if mark in "+-":
      flag = arg[1:]
      if flag == "h":
        help_txt(doc, xpect)
      elif flag == "ls":
        [elp(k, funs[k]) for k in funs]
      elif flag == "egs":
        do = [(k, v) for k, v in funs.items()]
      elif not args:
        print(f"W: missing argument for {flag}")
      elif flag == "eg":
        do = [(k, funs[k]) for k in funs if args[0] in k]
      elif flag not in want:
        print(f"W: ignoring {flag} (not defined)")
      else:
        old, new = want[flag], args[0]
        try:
          out[flag] = (float(new) if type(old) == float else (
              int(new) if type(old) == int else (
                  new)))
        except Exception:
          print(f"W: {new} not of type {type(old).__name__}")
  out["_do"] = do
  return out


def eg_s(l): return {k: v for k, v in l.items()
                     if type(v) == fun and k[:3] == "eg_"}


def main(doc, help, funs, also=None):
  my = obj(**cli(doc, help, funs))
  also(my) if also else [eg(k, v, my) for k, v in my._do]
