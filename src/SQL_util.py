#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

try:
    import sqlite3
except:
    print "Sorry, you need sqlite3"
    sys.exit(1)

try:
    from lib.sqlit import connect4git
except:
    print "Sorry, you need the sqlit librairy"
    sys.exit(1)

from src.__init__ import get_formula
from src.__init__ import cond_sql_or
from src.__init__ import run_info_2_hash

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


#  __        
# /__  _ _|_ 
# \_| (/_ |_ 
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

    c.execute("""SELECT run_id FROM run_tab_expended
                WHERE method =(?) AND
                       basis =(?) AND
                         geo =(?) AND
                    comments =(?)""", [method, basis, geo, comments])

    return c.fetchone()[0]


def get_run_info(run_id):
    c.execute("""SELECT method,
                        basis,
                        geo,
                        comments 
                   FROM run_tab_expended
                  WHERE run_id = (?)""", [run_id])

    return list(c.fetchall()[0])


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


#              
#  /\   _|  _| 
# /--\ (_| (_| 
#              
def add_new_run(method, basis, geo, comments):
    # Only work id method,basis,geo already exist
    method_id = get_method_id(method)
    basis_id = get_basis_id(basis)
    geo_id = get_geo_id(geo)

    run_id = run_info_2_hash("".join([method,basis,geo,comments]))

    c.execute("""INSERT INTO run_tab(run_id,method_id,basis_id,geo_id,comments)
        VALUES (?,?,?,?,?)""", [run_id,method_id, basis_id, geo_id, comments])
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

#                         
# | | ._   _|  _. _|_  _  
# |_| |_) (_| (_|  |_ (/_ 
#     |

def update_run_id(run_id_new,run_id_old, commit=False):

    for tab in "run_tab so_tab ae_tab e_tab".split():
        cmd = """UPDATE {0}
                    SET run_id=?
                  WHERE run_id=?""".format(tab)
        c.execute(cmd, [run_id_new,run_id_old])

    if commit:
        conn.commit()

def delete_run_id(run_id, commit=False):

    for tab in "run_tab so_tab ae_tab e_tab".split():
        cmd = """DELETE FROM {0}
                WHERE run_id=?""".format(tab)
        c.execute(cmd, [run_id])

    if commit:
        conn.commit()