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
  vladimir.py remove --run_id=<id>

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
    from lib.docopt import docopt
    from src.SQL_util import add_or_get_run, get_run_info, delete_run_id
    from src.SQL_util import add_energy
    from src.SQL_util import conn
    from src.__init__ import check_argument
except:
    raise
    print "File in misc is corupted. Git reset may cure the diseases"
    sys.exit(1)
    
from lib.irpy import irpy


class Vladimir(object):

    # ___           
    #  |  ._  o _|_ 
    # _|_ | | |  |_ 
    #

    @irpy.lazy_property_leaves(immutables=["d_arguments"])
    def __init__(self, d_arguments):
        #Sanitize
        self.d_arguments = {k: v for k, v in d_arguments.iteritems() if v}

    @irpy.lazy_property
    def overwrite(self):
        return check_argument(self.d_arguments, "--overwrite")

    @irpy.lazy_property
    def run_id(self):
        if "--run_id" in self.d_arguments:
            run_id = self.d_arguments["--run_id"]
        else:
            l = [arguments[i]
                 for i in ["--method", "--basis", "--geo", "--comment"]]
            run_id = add_or_get_run(*l)

        return run_id

    @irpy.lazy_property
    def run_id_pt2(self):
        l = get_run_info(self.run_id)
        l[-1] += " (+PT2)"
        run_id = add_or_get_run(*l)

        return run_id

    @irpy.lazy_property
    def ll_data(self):
        with open(self.d_arguments["--path"], "r") as f:
            #Get Line
            l_line = [line for line in f.read().split("\n") if line]


        #Now handle '#'
        l_wo_comm = [line.split('#')[0] for line in l_line if line]

        #Now finaly split
        return [line.split() for line in l_wo_comm]

    def add_simple_energy(self):

        for name, energy in self.ll_data:

            add_energy(run_id=self.run_id,
                       name=name,
                       e=energy,
                       err=None,
                       overwrite=self.overwrite)

        conn.commit()

    def add_cipsi(self):

        for name, energy, pt2 in self.ll_data:

            ept2 = float(energy) + float(pt2)

            for run_id, e in ([self.run_id, energy], [self.run_id_pt2, ept2]):

                add_energy(run_id=run_id,
                           name=name,
                           e=e,
                           err=None,
                           overwrite=self.overwrite)

        conn.commit()

    def add_cipsi_epp(self):

        for name, energy, ept2 in self.ll_data:

            for run_id, e in ([self.run_id, energy], [self.run_id_pt2, ept2]):

                add_energy(run_id=run_id,
                           name=name,
                           e=e,
                           err=None,
                           overwrite=self.overwrite)

        conn.commit()

    def add_qmc(self):

        for name, energy, err in self.ll_data:

            add_energy(run_id=self.run_id,
                       name=name,
                       e=energy,
                       err=err,
                       overwrite=self.overwrite)

        conn.commit()


if __name__ == '__main__':

    arguments = docopt(__doc__)
    v = Vladimir(arguments)

    if arguments["put_in"]:
        if arguments["--simple"]:
            v.add_simple_energy()
        elif arguments["--epp"]:
            v.add_cipsi_epp()
        elif arguments["--cipsi"]:
            v.add_cipsi()
        elif arguments["--qmc"]:
            v.add_qmc()
    elif arguments["remove"]:
        delete_run_id(run_id=arguments["--run_id"], commit=True)
