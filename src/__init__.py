def zipdic(*dcts):
    for i in set(dcts[0]).intersection(*dcts[1:]):
        yield (i,) + tuple(d[i] for d in dcts)

def cond_sql_or(table_name, l_value, glob=True):
    # Create the OR condition for a WHERE filter
    
    operator = "GLOB" if glob else "=="
    
    str_template = '{table_name} {operator} "{value}"'
    str_l_value = [str_template.format(table_name=table_name,
                                       operator=operator,
                                       value=v) for v in l_value]

    return "(%s)" % " OR ".join(str_l_value)

def cond_sql_and(table_name, l_value, glob=True):
    # Create the OR condition for a WHERE filter

    l = []

    operator = "GLOB" if glob else "=="

    dmy = " AND ".join(['{0} {1} "{2}"'.format(table_name,operator,i) for i in l_value])
    if dmy:
        l.append("(%s)" % dmy)

    return l

def get_formula(ele):
    import re

    def s2i(str_):
        return int(str_) if str_ else 1

    l_formula_raw = re.findall(r'([A-Z][a-z]*)(\d*)', ele)
    l_formula_tuple = [(atome, s2i(char_number))
                       for atome, char_number in l_formula_raw]
    l_formula_flaten = [a for a, nb in l_formula_tuple for i in range(nb)]

    return l_formula_flaten
