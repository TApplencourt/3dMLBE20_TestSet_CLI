#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Welcome to the G2 Api! Grab all the G2 data you're dreaming of.

Usage:
  scemama.py (-h | --help)
  scemama.py list_geometries  [--ele=<element_name>...]
  scemama.py list_elements    (--geo=<geometry_name>... | --run=<id>...)
  scemama.py get_multiplicity  --ele=<element_name>...
  scemama.py get_xyz    --geo=<geometry_name>...
                        --ele=<element_name>...
                            [(--save [--path=<path>])]
  scemama.py get_g09    --geo=<geometry_name>...
                        --ele=<element_name>...
                              [(--save [--path=<path>])]
  scemama.py get_target_pt2_max --hf=<id>
                                --target=<id>
                                [--quality_factor=<qf>]

Options:
  --ref=<id>               Speed in knots [default: 1].
  --quality_factor=<vqf>   QSkdsjkdsfj [default: 0].  

Example of use:
  ./scemama.py list_geometries
  ./scemama.py list_elements --geo Experiment
  ./scemama.py get_xyz --geo Experiment --ele FeCl --ele MnCl
"""

version = "0.0.1"

import sys

from lib.docopt import docopt

from src.__init__ import cond_sql_or
from src.__init__ import get_formula

from src.SQL_util import c, c_row
from src.SQL_util import list_geo, list_ele, get_coord




# ______ _      _
# |  _  (_)    | |
# | | | |_  ___| |_
# | | | | |/ __| __|
# | |/ /| | (__| |_
# |___/ |_|\___|\__|
#

from collections import defaultdict

def get_dict_element():
    c.execute('''SELECT id,name,charge,multiplicity,
                        num_atoms,num_elec,symmetry FROM ele_tab''')

    d = defaultdict(dict)

    for i in c.fetchall():
        d[str(i[1])] = {"id": str(i[0]),
                        "charge": int(i[2]),
                        "multiplicity": int(i[3]),
                        "num_atoms": int(i[4]),
                        "symmetry": str(i[6])}

    for ele in d:
            f = get_formula(ele)
            d[ele]["formula"] = f

            for geo in list_geo():

                l = [get_coord(ele, a, geo) for a in f]
                d[ele][geo] = l

    return d

# ______                         _
# |  ___|                       | |
# | |_ ___  _ __ _ __ ___   __ _| |_
# |  _/ _ \| '__| '_ ` _ \ / _` | __|
# | || (_) | |  | | | | | | (_| | |_
# \_| \___/|_|  |_| |_| |_|\__,_|\__|
#
def get_multiplicity(ele):
    d = get_dict_element()
    d_ele = d[ele]

    assert d_ele, "No multiplicity for ele {0}".format(ele)
    return d_ele["multiplicity"]

def get_xyz(geo, ele):
    d = get_dict_element()

    d_ele = d[ele]

    xyz_file_format = [d_ele["num_atoms"]]

    str_ = "{0} Geo: {1} Mult: {2} Symmetry: {3}"
    line = str_.format(ele,geo,d_ele["multiplicity"],d_ele["symmetry"])

    xyz_file_format.append(line)

    for atom, xyz in zip(d_ele["formula"], d_ele[geo]):
        line_xyz = "    ".join(map(str, xyz))
        line = "{0}    {1}".format(atom, line_xyz)

        xyz_file_format.append(line)

    return "\n".join(map(str, xyz_file_format))


def get_g09(geo, ele):
    d = get_dict_element()

    d_ele = d[ele]

    str_ = "{0} Geo: {1} Mult: {2} Symmetry: {3}"
    line = str_.format(ele,geo,d_ele["multiplicity"],d_ele["symmetry"])

    method = "RHF" if d_ele["multiplicity"] == 1 else "ROHF"

    g09_file_format = ["# cc-pvdz {0}".format(method), 
                        "", line, "",
                       "{0} {1}".format(d_ele["charge"], d_ele["multiplicity"])]

    for atom, xyz in zip(d_ele["formula_flat"], d_ele[geo]):
        line_xyz = "    ".join(map(str, xyz)).replace("e", ".e")
        line = "    ".join([atom, line_xyz])

        g09_file_format.append(line)
    g09_file_format.append("\n\n\n")

    return "\n".join(map(str, g09_file_format))

if __name__ == '__main__':

    arguments = docopt(__doc__, version='G2 Api ' + version)

    if arguments["list_geometries"]:

        if arguments["--ele"]:
            cond = cond_sql_or("ele_tab.name", arguments["--ele"])
            where = "AND".join(cond)
        else:
            where = '(1)'

        r = list_geo(where_cond=where)
        assert r, "No geometries for {0} elements".format(arguments["--ele"])
        print(", ".join(r))

    elif arguments["list_elements"]:

        if arguments['--geo']:
    
            cond = cond_sql_or("geo_tab.name", arguments["--geo"])
            where = "AND".join(str_)
    
            r = list_ele(where_cond=where)
            assert r, "No element for {0} geometries".format(arguments["--geo"])
    
            print(", ".join(r))
        elif arguments['--run']:

            from src.calc import BigData
            q = BigData(d_arguments=arguments)
            print(", ".join(q.l_element))

    elif arguments["get_multiplicity"]:
        l_ele = arguments["--ele"]
        l = [str(get_multiplicity(ele)) for ele in l_ele]

        print(" ".join(l))

    elif arguments["get_g09"] or arguments["get_xyz"]:

        from collections import namedtuple

        get_general = namedtuple('get_general', ['get', 'ext'])

        if arguments['get_g09']:
            g = get_general(get=get_g09, ext='com')
        elif arguments['get_xyz']:
            g = get_general(get=get_xyz, ext='xyz')

        l_geo = arguments["--geo"]
        l_ele = arguments["--ele"]

        to_print = []
        for ele in l_ele:
            for geo in l_geo:
                try:
                    xyz = g.get(geo, ele)
                except KeyError:
                    pass
                else:
                    to_print.append(xyz)

        str_ = "\n\n".join(to_print)

        import os

        if arguments["--save"]:

            if arguments["--path"]:
                path = arguments["--path"]
            else:
                name = "{0}.{1}".format("_".join(l_geo+l_ele),g.ext)
                path = os.path.join("/tmp/",name)

            print(path)
            with open(path, 'w') as f:
                f.write(str_ + "\n")

        else:
            print(str_)

    elif arguments["get_target_pt2_max"]:

        hf_id = int(arguments["--hf"])
        fci_id = int(arguments["--target"])

        arguments["--run"]=[hf_id,fci_id]

        from src.calc import BigData
        q = BigData(d_arguments=arguments)

        from src.__init__ import get_formula


        # -#-#-#-#-#-#-#-#-#-#-#- #
        # D _ t a r g e t _ p t 2 #
        # -#-#-#-#-#-#-#-#-#-#-#- #

        from collections import defaultdict
        d_target_pt2 = defaultdict(lambda: 0.)

        for ele in q.l_element:
            try:
                for name_atome in get_formula(ele):
                    dump = (q.d_e[fci_id][name_atome] - q.d_e[hf_id][name_atome])
                    d_target_pt2[ele] += dump
            except KeyError:
                pass

        # -#-#-#-#-#-#-#-#-#-#-#-#-#- #
        # Q u a l i t y _ f a c t o r #
        # -#-#-#-#-#-#-#-#-#-#-#-#-#- #

        if arguments["--quality_factor"]:
            if not 0. <= float(arguments["--quality_factor"]) <= 1.:
                print("0. < quality factor < 1. ")
                sys.exit(1)
            else:
                quality_factor = float(arguments["--quality_factor"])
        else:
            quality_factor = 0.

        #  _
        # |_) ._ o ._ _|_
        # |   |  | | | |_
        #
        print("{0:<7} {1:<8} {2:>15}  quality_factor: {3}".format("Ele","Target_PT2","Target_Energie",quality_factor))
        str_ = "{0:<7} {1:<8.4f} {2:>17.4f}"

        for ele, target_pt2 in d_target_pt2.items():
            ept2 = target_pt2 * (1 - quality_factor)
            efci = q.d_e[fci_id][ele]
            print(str_.format(ele, ept2, efci-ept2))