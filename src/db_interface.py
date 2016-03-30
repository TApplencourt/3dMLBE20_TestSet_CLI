#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Get data from interface
"""

# ___                      
#  |  ._ _  ._   _  ._ _|_ 
# _|_ | | | |_) (_) |   |_ 
#           |              
import sys
from collections import defaultdict

from src.SQL_util import c, c_row
from src.SQL_util import cond_sql_or

from src.object import Energie

#  _                   _                               
# |_)     ._    o ._ _|_ _  ._ ._ _   _. _|_ o  _  ._  
# | \ |_| | |   | | | | (_) |  | | | (_|  |_ | (_) | | 
#                                                                                                            
def db_run_info(d_arguments,run_id_ref=None):
    """
    Take the docopt dict of arguments on input
    
    """

    d = {"run_id": "--run_id",
         "geo": "--geo",
         "basis": "--basis",
         "method": "--method",
         "comments": "--comments"}

    # If the user give ask for somme run_id return it
    l_cond_filter = []
    

    for k, v in d.items():
        try:
            l_cond_filter += cond_sql_or(k, d_arguments[v])
        except KeyError:
            pass

    l_cond_filter = l_cond_filter if l_cond_filter else ["(1)"]
    sql_cmd_where = " AND ".join(l_cond_filter)

    # -#-#- #
    # S Q L #
    # -#-#- #
    cursor = c_row.execute("""SELECT run_id,
                                     method,
                                     basis,
                                     geo,
                                     comments
                                FROM run_tab_expended
                               WHERE {0}
                           """.format(sql_cmd_where))
    
    d_run_info = dict()
    for r in cursor:
        d_run_info[r['run_id']] = [r['method'], r['basis'],
                                 r['geo'], r['comments']]

    if not d_run_info:
        print "No run_id with:", sql_cmd_where
        sys.exit(1)

    if run_id_ref and run_id_ref not in d_run_info:
        d_run_info[run_id_ref] = None
        print_run_id = False
    else:
        print_run_id = True

    return d_run_info, print_run_id


#
# |  o  _ _|_    _  |  _  ._ _   _  ._ _|_
# |_ | _>  |_   (/_ | (/_ | | | (/_ | | |_
#
def db_formula():
    """
    Input: l_ele

    Return
    d |
    -> key: name
    -> value: the flaten formula (H,H,O) for H2O for exemple.

    All the element need to have a formula!
    """
    d = dict()

    c.execute("""SELECT name, formula
                               FROM ele_tab""")

    d = {name: [a*nb for a,nb in eval(f)] for (name, f) in c.fetchall()}

    return d

def db_list_element(l_run_id): 
    """
    Input
    l_run_id: List of run_id who whant the elements

    Return
    l_ele: List of element who are present in this run_id
    """

    sql_cmd_where = "".join(cond_sql_or("run_id", l_run_id))

    cursor = c_row.execute("""SELECT ele_name
                               FROM  run_tab_ele
                               WHERE {0}
                               """.format(sql_cmd_where))

    l_ele = [i[0] for i in cursor]

    if not l_ele:
        print "No element in run_id:", d_arguments["--like_run_id"]
        sys.exit(1)

    return l_ele

def db_list_element_whe_have(l_ele,l_run_id, d_formula):
    """
    Input: 
    l_ele: list of element who want
    l_run_id: list of run_id who may have this the element

    Return
    d |
    -> key: run_id
    -> value:  List of element whe want who are avalaible for this run_id

    Return a error if the d is empy
    """

    if l_ele != ["*"]:
        try:
            l_ele_tot = l_ele + [a for ele in l_ele for a in d_formula[ele]]
        except KeyError:
            print "We do not know one of the element you wan't", l_ele
            print "Check you're imput"
            sys.exit(1)

        l_ele_tot_uniq = list(set(l_ele_tot))
    else:
        l_ele_tot_uniq = l_ele

    l = cond_sql_or("ele_name",l_ele)
    l += cond_sql_or("run_id", l_run_id)
    sql_cmd_where = " AND ".join(l)

    cursor =  c_row.execute("""SELECT run_id,
                                      ele_name
                               FROM run_tab_ele
                               WHERE {0}
                            """.format(sql_cmd_where))

    d_run_id_ele = defaultdict(list)
    for r in cursor:
        d_run_id_ele[r['run_id']].append(r['ele_name'])

    if not d_run_id_ele:
        print "No run id with:", l_ele
        assert d_run_id_ele

    return d_run_id_ele



#                          _    _                        
# \  / _. |      _     _ _|_   |_ ._   _  ._ _  o  _   _ 
#  \/ (_| | |_| (/_   (_) |    |_ | | (/_ | (_| | (/_ _> 
#                                            _|          
#      

# -#-#-#-#-#-#-#-#-#-#-#- #
# S p i n _ O r b i t a l #
# -#-#-#-#-#-#-#-#-#-#-#- #                                   
def db_so(run_id):
    """
    Input
    l_run_id: Run_id who want to check if a have the spin_orbtial corection

    Return
    d |
    -> key: d[ele]  
    -> value:  Value of the correction (Format Energie)

    Return a error if d is empy
    """

    l = cond_sql_or("run_id", [run_id])
    sql_cmd_where = " ".join(l)

    d = dict()

    cursor = c_row.execute("""SELECT *
                              FROM constant_tab
                             NATURAL JOIN ele_tab
                             WHERE {0}""".format(sql_cmd_where))

    for r in cursor:
        
        so = r["so_energy"]
        so_e = r["so_err"] if r["so_err"] else 0
        d[r["ele_name"]] = Energie(so,so_e)

    if not d:
        print "No spin_orbtial correction for run_id:", run_id
        assert d


    return d


def db_get(d_run_id_ele,table_name):
    """
    Input
    d_run_id_ele |
    -> key: run_id
    -> value:  List of element whe want who are avalaible for this run_id

    Return
    d_run_id_ele |
    -> key: run_id
    -> value: |
         key: ele
         value: Atomisation energy

    Can return a empty dict
    """

    l_run_id = d_run_id_ele.keys()
    l_ele = list(set.union(*map(set, d_run_id_ele.values())))

    l = cond_sql_or("run_id",l_run_id)
    l += cond_sql_or("ele_name",l_ele)
    sql_cmd_where = " AND ".join(l)

    cursor = c_row.execute("""SELECT *
                              FROM {0}
                             WHERE {1}""".format(table_name,sql_cmd_where))

    d = defaultdict(dict)

    for r in cursor:
        
        ae = r["energy"]
        ae_e = r["err"] if r["err"] else 0

        d[r["run_id"]][r["ele_name"]] = Energie(ae,ae_e)

    return d

# -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#- #
# A t o m i s a t i o n _ E n e r g i e #
# -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#- #   
def db_ae(d_run_id_ele):
    """
    Input
    d_run_id_ele |
    -> key: run_id
    -> value:  List of element whe want who are avalaible for this run_id

    Return
    d_run_id_ele |
    -> key: run_id
    -> value: |
         key: ele
         value: Atomisation energy

    Can return a empty dict
    """

    return db_get(d_run_id_ele,"ae_tab")


def db_e(d_run_id_ele):
    """
    Input
    d_run_id_ele |
    -> key: run_id
    -> value:  List of element whe want who are avalaible for this run_id

    Return
    d_run_id_ele |
    -> key: run_id
    -> value: |
         key: ele
         value: Energy

    Can return a empty dict
    """

    return db_get(d_run_id_ele,"e_tab")

