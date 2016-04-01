#!/usr/bin/python
from collections import namedtuple
from collections import defaultdict

from src.__init__ import lru_cache
from src.__init__ import zipdic
from src.__init__ import cond_sql_or
from src.__init__ import get_formula

from src.SQL_util import c, c_row


class BigData(object):

    # ___           
    #  |  ._  o _|_ 
    # _|_ | | |  |_ 
    #

    def __init__(self, d_arguments):
        self.d_arguments = d_arguments
 

    @property
    @lru_cache(maxsize=1)
    def d_run_info(self):
        "Return a dict in adecation of d_arguments"

        d = {"run_id": "--run",
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

        assert d_run_info, "No run_id with: {0}".format(sql_cmd_where)

        return d_run_info

    @property
    @lru_cache(maxsize=1)
    def run_id_ref(self):
        return int(self.d_arguments["--ref"])
    
    @property
    @lru_cache(maxsize=1)
    def l_run_id(self):
        return self.d_run_info.keys()

    def get_l_children(self, l_ele):
        return list(set([a for ele in l_ele for a in get_formula(ele)]))

    def db_list_element(self, run_id):

        sql_cmd_where = "".join(cond_sql_or("run_id", [run_id]))

        cursor = c_row.execute("""SELECT ele_name
                                   FROM  run_tab_ele
                                   WHERE {0}
                               """.format(sql_cmd_where))

        l_ele = [i[0] for i in cursor]

        str_ = "No element in run_id: {0}"
        assert (l_ele), str_.format(self.d_arguments["--like-run"])

        return l_ele

    def check(self, str_):
        if str_ in self.d_arguments and self.d_arguments[str_]:
            return self.d_arguments[str_]
        else:
            return False

    @property
    @lru_cache(maxsize=1)
    def l_element_whe_ask(self):

        if self.check("--with"):
            l_ele = self.d_arguments["--with"]
        elif self.check("--like-sr7"):
            l_ele = ["MnCl", "ZnCl", "FeCl", "CrCl", "ZnS", "ZnH", "CuCl"]
        elif self.check("--like-mr13"):
            l_ele = ["ZnO", "NiCl", "TiCl", "CuH", "VO", "VCl", "MnS", "CrO",
                     "CoH", "CoCl", "VH", "FeH", "CrH"]
        elif self.check("--like-run"):
            l_ele = self.db_list_element(self.d_arguments["--like-run"])
        else:
            l_ele = ["*"]

        if self.check("--with_children") and not l_ele == ["*"]:
            l_ele += self.get_l_children(l_ele)

        return l_ele

    @property
    @lru_cache(maxsize=1)
    def l_element_whe_want(self):

        l_ele = self.l_element_whe_ask

        if any([self.check("ae"), self.check("list_run"), not l_ele == ["*"],
                not self.check("--like-run")]):

            l_child = self.get_l_children(l_ele)
            l_ele = list(set(l_ele) | set(l_child))

        return l_ele

    @property
    @lru_cache(maxsize=1)
    def l_element(self):

        l = cond_sql_or("ele_name", self.l_element_whe_want)
        l += cond_sql_or("run_id", self.l_run_id)
        sql_cmd_where = " AND ".join(l)

        cursor = c_row.execute("""SELECT DISTINCT
                                         ele_name
                                   FROM run_tab_ele
                                   WHERE {0}
                               """.format(sql_cmd_where))

        return [i[0] for i in cursor.fetchall()]


    def db_get(self, table_name):

        l = cond_sql_or("run_id", self.l_run_id)
        l += cond_sql_or("ele_name", self.l_element)
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
        return d

    @property
    @lru_cache(maxsize=1)
    def d_ae_calc(self):

        d = defaultdict(dict)

        for run_id, d_mol in self.d_e.items():
            for ele, energy in d_mol.items():

                if len(get_formula(ele)) == 1:
                    continue

                try:
                    d[run_id][ele] = sum(
                        d_mol[i] for i in get_formula(ele)) - d_mol[ele]
                    d[run_id][ele] *= 627.503

                except KeyError:
                    pass

        return d

    
    def dict_subset(self,d):

        d_filter = defaultdict(dict)

        run_id = int(self.d_arguments["--like-run"])
        k_ref = d[run_id].viewkeys()

        for run_id, d_ in d.items():
                if k_ref <= d_.viewkeys():
                    d_filter[run_id] = {k: d_[k] for k in k_ref}

        return d_filter

    @property
    @lru_cache(maxsize=1)
    def d_ae(self):

        d = self.d_ae_db.copy()
        d.update(self.d_ae_calc)

        if self.check("--like-run") and self.check("--respect_to")=="ae":
            d = self.dict_subset(d)

        return d

    @property
    @lru_cache(maxsize=1)
    def d_ae_ref(self):

        d_arguments = {"--run_id": [self.run_id_ref], "--with_children": True}
        q = BigData(d_arguments=d_arguments)

        return q.d_ae[self.run_id_ref]

    @property
    @lru_cache(maxsize=1)
    def d_e(self):

        d = self.d_e_db
        
        if self.check("--like-run") and self.check("--respect_to")=="e":
            d = self.dict_subset(d)

        return d

    @property
    @lru_cache(maxsize=1)
    def d_ae_deviation(self):

        d = defaultdict(dict)

        for run_id, d_ae_run_id in self.d_ae.items():

            for ele, energy, energy_ref in zipdic(d_ae_run_id, self.d_ae_ref):
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
                   "--with": ["MnCl"],
                   "--with_children": True}

    q = BigData(d_arguments=d_arguments, run_id_ref="1")
    print q.d_ae
    print q.d_ae_deviation
