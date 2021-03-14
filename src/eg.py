#!/usr/bin/env python3
# vim: filetype=python ts=2 sw=2 sts=2 et :
#  test suites, command line interface for es.py
from etc import *
from es import *
import es


def eg_one(MY):
  "one example"
  t = Tab(csv(MY.dir + MY.data))
  rows = sorted(t.rows)
  u = t.clone(rows[:100])
  v = t.clone(rows[100:])
  print(u.goals())
  print(v.goals())
  for col1, col2 in zip(u.xs, v.xs):
    print("")
    print(col1.txt)
    for b in col1.discretize(col2, MY):
      print(b, b.also.seen)


def eg_two(MY):
  "one example"
  t = Tab(csv(MY.dir + MY.data))
  best, rest = betterBad(t, MY)
  # or s, rule in Contrast(best, rest, MY).rules:
  # print(f"{s:>6.2f}", canonical(rule))
  for rule in contrast(best, rest, MY):
    print(canonical(t, rule))


main(es.__doc__, es.HELP, eg_s(vars()),
     also=eg_two)
