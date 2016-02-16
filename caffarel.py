#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Get all the List you whant.

Usage:
  caffarel.py (-h | --help)
  caffarel.py get [--e] [--ae]
                  [--run_id=<id>... | ([--method=<method_name>...]
                                       [--basis=<basis_name>...]
                                       [--geo=<geometry_name>...]
                                       [--comments=<comments>...])]
                  [(  --ele=<element_name>...
                    | --like_run_id=<run_id>...
                    | --like-sr7
                    | --like-mr13 ) [--all_children]]
                  [--order_by=<column>...]"""

version = "0.0.1"

#
# |  o |_  ._ _. ._
# |_ | |_) | (_| | \/
#                  /
try:
    from src.docopt import docopt, DocoptExit
except:
    print "File in misc is corupted. Git reset may cure the diseases"
    sys.exit(1)

# ___                      
#  |  ._ _  ._   _  ._ _|_ 
# _|_ | | | |_) (_) |   |_ 
#           |              

from src.db_interface import db_run_info
from src.db_interface import db_list_element
from src.db_interface import db_list_element_whe_have
from src.db_interface import db_formula
from src.db_interface import db_ae, db_e

from src.combination import calc_deviation
from src.combination import calc_mad
from src.combination import calc_atomisation
from src.combination import merge_two_dicts


def get_list_element_whe_want(d_arguments):
    """
    Input
    d_arguments: docot dict of arguments
    
    Return
    l_ele:  list of element who satisfy the condition
    If we need to get all the element, l_ele = "*"
    """

    if d_arguments["--ele"]:
        l_ele = d_arguments["--ele"]
    elif d_arguments["--like-sr7"]:
        l_ele = ["MnCl","ZnCl","FeCl","CrCl","ZnS","ZnH","CuCl"]
    elif d_arguments["--like-mr13"]:
        l_ele = ["ZnO","NiCl","TiCl","CuH","VO","VCl","MnS","CrO","CoH","CoCl","VH","FeH","CrH"]
    elif d_arguments["--like_run_id"]:
        l_ele = db_list_element(d_arguments["--like_run_id"])
    else:
        l_ele = ["*"]

    return l_ele


if __name__ == '__main__':
    
    d_arguments = docopt(__doc__, version='G2 Api ' + version)

    d_formula = db_formula()

    run_id_ref = 1
    d_run_info, print_run_id = db_run_info(d_arguments,run_id_ref)

    l_ele = get_list_element_whe_want(d_arguments)
    d_run_id_ele = db_list_element_whe_have(l_ele, d_run_info, d_formula)

    if l_ele == ["*"]:
        l_ele_tot = list(set.union(*map(set, d_run_id_ele.values())))
    else:
        l_ele_tot = l_ele
  
    d_e = db_e(d_run_id_ele)


    mode = 0
    if d_arguments["--e"]:
        mode += 1
    if d_arguments["--ae"]:
        mode += 2

    if not mode:
        mode = 3

    if mode==2 or mode==3:

        d_ae_calc = calc_atomisation(d_e,d_formula)
        d_ae_db = db_ae(d_run_id_ele)
        d_ae = merge_two_dicts(d_ae_calc,d_ae_db)

        d_deviation = calc_deviation(d_ae,run_id_ref)
    else:
        d_ae = {}
        d_deviation = {}

    from src.print_util import print_energie_recap
    print_energie_recap(d_run_info,
                        run_id_ref,
                        print_run_id,
                        l_ele_tot,
                        d_e,
                        d_ae,
                        d_deviation, order_by=d_arguments["--order_by"],mode=mode)