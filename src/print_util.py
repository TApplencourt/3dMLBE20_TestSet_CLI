#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  _
# /   _  | |  _   _ _|_ o  _  ._
# \_ (_) | | (/_ (_  |_ | (_) | |
#
from collections import defaultdict
from src.__init__ import config
from lib.terminaltables import AsciiTable

import sys

# Format dict
D_FORMAT = defaultdict(lambda: '{0}')
for name, value in config.items("Format_dict"):
    D_FORMAT[name] = value

L_FIELD = config.items("Display")[0][1].split()

DEFAULT_CHARACTER = ""




#  _
# |_ _  ._ ._ _   _. _|_
# | (_) |  | | | (_|  |_
#
def format_table(l_header, table_body):
    """
    For all value in all ligne, format the table
    """

    table_formated = [[D_FORMAT[h].format(v) if v else DEFAULT_CHARACTER
                       for h, v in zip(l_header, l)] for l in table_body]

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
def print_mad_recap(q, order_by=["run_id"]):
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

    header_name = L_FIELD + ["mad", "rmsad"]
    header_unit = [DEFAULT_CHARACTER] * len(L_FIELD) + ["kcal/mol", "kcal/mol"]

    # -#-#-#- #
    # B o d y #
    # -#-#-#- #

    #Now add the real mad
    for run_id, l_info in q.d_run_info.iteritems():

        try:
            mad = q.d_mad[run_id]
            rmsad = q.d_rmsad[run_id]
        except KeyError:
            mad = 0.
            rmsad = 0.

        line = [getattr(l_info, field) for field in L_FIELD] + [mad, rmsad]
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


def print_energie_recap(q, order_by=["run_id"], mode=3):

    # -#-#-#- #
    # I n i t #
    # -#-#-#- #

    # 1 : only energy
    # 2 : only ae
    # 3 : all

    # -#-#-#-#-#- #
    # H e a d e r #
    # -#-#-#-#-#- #

    header_name = L_FIELD + ["ele"]
    header_unit = [DEFAULT_CHARACTER] * (len(L_FIELD) + 1)

    # -#- #
    # A E #
    # -#- #
    if mode == 1 or mode == 3:
        header_name += "e".split()
        header_unit += ["hartree"]
    if mode == 2 or mode == 3:
        header_name += "ae ae_ref ae_diff".split()
        header_unit += ["kcal/mol"] * 3

    table_body = []
    for run_id in q.l_run_id:

        l_info = q.d_run_info[run_id]
        line = [getattr(l_info, field) for field in L_FIELD]

        if mode in [1, 3]:
            d_e = q.d_e[run_id]

        if mode in [2, 3]:
            d_ae = q.d_ae[run_id]
            d_ae_ref = q.d_ae_ref
            d_ae_deviation = q.d_ae_deviation[run_id]

        for ele in q.l_element:

            sentinel = False

            line_value = []

            if mode in [1, 3]:

                if ele in d_e:
                    line_value.append(d_e[ele])
                    sentinel = True
                else:
                    line_value.append(None)

            if mode in [2, 3]:

                if ele in d_ae:
                    line_value.append(d_ae[ele])
                    sentinel = True
                else:
                    line_value.append(None)

                if ele in d_ae_ref:
                    line_value.append(d_ae_ref[ele])
                else:
                    line_value.append(None)

                if ele in d_ae_deviation:
                    line_value.append(d_ae_deviation[ele])
                else:
                    line_value.append(None)

            if sentinel:
                table_body.append(line + [ele] + line_value)

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

    mode = config.get("Size", "mode")

    table_big = AsciiTable(table_data)

    if all([mode == "Auto", not table_big.ok]) or mode == "Small":

        table_data_top = []
        for i in table_data:
            l = i[:len(L_FIELD)]
            if l not in table_data_top: table_data_top.append(l)

        table_data_botom = [i[0:1] + i[len(L_FIELD):] for i in table_data]

        table_big = AsciiTable(table_data_top)
        print table_big.table(row_separator=2)

        table_big = AsciiTable(table_data_botom)
        print table_big.table(row_separator=2)

    else:
        print table_big.table(row_separator=2)


def print_plotly(q):

    try:
        import plotly.plotly as py
        from plotly.graph_objs import Layout, ErrorY, XAxis, YAxis, Legend, Scatter, Figure
    except:
        print "You need plotly"
        print "http://plot.ly/python/getting-started"
        sys.exit(1)

    data = []
    for run_id, d in q.d_ae_deviation.iteritems():

        x = []
        y = []
        ye = []
        for e, v in sorted(d.iteritems()):
            x.append(e)
            y.append(v.e)
            ye.append(v.err)

        name = q.d_run_info[run_id]
        a = Scatter(name=name,
                    x=x,
                    y=y,
                    error_y=dict(type='data',
                                 array=ye,
                                 visible=True),
                    mode='lines+markers')

        data.append(a)

    layout = Layout(yaxis=YAxis(title='$\Delta AE~(kcal/mol)$'),
                    showlegend=True,
                    legend=Legend(x=0.,
                                  y=100))

    fig = Figure(data=data, layout=layout)
    py.image.save_as(fig, filename='AE_diff.png')
    print "You png file is save at AE_diff.png"
    py.plot(fig, filename='AE_diff')


def print_table_gnuplot(q):

    for run_id, d in q.d_ae_deviation.iteritems():

        l_info = q.d_run_info[run_id]

        a = [getattr(l_info, field) for field in L_FIELD]
        print ".".join(map(str, a))
        for e, v in sorted(d.iteritems()):
            print "{0:<10}  {1}  {2}".format(e, v.e, v.err)

        print "\n\n"

    print "#plot for [IDX=0:1] 'data.dat' i IDX u 2:xticlabel(1)  w lp title columnheader(1)"
