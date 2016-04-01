#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Get all the List you whant.

Usage:
  caffarel.py (-h | --help)
  caffarel.py get [e] [ae]
                  [--run=<id>... | ([--method=<method_name>...]
                                    [--basis=<basis_name>...]
                                    [--geo=<geometry_name>...]
                                    [--comments=<comments>...])]
                  [(  --ele=<element_name>...
                    | --like_run_id=<run_id>...
                    | --like-sr7
                    | --like-mr13 ) [--with_children]]
                  [--order_by=<column>...]
                  [--ref=<id>]

Options:
  --ref=<id>    Speed in knots [default: 1].

"""

version = "0.0.1"

#
# |  o |_  ._ _. ._
# |_ | |_) | (_| | \/
#                  /
try:
    from src.docopt import docopt
except:
    print "File in misc is corupted. Git reset may cure the diseases"
    sys.exit(1)

if __name__ == '__main__':

    d_arguments = docopt(__doc__, version='G2 Api ' + version)
    
    from src.calc import BigData
    run_id_ref=int(d_arguments["--ref"])
    q = BigData(d_arguments=d_arguments,run_id_ref=run_id_ref)

    mode = 0
    if d_arguments["e"]:
        mode += 1
    if d_arguments["ae"]:
        mode += 2
    if not mode:
        mode = 3

    from src.print_util import print_energie_recap
    print_energie_recap(q,order_by=d_arguments["--order_by"],mode=mode)