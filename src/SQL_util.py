#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

try:
    import sqlite3
except:
    print "Sorry, you need sqlite3"
    sys.exit(1)


# ___  ____
# |  \/  (_)
# | .  . |_ ___  ___
# | |\/| | / __|/ __|
# | |  | | \__ \ (__
# \_|  |_/_|___/\___|
#
def isSQLite3(filename):
    from os.path import isfile, getsize

    if not isfile(filename):
        return False
    if getsize(filename) < 100:  # SQLite database file header is 100 bytes
        return False

    with open(filename, 'rb') as fd:
        header = fd.read(100)

    if header[:16] == 'SQLite format 3\x00':
        return True
    else:
        return False

path = os.path.dirname(__file__) + "/../db/g2.db"
if not isSQLite3(path):
    print "'%s' is not a SQLite3 database file" % path
    print sys.exit(1)


def cond_sql_or(table_name, l_value):

    l = []
    dmy = " OR ".join(['%s = "%s"' % (table_name, i) for i in l_value])
    if dmy:
        l.append("(%s)" % dmy)

    return l


conn = sqlite3.connect(path)
c = conn.cursor()


#  _____      _
# |  __ \    | |
# | |  \/ ___| |_
# | | __ / _ \ __|
# | |_\ \  __/ |_
#  \____/\___|\__|
#
def get_coord(id, atom, geo_name):
    c.execute(''' SELECT x,y,z FROM coord_tab NATURAL JOIN geo_tab
                WHERE id =?  AND
                      atom=? AND
                      name = ?''', [id, atom, geo_name])

    return c.fetchall()


def get_mol_id(name):
    c.execute("SELECT id FROM id_tab WHERE name=?", [name])
    r = c.fetchone()[0]
    return r


def get_method_id(name):
    c.execute("SELECT method_id FROM method_tab WHERE name=?", [name])
    r = c.fetchone()[0]
    return r


def get_basis_id(name):
    c.execute("SELECT basis_id FROM basis_tab WHERE name=?", [name])
    r = c.fetchone()[0]
    return r


def get_geo_id(name):
    c.execute("SELECT geo_id FROM geo_tab WHERE name=?", [name])
    r = c.fetchone()[0]
    return r


def list_geo(where_cond='(1)'):
    c.execute('''SELECT DISTINCT geo_tab.name
                            FROM coord_tab
                    NATURAL JOIN geo_tab
                      INNER JOIN id_tab
                              ON coord_tab.id = id_tab.id
                           WHERE {where_cond}'''.format(where_cond=where_cond))
    return [i[0] for i in c.fetchall()]


def list_ele(where_cond='(1)'):
    c.execute('''SELECT DISTINCT id_tab.name
                            FROM coord_tab
                    NATURAL JOIN geo_tab
                      INNER JOIN id_tab
                              ON coord_tab.id = id_tab.id
                           WHERE {where_cond}'''.format(where_cond=where_cond))
    return [i[0] for i in c.fetchall()]


# ______ _      _
# |  _  (_)    | |
# | | | |_  ___| |_
# | | | | |/ __| __|
# | |/ /| | (__| |_
# |___/ |_|\___|\__|
#
def full_dict(geo_name, only_neutral=True):
    d = dict_raw()

    for i, dic_ele in d.items():

        if only_neutral:
            if "+" in i or "-" in i:
                del d[i]
                continue

        formula_clean = []
        a = []
        for [atom, nb] in dic_ele["formula"]:
            for l in range(0, nb):
                formula_clean.append(atom)

            list_ = get_coord(dic_ele["id"], atom, geo_name)
            if not list_:
                del d[i]
                break
            else:
                a += list_

        dic_ele["formula_clean"] = formula_clean
        dic_ele["list_xyz"] = a

    return dict(d)


def dict_raw():
    c.execute(
        '''SELECT id,name,formula,charge,multiplicity,num_atoms,num_elec,symmetry FROM id_tab''')

    d = {}
    for i in c.fetchall():
        d[str(i[1])] = {"id": str(i[0]),
                        "formula": eval(i[2]),
                        "charge": int(i[3]),
                        "multiplicity": int(i[4]),
                        "num_atoms": int(i[5]),
                        "symmetry": str(i[6])}

    return d


#   ___      _     _
#  / _ \    | |   | |
# / /_\ \ __| | __| |
# |  _  |/ _` |/ _` |
# | | | | (_| | (_| |
# \_| |_/\__,_|\__,_|
#
def add_new_run(method, basis, geo, comments):

    method_id = get_method_id(method)
    basis_id = get_basis_id(basis)
    geo_id = get_geo_id(geo)

    c.execute("""INSERT INTO run_tab(method_id,basis_id,geo_id,comments)
        VALUES (?,?,?,?)""", [method_id, basis_id, geo_id, comments])

    conn.commit()


