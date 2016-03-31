#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

try:
    import sqlite3
    from sqlit import connect4git
except:
    print "Sorry, you need sqlite3"
    sys.exit(1)

from src.__init__ import get_formula
from src.__init__ import cond_sql_or
#  _
# /  ._ _   _. _|_  _     _     ._ _  _  ._
# \_ | (/_ (_|  |_ (/_   (_ |_| | _> (_) |
#

dump_path = os.path.abspath(os.path.dirname(__file__) + "/../db/3dMLBE20.dump")
db_path = os.path.abspath(os.path.dirname(__file__) + "/../db/3dMLBE20.db")

try:
    conn = connect4git(dump_path, db_path)
except sqlite3.Error as e:
    print "{0} is not a SQLite3 database file".fomat(db_path)
    sys.exit(1)

c = conn.cursor()

conn.row_factory = sqlite3.Row
c_row = conn.cursor()

#  _____      _
# |  __ \    | |
# | |  \/ ___| |_
# | | __ / _ \ __|
# | |_\ \  __/ |_
#  \____/\___|\__|
#
def get_coord(mol, atom, geo):

    mol_id = get_mol_id(mol)
    # Only work if, id, atom, already exist
    c.execute(''' SELECT x,y,z FROM coord_tab NATURAL JOIN geo_tab
                    WHERE mol_id =? AND
                          atom=? AND
                          name = ?''', [mol_id, atom, geo])

    return c.fetchall()[0]


def get_mol_id(name):
    # Only work if name already exist
    c.execute("SELECT id FROM ele_tab WHERE name=?", [name])
    return c.fetchone()[0]


def get_method_id(name):
    # Only work if name already exist
    c.execute("SELECT method_id FROM method_tab WHERE name=?", [name])
    return c.fetchone()[0]


def get_basis_id(name):
    # Only work if name already exist
    c.execute("SELECT basis_id FROM basis_tab WHERE name=?", [name])
    return c.fetchone()[0]


def get_geo_id(name):
    # Only work if name already exist
    c.execute("SELECT geo_id FROM geo_tab WHERE name=?", [name])
    return c.fetchone()[0]


def get_run_id(method, basis, geo, comments):
    # Only work if method,basis,geo already exist
    method_id = get_method_id(method)
    basis_id = get_basis_id(basis)
    geo_id = get_geo_id(geo)

    c.execute("""SELECT run_id FROM run_tab
                WHERE method_id =(?) AND
                      basis_id = (?) AND
                      geo_id = (?)   AND
                      comments =(?)""", [method_id, basis_id, geo_id, comments])

    return c.fetchone()[0]

def list_geo(where_cond='(1)'):
    c.execute('''SELECT DISTINCT geo_tab.name
                            FROM coord_tab
                    NATURAL JOIN geo_tab
                      INNER JOIN ele_tab
                              ON coord_tab.mol_id = ele_tab.id
                           WHERE {where_cond}'''.format(where_cond=where_cond))
    return [i[0] for i in c.fetchall()]


def list_ele(where_cond='(1)'):
    c.execute('''SELECT DISTINCT ele_tab.name
                            FROM coord_tab
                    NATURAL JOIN geo_tab
                      INNER JOIN ele_tab
                              ON coord_tab.mol_id = ele_tab.id
                           WHERE {where_cond}'''.format(where_cond=where_cond))
    return [i[0] for i in c.fetchall()]


#   ___      _     _
#  / _ \    | |   | |
# / /_\ \ __| | __| |
# |  _  |/ _` |/ _` |
# | | | | (_| | (_| |
# \_| |_/\__,_|\__,_|
#
def add_new_run(method, basis, geo, comments):
    # Only work id method,basis,geo already exist
    method_id = get_method_id(method)
    basis_id = get_basis_id(basis)
    geo_id = get_geo_id(geo)

    c.execute("""INSERT INTO run_tab(method_id,basis_id,geo_id,comments)
        VALUES (?,?,?,?)""", [method_id, basis_id, geo_id, comments])
    conn.commit()


def add_or_get_run(method, basis, geo, comments):

    try:
        return get_run_id(method, basis, geo, comments)
    except TypeError:
        add_new_run(method, basis, geo, comments)
    finally:
        return get_run_id(method, basis, geo, comments)

def add_energy(run_id, name, e, err, overwrite=False, commit=False):

    if overwrite:
        cmd = """INSERT OR REPLACE INTO e_tab(run_id,ele_name,energy,err)
                  VALUES (?,?,?,?)"""
    else:
        cmd = """INSERT INTO e_tab(run_id,ele_name,energy,err)
                  VALUES (?,?,?,?)"""

    c.execute(cmd, [run_id, name, e, err])

    if commit:
        conn.commit()


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
