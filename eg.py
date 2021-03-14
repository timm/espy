#!/usr/bin/env python3
# vim: filetype=python ts=2 sw=2 sts=2 et :
# Support code, test suites, command line interface for es.py
import random, sys, es
from types import FunctionType as fun
from es import *

def eg_one(THE):
  "one example"
  t=Tab(csv(THE.dir + THE.data))
  rows = sorted(t.rows)
  u=t.clone(rows[:100])
  v=t.clone(rows[100:])
  print(u.goals())
  print(v.goals())
  for col1,col2 in zip(u.xs,v.xs):
    print("")
    print(col1.txt)
    for b in col1.discretize(col2,THE):
      print(b, b.also.seen)

def eg_two(THE):
  "one example"
  t = Tab(csv(THE.dir + THE.data))
  best,rest = betterBad(t,THE)
  for rule in Contrast(best,rest,THE).rules: print(rule)
  print("")
  for rule in Contrast(rest,best,THE).rules: print(rule)

def eg(k,f,THE):
  random.seed(THE.seed)
  print(flair(HEADER= ("# " + k + " : " + (f.__doc__ or ""))))
  try: f(THE)
  except Exception: ok(False, "function ran?")
  return f

def ok(x, txt=""):
  if x: print("\t" + txt + flair(OKGREEN=" PASS"))
  else: print("\t" + txt + flair(FAIL   =" FAIL"))

def flair(**d):
  c = dict(
    HEADER  = '\033[95m', OKBLUE  = '\033[94m', OKCYAN    = '\033[96m',
    OKGREEN = '\033[92m', WARNING = '\033[93m', FAIL      = '\033[91m',
    ENDC    = '\033[0m',  BOLD    = '\033[1m',  UNDERLINE = '\033[4m')
  for k,v in d.items():
    return c[k] + c["BOLD"] + str(v) + c["ENDC"]

def help_txt(doc,xpect):
  print(flair(OKCYAN=doc))
  print(f" -{'h':12} show help   ")
  print(f" -{'egs':12} run all examples   ")
  print(f" -{'eg S':12} run examples matching 'S'  ")
  print(f" -{'ls':12} list all examples   ")
  for k,(v,help) in xpect.items():
    m = ("  " if v==False       else (
         " I" if type(v)==int   else (
         " F" if type(v)==float else (
         " S"))))
    print(f" +{k:12} {help}   " if v==False else f" -{k+m:12} {help}  ")

def cli(doc,xpect,funs=[]):
  """Takes a dictionary (k1:(default1,help1))+, valid cli keys are one of the 
  `default` symbols and `-h` shows the `help` text. Also, new arguments to
  those flags need to be same type as `default1`."""
  want = {k:v for k,(v,_) in xpect.items()} # all the key, defaults
  elp  = lambda k,v: print(f"{k[3:]:>15} :",v.__doc__) 
  got, args, out = {}, sys.argv, {k:want[k] for k in want}
  do = []
  while args:
    arg,*args = args
    mark = arg[0]
    if mark in "+-":
      flag = arg[1:]
      if   flag=="h"  : help_txt(doc, xpect)
      elif flag=="ls" : [elp(k,funs[k]) for k in funs      if k[:3]=="eg_"]
      elif flag=="egs": do= [(k,v) for k,v in funs.items() if k[:3]=="eg_"]
      elif not args   : print(f"W: missing argument for {flag}")
      elif flag=="eg" : do= [(k,funs[k]) for k in funs     if k[:3]=="eg_" and args[0] in k]
      elif flag not in want: print(f"W: ignoring {flag} (not defined)")
      else:                 
        old,new = want[flag],args[0]
        try: out[flag] = (float(new) if type(old) == float else (
                          int(new)   if type(old) == int   else (
                          new)))
        except Exception: print(f"W: {new} not of type {type(old).__name__}")
  out["_do"] = do
  return out

def main(funs):
  funs ={k:v for k,v in funs.items() if type(v) == fun}
  the  = obj(**cli(es.__doc__, es.HELP, funs))
  #[eg(k,v,the) for k,v in the._do]
  eg_two(the)

main(vars())
