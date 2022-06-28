import pyomo.environ as pe

def sum_rule(var, k_set):
    """ Returns sum expression of pyomo objects over a set """
    s = 0
    for k in k_set:
        s = s + var[k]
    return s

def sum_rule_heat(var, k_set):
    """ Does not work! To be removed"""
    h = 0
    c = 0
    for k in k_set:
        if pe.value(var[k]) >= 0:
            h = h + var[k]
        else:
            c = c + var[k]
    return {'heating': h, 'cooling': c}

class Stream():

    def __init__(self, i_stream, n, t, p, y, substances):
        self.stream_type = 'Free'
        self.i = i_stream
        self.n = n        # molar flux in kmol
        self.t = t         # array of compositions, sorted in order of list "substances"
        self.p = p                # temperature in K, default = standard conditions
        self.substances = substances
        self.y = {}
        for k in self.substances:
            self.y[k] = y[self.i, k]
