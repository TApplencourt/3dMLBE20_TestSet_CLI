#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  _
# /   _  | |  _   _ _|_ o  _  ._
# \_ (_) | | (/_ (_  |_ | (_) | |
#
from collections import defaultdict

from src.Requirement_util import config

import sys

# Format dict
d_format = defaultdict(lambda: '{0}')
for name, value in config.items("Format_dict"):
    d_format[name] = config.get("Format_mesure", value)


DEFAULT_CHARACTER = ""

from src.terminaltables import AsciiTable


#  _
# |_ _  ._ ._ _   _. _|_
# | (_) |  | | | (_|  |_
#
def format_table(l_header, table_body):
    """
    For all value in all ligne, format the table
    """

    table_formated = [[d_format[h].format(v) for h, v in zip(l_header,l)] 
                      for l in table_body]

    return table_formated


#  _
# / \ ._ _|  _  ._   |_
# \_/ | (_| (/_ |    |_) \/
#                        /
def order(list_order, header_name, table_body):
    """
    List_order is the list of ordonancement you wan't to try
    """

    def formatkey(value):
        try:
            return abs(value)
        except TypeError:
            return value

    for arg in list_order:
        try:
            index = header_name.index(arg)
        except ValueError:
            print "Error. Cannot order_by {0}".format(list_order)
            print "Choose in:", header_name
            sys.exit(1)
        else:
            table_body = sorted(table_body,
                                key=lambda x: formatkey(x[index]),
                                reverse=True)
    return table_body


#  _
# |_) ._ o ._ _|_   ._ _   _.  _|
# |   |  | | | |_   | | | (_| (_|
#
def print_mad_recap(run_id_ref, run_info, d_mad, order_by):
    """
    Create the table then print the mad
    """
    # -#-#-#- #
    # I n i t #
    # -#-#-#- #

    table_body = []

    # -#-#-#-#-#- #
    # H e a d e r #
    # -#-#-#-#-#- #

    header_name = "Run_id Method Basis Geo Comments mad".split()
    header_unit = [DEFAULT_CHARACTER] * 5 + ["kcal/mol"]

    # -#-#-#- #
    # B o d y #
    # -#-#-#- #

    #Add the reference
    line=["{0}*".format(run_id_ref)] + run_info[run_id_ref] + [0.]
    table_body.append(line)

    #Now add the real mad
    for run_id, mad in d_mad.iteritems():
        l = run_info[run_id]
        line = [run_id] + l + [mad]
        table_body.append(line)

    # -#-#-#-#-#- #
    # F o r m a t #
    # -#-#-#-#-#- #

    table_body = order(order_by, header_name, table_body)
    table_body = format_table(header_name, table_body)

    # -#-#-#-#-#-#-#- #
    # B i g  Ta b l e #
    # -#-#-#-#-#-#-#- #

    table_body = [map(str, i) for i in table_body]
    table_data = [header_name] + [header_unit] + table_body

    table_big = AsciiTable(table_data)
    print table_big.table(row_separator=2)


def print_energie_recap(d_run_info,run_id_ref,print_run_id_ref,
                        l_ele,d_e,d_ae,d_deviation, order_by,mode):

    # -#-#-#- #
    # I n i t #
    # -#-#-#- #

    # 1 : only energy
    # 2 : only ae
    # 3 : all

    # -#-#-#-#-#- #
    # H e a d e r #
    # -#-#-#-#-#- #

    header_name = "Run_id Method Basis Geo Comments ele ".split()
    header_unit = [DEFAULT_CHARACTER] * 6 


    # -#- #
    # A E #
    # -#- #
    if mode == 1 or mode == 3:
        header_name += "e".split()
    if mode == 2 or mode == 3:
        header_name += "ae ae_ref ae_diff".split()


    # -#-#-#-#- #
    # M E R G E #
    # -#-#-#-#- #

    from collections import namedtuple
    E_ae = namedtuple("e_ae",['e','ae'])
    E_ae.__new__.__defaults__ = (None,) * len(E_ae._fields)

    dd = defaultdict(dict)

    for run_id ,d in d_e.iteritems():
        for ele,e in d.iteritems():
            dd[run_id][ele] = E_ae(e=e,ae=None)


    for run_id ,d in d_ae.iteritems():
        for ele,ae in d.iteritems():

            try:
                e = dd[run_id][ele].e
                dd[run_id][ele] = E_ae(e,ae)
            except KeyError:
                dd[run_id][ele] =E_ae(e=None,ae=ae)

    # -#-#-#- #
    # B o d y #
    # -#-#-#- #
    table_body = []

    for run_id, d in dd.items():
        for ele, e_ae in d.items():


            if ele in l_ele:

                l = []

                if e_ae.e and (mode==1 or mode==3):
                    l.append(e_ae.e)
                else:
                    if mode == 3:
                        l.append("")

                if e_ae.ae and (mode==2 or mode==3):
                    l.append(e_ae.ae)
                    l.append(d_ae[run_id_ref][ele])
                    try:
                        l.append(d_deviation[run_id][ele])
                    except:
                        pass
                else:
                    if mode == 3:
                        l.extend([""]*3)

                if l:
                    if run_id != run_id_ref or print_run_id_ref:
                            l =  [run_id] + d_run_info[run_id]+[ele] + l
                            table_body.append(l)


    # -#-#-#-#-#- #
    # F o r m a t #
    # -#-#-#-#-#- #

    table_body = order(order_by, header_name, table_body)
    table_body = format_table(header_name, table_body)

    # -#-#-#-#-#-#-#- #
    # B i g  Ta b l e #
    # -#-#-#-#-#-#-#- #

    table_body = [map(str, i) for i in table_body]
    table_data = [header_name] + [header_unit] + table_body

    table_big = AsciiTable(table_data)
    print table_big.table(row_separator=2)