def add_energy_cispi(run_list,
                     geo_list,
                     basis_list,
                     path,
                     tail,
                     TruePt2=False,
                     compatibility=False,
                     debug=False):

    index = 0
    for geo in geo_list:

        dict_ = full_dict(geo)

        for basis in basis_list:

            for name, dic in dict_.iteritems():

                if compatibility:
                    from misc_info import new_name_to_old
                    name_path = new_name_to_old[
                        name] if name in new_name_to_old else name
                else:
                    name_path = name

                url = "".join([path, name_path, "_", basis, "_", geo, tail])

                if not os.path.isfile(url):
                    print "%s not existing" % url
                    continue

                with open(url, "r") as f:
                    s = f.read()

                    if TruePt2 and s.find("Final step") == -1:
                        print "%s have not a true PT2 for" % url
                        continue
                    else:
                        s = s[s.rfind(' N_det'):]

                s = s.splitlines()

                ndet = pt2 = time = None

                for i in s:
                    if "N_det " in i:
                        ndet = i.split("=")[-1].strip()
                    if " PT2      =" in i:
                        pt2 = i.split("=")[-1].strip()
                    if "E   " in i:
                        e = i.split("=")[-1].strip()
                    if "Wall" in i:
                        time = i.split(":")[-1].strip()

                if not all([ndet, e, time]):
                    print "%s file is buggy" % url
                    continue

                id_ = get_mol_id(name)
                run_id = run_list[index]

                print name, run_id, id_, ndet, pt2, e, time

                if not debug:
                    c.execute('''INSERT OR REPLACE INTO
                                cipsi_energy_tab(run_id,id,ndet,energy,pt2,time)
                                VALUES (?,?,?,?,?,?)''', [run_id, id_, ndet, e, pt2, time])

                    conn.commit()

            index += 1


# ______                         _
# |  ___|                       | |
# | |_ ___  _ __ _ __ ___   __ _| |_
# |  _/ _ \| '__| '_ ` _ \ / _` | __|
# | || (_) | |  | | | | | | (_| | |_
# \_| \___/|_|  |_| |_| |_|\__,_|\__|
#
def get_xyz(geo, ele, only_neutral=True):
    b = full_dict(geo, only_neutral)

    dic_ = b[ele]

    xyz_file_format = [dic_["num_atoms"]]

    line = " ".join(map(str, [ele,
                              "Geo:", geo,
                              "Mult:", dic_["multiplicity"],
                              "symmetry:", dic_["symmetry"]]))
    xyz_file_format.append(line)

    for atom, xyz in zip(dic_["formula_clean"], dic_["list_xyz"]):
        line_xyz = "    ".join(map(str, xyz))
        line = "    ".join([atom, line_xyz])

        xyz_file_format.append(line)

    return "\n".join(map(str, xyz_file_format))


def get_g09(geo, ele, only_neutral=True):
    b = full_dict(geo, only_neutral)

    dic_ = b[ele]

    line = " ".join(map(str, [ele,
                              "Geo:", geo,
                              "Mult:", dic_["multiplicity"],
                              "symmetry:", dic_["symmetry"]]))

    g09_file_format = ["# cc-pvdz", "", line, "",
                       "%d %d" % (dic_["charge"], dic_["multiplicity"])]

    for atom, xyz in zip(dic_["formula_clean"], dic_["list_xyz"]):
        line_xyz = "    ".join(map(str, xyz))
        line = "    ".join([atom, line_xyz])

        g09_file_format.append(line)
    g09_file_format.append("\n\n\n")
    return "\n".join(map(str, g09_file_format))


# ___  ___      _
# |  \/  |     (_)
# | .  . | __ _ _ _ __
# | |\/| |/ _` | | '_ \
# | |  | | (_| | | | | |
# \_|  |_/\__,_|_|_| |_|
#
if __name__ == "__main__":

#    add_new_run("CIPSI", "cc-pvtz", "Experiment", "1M_Dets_NO_1k_Dets_TruePT2")
#    add_new_run("CIPSI", "cc-pvtz", "MP2", "1M_Dets_NO_1k_Dets_TruePT2")

    add_energy_cispi([26, 27], ["Experiment", "MP2"], ["cc-pvtz"],
                     "/tmp/log_backup/", ".HF_1M_on_10k_true.log",
                     TruePt2=False, compatibility=True, debug=False)

    pass