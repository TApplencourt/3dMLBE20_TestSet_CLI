#!/usr/bin/python

from src.SQL_util import c, c_row
from src.SQL_util import cond_sql_or

from collections import namedtuple
from src.__init__ import lru_cache, zipdic


class BigData(object):

    # ___           
    #  |  ._  o _|_ 
    # _|_ | | |  |_ 
    #

    def __init__(self, d_arguments, run_id_ref=None):
        self.d_arguments = d_arguments
        self.run_id_ref = int(run_id_ref)

    @property
    @lru_cache(maxsize=1)
    def d_run_info(self):
        "Return a dict in adecation of d_arguments"

        d = {"run_id": "--run_id",
             "geo": "--geo",
             "basis": "--basis",
             "method": "--method",
             "comments": "--comments"}

        # If the user give ask for somme run_id return it
        l_cond_filter = []

        for k, v in d.items():
            try:
                l_cond_filter += cond_sql_or(k, self.d_arguments[v])
            except KeyError:
                pass

        l_cond_filter = l_cond_filter if l_cond_filter else ["(1)"]

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

        if not d_run_info:
            print "No run_id with:", sql_cmd_where
            sys.exit(1)

        return d_run_info

    @property
    @lru_cache(maxsize=1)
    def l_run_id(self):
        return self.d_run_info.keys()

    @property
    @lru_cache(maxsize=1)
    def d_formula(self):
        """
        Input: l_ele
    
        Return
        d |
        -> key: name
        -> value: the flaten formula (H,H,O) for H2O for exemple.
    
        All the element need to have a formula!
        """
        d = dict()

        c.execute("""SELECT name, formula
                                   FROM ele_tab""")

        d = {name: [a * nb for a, nb in eval(f)] for (name, f) in c.fetchall()}

        return d

    @property
    @lru_cache(maxsize=1)
    def l_element_whe_want(self):

        from src.db_interface import db_list_element
        """
        Input
        d_arguments: docot dict of arguments
        
        Return
        l_ele:  list of element who satisfy the condition
        If we need to get all the element, l_ele = "*"
        """

        if self.d_arguments["--ele"]:
            l_ele = self.d_arguments["--ele"]
        elif self.d_arguments["--like-sr7"]:
            l_ele = ["MnCl", "ZnCl", "FeCl", "CrCl", "ZnS", "ZnH", "CuCl"]
        elif self.d_arguments["--like-mr13"]:
            l_ele = ["ZnO", "NiCl", "TiCl", "CuH", "VO", "VCl", "MnS", "CrO",
                     "CoH", "CoCl", "VH", "FeH", "CrH"]
        elif self.d_arguments["--like_run_id"]:
            l_ele = db_list_element(self.d_arguments["--like_run_id"])
        else:
            l_ele = ["*"]

        if self.d_arguments["--all_children"] and not l_ele == ["*"]:
            l_ele = list(set(
                l_ele + [a for ele in l_ele for a in self.d_formula[ele]]))

        return l_ele

    @property
    @lru_cache(maxsize=1)
    def d_l_element(self):

        from collections import defaultdict

        l = cond_sql_or("ele_name", self.l_element_whe_want)
        l += cond_sql_or("run_id", self.l_run_id)
        sql_cmd_where = " AND ".join(l)

        cursor = c_row.execute("""SELECT run_id,
                                          ele_name
                                   FROM run_tab_ele
                                   WHERE {0}
                                """.format(sql_cmd_where))

        d_run_id_ele = defaultdict(list)
        for run_id, ele in cursor:
            d_run_id_ele[run_id].append(ele)

        assert d_run_id_ele, "No run have any element you request: {0}".format(
            self.l_element_whe_want)

        return d_run_id_ele

    @property
    @lru_cache(maxsize=1)
    def l_element(self):
        return list(set.union(*map(set, self.d_l_element.values())))

    def db_get(self, table_name):

        l = cond_sql_or("run_id", self.l_run_id)
        l += cond_sql_or("ele_name", self.l_element)
        sql_cmd_where = " AND ".join(l)

        cursor = c_row.execute("""SELECT *
                                  FROM {0}
                                 WHERE {1}"""
                               .format(table_name, sql_cmd_where))

        from collections import defaultdict
        from src.object import Energie

        d = defaultdict(dict)

        for r in cursor:

            e = r["energy"]
            err = r["err"] if r["err"] else 0

            d[r["run_id"]][r["ele_name"]] = Energie(e, err)

        return d

    @property
    @lru_cache(maxsize=1)
    def d_e_db(self):
        return self.db_get("e_tab")

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#- #
    # A t o m i s a t i o n _ E n e r g i e #
    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#- #

    @property
    @lru_cache(maxsize=1)
    def d_ae_db(self):

        d = self.db_get("ae_tab")

        for key, value in d.items():
                for key2, value2 in value:
                    d[key2][value2] *= 627.503
        return d

    @property
    @lru_cache(maxsize=1)
    def d_ae_calc(self):

        from collections import defaultdict

        d = defaultdict(dict)

        for run_id, d_mol in self.d_e.items():
            for ele, energy in d_mol.items():

                if len(self.d_formula[ele]) == 1:
                    continue

                try:
                    d[run_id][ele] = sum(
                        d_mol[i] for i in self.d_formula[ele]) - d_mol[ele]
                except KeyError:
                    pass

        return d

    @property
    @lru_cache(maxsize=1)
    def d_ae(self):
        d = self.d_ae_db.copy()
        d.update(self.d_ae_calc)

        return d

    @property
    @lru_cache(maxsize=1)
    def d_e(self):

        return self.d_e_db

    @property
    @lru_cache(maxsize=1)
    def d_ae_deviation(self):

        from collections import defaultdict

        d = defaultdict(dict)

        assert self.run_id_ref, "You need to set a run reference for compute the deviation"
        assert self.run_id_ref in self.l_run_id, "{0} need to be in {1}".format(
            self.run_id_ref, self.l_run_id)

        for run_id, d_ae_run_id in self.d_ae.items():

            for ele, energy, energy_ref in zipdic(d_ae_run_id,
                                                  self.d_ae[self.run_id_ref]):
                d[run_id][ele] = energy - energy_ref

        return d

    @property
    @lru_cache(maxsize=1)
    def d_mad(self):
        d = {}
        for run_id, d_ele in self.d_ae_deviation.items():
            l_energy = d_ele.values()
            mad = sum(map(abs, l_energy)) / len(l_energy)
            d[run_id] = mad
        return d


if __name__ == '__main__':
    d_arguments = {"--run_id": [1, 8],
                   "--ele": ["MnCl"],
                   "--all_children": True}

    q = BigData(d_arguments=d_arguments, run_id_ref="1")
    print q.d_ae
    print q.d_ae_deviation
