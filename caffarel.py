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
                  [(  --with=<element>...
                    | --like-run=<id> [ --respect_to=<value>]
                    | --like-sr7
                    | --like-mr13 ) [--with_children]]
                  [--order_by=<column>...]
                  [--ref=<id>]
                  [--plot (gnuplot|plotly|vladimir)]

Options:
  --ref=<id>             Speed in knots [default: 66474780].
  --respect_to=<value>   QSkdsjkdsfj [default: ae].  

"""
#
# |  o |_  ._ _. ._
# |_ | |_) | (_| | \/
#                  /
from lib.docopt import docopt

#                
# |\/|  _. o ._  
# |  | (_| | | | 
#                
if __name__ == '__main__':

    d_arguments = docopt(__doc__)

    from src.calc import BigData
    q = BigData(d_arguments=d_arguments)

    mode = 0
    if d_arguments["e"]:
        mode += 1
    if d_arguments["ae"]:
        mode += 2
    if not mode:
        mode = 3

    if not d_arguments["--plot"]:
      from src.print_util import print_energie_recap
      print_energie_recap(q,order_by=d_arguments["--order_by"],mode=mode)

    if d_arguments["plotly"]:
      from src.print_util import print_plotly
      print_plotly(q)

    elif d_arguments["gnuplot"]:
      from src.print_util import print_table_gnuplot
      print_table_gnuplot(q)

    elif d_arguments["vladimir"]:
      from src.print_util import print_table_vladimir
      print_table_vladimir(q)