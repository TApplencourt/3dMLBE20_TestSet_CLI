#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Welcome! добро пожаловать! Vladimir say Hi.
You can create or modify a run_id and put_in new data in it.

Usage:
  vladimir.py (-h | --help)
  vladimir.py put_in --path=<path>
                     (--method=<method_name> --basis=<basis_name>
                      --geo=<geometry_name> --comment=<comment>|
                      --run_id=<id>)
                     (--simple | --cipsi [--epp] | --qmc)
                     [--overwrite]

WARNING ! If CIPSI will use the run_id and the run_id + 1

Example of input file for a simple run (molecule,energy):

F                             -24.1891722605
CH2_1A1                        -6.7152075579
NH                            -10.4245101299
SiH2_3B1                       -4.9754588687
CH3                            -7.4164102812

Example of input file for a CIPSI run (molecule,energy,pt2):

F                             -24.1891722605      0.0003183747
CH2_1A1                        -6.7152075579      0.0003207809
NH                            -10.4245101299      0.0003317405
SiH2_3B1                       -4.9754588687      0.0003413844
CH3                            -7.4164102812      0.0003798976

Example of input file for a QMC run (molecule,energy, error):

F                             -24.1891722605      0.0003183747
CH2_1A1                        -6.7152075579      0.0003207809
NH                            -10.4245101299      0.0003317405
SiH2_3B1                       -4.9754588687      0.0003413844
CH3                            -7.4164102812      0.0003798976


"""

version = "0.0.2"

import sys

try:
    from src.docopt import docopt
    from src.SQL_util import add_or_get_run, get_mol_id
    from src.SQL_util import add_energy
    from src.SQL_util import conn
except:
    raise
    print "File in misc is corupted. Git reset may cure the diseases"
    sys.exit(1)

if __name__ == '__main__':

    arguments = docopt(__doc__, version='G2 Api ' + version)

    if arguments["--run_id"]:
        run_id = arguments["--run_id"]
    else:
        l = [arguments[i] for i in ["--method",
                                    "--basis",
                                    "--geo",
                                    "--comment"]]
        run_id = add_or_get_run(*l)

        if arguments["--cipsi"]:
            l[3] += " (+PT2)"
            run_id_new = add_or_get_run(*l)

            assert run_id +1 == run_id_new

    print run_id,

    with open(arguments["--path"], "r") as f:
        data = [line for line in f.read().split("\n") if line]

    for line in data:

        list_ = line.split("#")[0].split()

        try:
            list_[0]
        except IndexError:
            continue

        name = list_[0]
        print name,

        if arguments["--simple"]:
            e = list_[1]

            print e
            add_energy(run_id, name, e, None, overwrite=arguments["--overwrite"])

        elif arguments["--cipsi"]:
            if not arguments["--epp"]:
                e, pt2 = list_[1:]
                ept2 = float(e) + float(pt2)
            else:
                e, ept2 = list_[1:]

            print e, ept2
            add_energy(run_id, name, e, None,
                             overwrite=arguments["--overwrite"])

            add_energy(str(int(run_id)+1), name, ept2, None,
                             overwrite=arguments["--overwrite"])


        elif arguments["--qmc"]:
            e, err = list_[1:]

            print e, err
            add_energy(run_id, name, e, err,
                           overwrite=arguments["--overwrite"])

    conn.commit()
