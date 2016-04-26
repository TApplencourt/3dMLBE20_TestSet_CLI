#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Get all the List you whant.

Usage:
  schindler.py (-h | --help)
  schindler.py list_run [--run=<id>... | ([--method=<method_name>...]
                                    [--basis=<basis_name>...]
                                    [--geo=<geometry_name>...]
                                    [--comments=<comments>...])]
                         [(  --with=<element>...
                           | --like-run=<id> [ --respect_to=<value>]
                           | --like-sr7
                           | --like-mr13 ) [--with_children]]
                           [--order_by=<column>...]
                           [--ref=<id>]

Options:
  --ref=<id>    Id of reference for the run [default: 66474780].

"""
#
# |  o |_  ._ _. ._
# |_ | |_) | (_| | \/
#                  /
from lib.docopt import docopt
from src.calc import BigData
from src.print_util import print_mad_recap

#                
# |\/|  _. o ._  
# |  | (_| | | | 
#                
if __name__ == '__main__':
    
    d_arguments = docopt(__doc__)
    q = BigData(d_arguments=d_arguments)


    if d_arguments["--order_by"]:
      order_by = d_arguments["--order_by"]
    else:
      order_by = ["mad"]

    print_mad_recap(q,order_by=order_by)
