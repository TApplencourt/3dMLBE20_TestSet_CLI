#!/usr/bin/python
from collections import namedtuple
from collections import defaultdict

from src.__init__ import zipdic
from src.__init__ import cond_sql_or
from src.__init__ import get_formula

from irpy import lazy_property
from irpy import lazy_property_mutable
from irpy import lazy_property_leaves

from src.SQL_util import c, c_row


class BigData(object):

    # ___           
    #  |  ._  o _|_ 
    # _|_ | | |  |_ 
    #

    @lazy_property_leaves(immutables=["d_arguments"])
    def __init__(self, d_arguments):
        #Sanitize
        self.d_arguments = {k: v for k, v in d_arguments.iteritems() if v}

#  _            ___      _    
# |_)     ._     |  ._ _|_ _  
# | \ |_| | |   _|_ | | | (_) 
#

    @lazy_property
    def d_arg_to_db(self):
        d = {
            "--run": "run_id",
            "--geo": "geo",
            "--basis": "basis",
            "--method": "method",
            "--comments": "comments"
        }
        return d

    @lazy_property
    def d_run_info(self):
        "Return a dict in adecation with d_arguments"

        d_arg2db = self.d_arg_to_db
        d_arg2value = self.d_arguments

        l = d_arg2db.viewkeys() & d_arg2value.viewkeys()
        if l:
            l_cond_filter = [cond_sql_or(table_name=d_arg2db[k],
                                         l_value=d_arg2value[k]) for k in l]
        else:
            l_cond_filter = ["(1)"]

        sql_cmd_where = " AND ".join(l_cond_filter)

        # -#-#- #
        # S Q L #
        # -#-#- #
        cursor = c_row.execute("""SELECT run_id,
                                         method,
                                         basis,
                                         geo,
                                         comments
                                    FROM run_tab_expended
                                   WHERE {0}
                               """.format(sql_cmd_where))

        RunInfo = namedtuple('RunInfo', 'run_id, method, basis, geo, comments')

        d_run_info = dict()
        for emp in map(RunInfo._make, cursor.fetchall()):
            d_run_info[emp.run_id] = emp

        assert d_run_info, "No run_id with: {0}".format(sql_cmd_where)

        return d_run_info

    @lazy_property
    def run_id_ref(self):
        return int(self.d_arguments["--ref"])

    @lazy_property
    def l_run_id(self):
        return self.d_run_info.keys()

    # _                                                                     
    # |_ |  _  ._ _   _  ._ _|_   ._ _   _. ._   _.  _   _  ._ _   _  ._ _|_ 
    # |_ | (/_ | | | (/_ | | |_   | | | (_| | | (_| (_| (/_ | | | (/_ | | |_ 
    #                                                _|
    def get_l_children(self, l_ele):
        "From a list of element, return the list of children"
        l = {a
             for ele in l_ele for a in get_formula(ele)
             } if l_ele != set(["*"]) else set(["*"])
        return l

    def db_list_element(self, run_id):
        """
        Get the element listed in a run_id
        """
        sql_cmd_where = cond_sql_or("run_id", [run_id])

        cursor = c_row.execute("""SELECT ele_name
                                    FROM run_tab_ele
                                   WHERE {0}
                               """.format(sql_cmd_where))

        l_ele = {i[0] for i in cursor}

        str_ = "No element in run_id: {0}"
        assert (l_ele), str_.format(self.d_arguments["--like-run"])

        return l_ele

    def check_argument(self, str_):
        if str_ in self.d_arguments:
            return self.d_arguments[str_]
        else:
            return False

    @lazy_property
    def l_element_whe_ask(self):
        "From d_arguments return the list of element we whant"
        if "--with" in self.d_arguments:
            l_ele = set(self.d_arguments["--with"])

        elif "--like-sr7" in self.d_arguments:
            l_ele = set(["MnCl", "ZnCl", "FeCl", "CrCl", "ZnS", "ZnH", "CuCl"])

        elif "--like-mr13" in self.d_arguments:
            l_ele = set(["ZnO", "NiCl", "TiCl", "CuH", "VO", "VCl", "MnS",
                         "CrO", "CoH", "CoCl", "VH", "FeH", "CrH"])

        elif "--like-run" in self.d_arguments:
            l_ele = self.db_list_element(self.d_arguments["--like-run"])
        else:

            l_ele = set(["*"])

        if "--with_children" in self.d_arguments:
            l_ele |= self.get_l_children(l_ele)

        return l_ele

    @lazy_property
    def l_element_whe_want(self):
        "If we ask for ae, or for list_run we need the children"

        l_ele = self.l_element_whe_ask

        ae_or_list_run = set(["ae", "list_run"]) & self.d_arguments.viewkeys()
        if ae_or_list_run and not "--like-run" in self.d_arguments:
            l_ele |= self.get_l_children(l_ele)

        return l_ele

    @lazy_property
    def l_element(self):
        """
        Get the element from the databse
        """
        l = {
            cond_sql_or(k, v)
            for k, v in (["ele_name", self.l_element_whe_want],
                         ["run_id", self.l_run_id])
        }
        sql_cmd_where = " AND ".join(l)

        cursor = c_row.execute("""SELECT DISTINCT ele_name
                                             FROM run_tab_ele
                                            WHERE {0}
                               """.format(sql_cmd_where))

        return {i[0] for i in cursor.fetchall()}

    #  __                               
    # /__  _ _|_   \  / _. |      _   _ 
    # \_| (/_ |_    \/ (_| | |_| (/_ _> 
    #
    def db_get(self, table_name):
        """
        Get a table from the database
        Return a dict[run_id][ele] = Value
        TableName is eather e_tab _ae_tab 
        """
        l = {
            cond_sql_or(k, v)
            for k, v in (["ele_name", self.l_element_whe_want],
                         ["run_id", self.l_run_id])
        }

        sql_cmd_where = " AND ".join(l)

        cursor = c_row.execute("""SELECT *
                                    FROM {0}
                                   WHERE {1}
                               """.format(table_name, sql_cmd_where))

        from src.object import Energie
        d = defaultdict(dict)
        for r in cursor:
            e = r["energy"]
            err = r["err"] if r["err"] else 0

            d[r["run_id"]][r["ele_name"]] = Energie(e, err)

        return d

    def dict_subset_of_ref(self, d):
        """
        Take a dict in argument and
        return a new dict with these key are a subset of the ref
        """
        d_filter = defaultdict(dict)

        run_id = int(self.d_arguments["--like-run"])
        k_ref = d[run_id].viewkeys()

        for run_id, d_ in d.items():
            if k_ref <= d_.viewkeys():
                d_filter[run_id] = {k: d_[k] for k in k_ref}

        return d_filter

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#- #
    # E n e r g i e #
    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#- #

    @lazy_property
    def d_e_db(self):
        return self.db_get("e_tab")

    @lazy_property
    def d_e(self):
        if set(["--like-run", "--respect_to"]) <= self.d_arguments.viewkeys(
        ) and self.d_arguments["--respect_to"] == "e":
            d = self.dict_subset_of_ref(self.d_e_db)
        else:
            d = self.d_e_db

        return d

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#- #
    # A t o m i s a t i o n _ E n e r g i e #
    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#- #

    @lazy_property
    def d_ae_db(self):
        return self.db_get("ae_tab")

    @lazy_property
    def d_ae_calc(self):

        d = defaultdict(dict)

        for run_id, d_mol in self.d_e.items():
            for ele, energy in d_mol.items():

                if len(get_formula(ele)) == 1:
                    continue

                try:
                    ae = sum(d_mol[i] for i in get_formula(ele)) - d_mol[ele]
                except KeyError:
                    pass
                else:
                    ae *= 627.503
                    d[run_id][ele] = ae
        return d

    @lazy_property
    def d_ae(self):

        d_ae_full = self.d_ae_db.copy()
        d_ae_full.update(self.d_ae_calc)

        if set(["--like-run", "--respect_to"]) <= self.d_arguments.viewkeys(
        ) and self.d_arguments["--respect_to"] == "ae":
            d = self.dict_subset_of_ref(d_ae_full)
        else:
            d = d_ae_full

        return d

    @lazy_property
    def d_ae_ref(self):
        d_arguments = {"--run_id": [self.run_id_ref], "--with_children": True}
        q = BigData(d_arguments=d_arguments)

        return q.d_ae[self.run_id_ref]

    @lazy_property
    def d_ae_deviation(self):
        d = defaultdict(dict)
        for run_id, d_ae_run_id in self.d_ae.items():

            for ele, energy, energy_ref in zipdic(d_ae_run_id, self.d_ae_ref):
                d[run_id][ele] = energy - energy_ref

        return d

    @lazy_property
    def d_mad(self):
        d = {}
        for run_id, d_ele in self.d_ae_deviation.items():
            l_ae_dev = d_ele.values()
            mad = sum(map(abs, l_ae_dev)) / len(l_ae_dev)
            d[run_id] = mad
        return d

    @lazy_property
    def d_rmsad(self):
        d = {}
        for run_id, d_ele, mad in zipdic(self.d_ae_deviation, self.d_mad):
            l_ae_dev = d_ele.values()
            rmsad = sum((abs(ae_dev) - mad).e ** 2
                        for ae_dev in l_ae_dev) / (len(l_ae_dev) - 1)
            d[run_id] = rmsad
        return d