#!/usr/bin/env python3
# vim: filetype=python ts=2 sw=2 sts=2 et :
from es import *

def main():
  the = A(**cli(HELP))
  return True
  t=Tab(csv("auto93.csv"))
  rows = sorted(t.rows)
  u=t.clone(rows[:100])
  v=t.clone(rows[100:])
  for col1,col2 in zip(u.xs,v.xs):
    print("")
    print(col1.txt)
    for b in col1.discretize(col2,the):
      print(b)

main()
