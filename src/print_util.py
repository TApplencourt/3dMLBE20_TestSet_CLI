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
    d_format[name] = value


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
def print_mad_recap(q, order_by="run_id"):
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


    l_fields = "run_id method basis geo comments".split()

    header_name = l_fields + ["mad"]
    header_unit = [DEFAULT_CHARACTER] * len(l_fields) + ["kcal/mol"]

    # -#-#-#- #
    # B o d y #
    # -#-#-#- #

    #Now add the real mad
    for run_id, mad in q.d_mad.iteritems():

        l_info = q.d_run_info[run_id]

        line = [getattr(l_info, field) for field in l_fields] + [mad]
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


def print_energie_recap(q, order_by="run_id",mode=3):

    # -#-#-#- #
    # I n i t #
    # -#-#-#- #

    # 1 : only energy
    # 2 : only ae
    # 3 : all

    # -#-#-#-#-#- #
    # H e a d e r #
    # -#-#-#-#-#- #

    l_fields = "run_id method basis geo comments".split()

    header_name = l_fields + ["ele"]
    header_unit = [DEFAULT_CHARACTER] * (len(l_fields)+1)

    # -#- #
    # A E #
    # -#- #
    if mode == 1 or mode == 3:
        header_name += "e".split()
    if mode == 2 or mode == 3:
        header_name += "ae ae_ref ae_diff".split()

    table_body = []
    for run_id in q.l_run_id:

        l_info = q.d_run_info[run_id]
        line = [getattr(l_info, field) for field in l_fields]

        if mode == 1 or mode==3:
            d_e = q.d_e[run_id]
        
        if mode == 2 or mode == 3:
            d_ae = q.d_ae[run_id]
            d_ae_ref = q.d_ae_ref
            d_ae_deviation = q.d_ae_deviation[run_id]

        if mode == 1:
            l = d_e.keys()
        elif mode == 2:
            l = d_ae.keys()
        elif mode == 3:
            l = set(d_e.keys()) | set(d_ae.keys())

        for ele in l:

            sentinel = False

            line_value = []
            if mode == 1 or mode==3:
                if ele in d_e:
                    line_value.append(d_e[ele])
                    sentinel = True
                else:
                    line_value.append("")

            if mode == 2 or mode == 3:
                if ele in d_ae:
                    line_value.append(d_ae[ele])
                    sentinel = True
                else:
                    line_value.append("")


                if ele in d_ae_ref:
                    line_value.append(d_ae_ref[ele])
                else:
                    line_value.append("")

                if ele in d_ae_deviation:
                    line_value.append(d_ae_deviation[ele])
                else:
                    line_value.append(""*3)

            if sentinel:
                table_body.append(line+[ele]+line_value)

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