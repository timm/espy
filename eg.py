#!/usr/bin/env python3
# vim: filetype=python ts=2 sw=2 sts=2 et :
#  test suites, command line interface for es.py
from etc import *
from es import *
import es


def eg_one(THE):
  "one example"
  t = Tab(csv(THE.dir + THE.data))
  rows = sorted(t.rows)
  u = t.clone(rows[:100])
  v = t.clone(rows[100:])
  print(u.goals())
  print(v.goals())
  for col1, col2 in zip(u.xs, v.xs):
    print("")
    print(col1.txt)
    for b in col1.discretize(col2, THE):
      print(b, b.also.seen)


def eg_two(THE):
  "one example"
  t = Tab(csv(THE.dir + THE.data))
  best, rest = betterBad(t, THE)
  for s, rule in Contrast(best, rest, THE).rules:
    print(f"{s:>6.2f}", canonical(rule))


main(es.__doc__, es.HELP, eg_s(vars()),
     also=eg_two)
