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


def cond_sql_or(table_name, l_value, glob=True):
    # Create the OR condition for a WHERE filter

    l = []

    operator = "GLOB" if glob else "=="

    dmy = " OR ".join(['{} {} "{}"'.format(table_name,operator,i) for i in l_value])
    if dmy:
        l.append("(%s)" % dmy)

    return l

def cond_sql_and(table_name, l_value, glob=True):
    # Create the OR condition for a WHERE filter

    l = []

    operator = "GLOB" if glob else "=="

    dmy = " AND ".join(['{} {} "{}"'.format(table_name,operator,i) for i in l_value])
    if dmy:
        l.append("(%s)" % dmy)

    return l


#  _____      _
# |  __ \    | |
# | |  \/ ___| |_
# | | __ / _ \ __|
# | |_\ \  __/ |_
#  \____/\___|\__|
#
def get_coord(id, atom, geo):
    # Only work if, id, atom, already exist
    c.execute(''' SELECT x,y,z FROM coord_tab NATURAL JOIN geo_tab
                WHERE mol_id =?  AND
                      atom=? AND
                      name = ?''', [id, atom, geo])

    return c.fetchall()


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
def full_dict(geo_name=None):
    d = dict_raw()

    for i, dic_ele in d.items():

        formula_flat = []
        a = []
        for [atom, nb] in dic_ele["formula"]:
            for l in range(0, nb):
                formula_flat.append(atom)

            if geo_name:
                list_ = get_coord(dic_ele["id"], atom, geo_name)
                if not list_:
                    del d[i]
                    break
                else:
                    a += list_

        dic_ele["formula_flat"] = formula_flat

        if geo_name:
            dic_ele["list_xyz"] = a

    return dict(d)


def dict_raw():
    c.execute(
        '''SELECT id,name,formula,charge,multiplicity,num_atoms,num_elec,symmetry FROM ele_tab''')

    d = {}
    for i in c.fetchall():
        d[str(i[1])] = {"id": str(i[0]),
                        "formula": eval(i[2]),
                        "charge": int(i[3]),
                        "multiplicity": int(i[4]),
                        "num_atoms": int(i[5]),
                        "symmetry": str(i[6])}

    return d

# ______                         _
# |  ___|                       | |
# | |_ ___  _ __ _ __ ___   __ _| |_
# |  _/ _ \| '__| '_ ` _ \ / _` | __|
# | || (_) | |  | | | | | | (_| | |_
# \_| \___/|_|  |_| |_| |_|\__,_|\__|
#
def get_xyz(geo, ele, only_neutral=True):
    b = full_dict(geo)

    dic_ = b[ele]

    xyz_file_format = [dic_["num_atoms"]]

    line = " ".join(map(str, [ele,
                              "Geo:", geo,
                              "Mult:", dic_["multiplicity"],
                              "Symmetry:", dic_["symmetry"]]))
    xyz_file_format.append(line)

    for atom, xyz in zip(dic_["formula_flat"], dic_["list_xyz"]):
        line_xyz = "    ".join(map(str, xyz))
        line = "    ".join([atom, line_xyz])

        xyz_file_format.append(line)

    return "\n".join(map(str, xyz_file_format))


def get_g09(geo, ele, only_neutral=True):
    b = full_dict(geo)

    dic_ = b[ele]

    line = " ".join(map(str, [ele,
                              "Geo:", geo,
                              "Mult:", dic_["multiplicity"],
                              "symmetry:", dic_["symmetry"]]))

    method = "RHF" if dic_["multiplicity"] == 1 else "ROHF"

    g09_file_format = ["# cc-pvdz %s" % (method), "", line, "",
                       "%d %d" % (dic_["charge"], dic_["multiplicity"])]

    for atom, xyz in zip(dic_["formula_flat"], dic_["list_xyz"]):
        line_xyz = "    ".join(map(str, xyz)).replace("e", ".e")
        line = "    ".join([atom, line_xyz])

        g09_file_format.append(line)
    g09_file_format.append("\n\n\n")
    return "\n".join(map(str, g09_file_format))
