import pandas as pd
import pyomo.environ as pe
import numpy as np


def is_empty_cell(c):
    """ Tests if c refers to empty cell in excel file"""
    e = False
    if type(c) == np.float64:
        if c.astype(str) == 'nan':
            e = True
    if type(c) == float:
        if str(c) == 'nan':
            e = True
    return e


def len2(v):
    """ Returns len of v until first nan-entry"""
    i = 0
    while i < len(v) and not is_empty_cell(v[i]):
        i += 1
    return i


def df_to_list(A):
    """ Converts 1d-Matrix (pd.Dataframe) into simple list """
    if min(A.shape) != 1:
        raise Warning("Input matrix is not one-dimensional")

    m = max(A.shape)

    i = 0

    a_list = []

    while i < m:
        if A.shape[0] >= A.shape[1]:
            a = A.iloc[i, 0]
        elif A.shape[0] < A.shape[1]:
            a = A.iloc[0, i]
        a_list.append(a)
        i += 1
    return a_list


def replace_redundant_names(list):
    """ Searches list for recurrent string entries and re-names those strings """
    bad_names = {}
    clean_list = []
    i = 0
    while i < len(list):
        l = list[i]
        if l in clean_list:
            if l in bad_names.keys():
                bad_names[l] += 1
            else:
                bad_names[l] = 2
            l = l + ' (' + str(bad_names[l]) + ')'
        clean_list.append(l)
        i += 1
    return clean_list


def remove_apostrophes(list):
    clean_list = []
    i = 0
    while i < len(list):
        l = list[i].split("'")

        if len(l) == 1:
            clean_list.append(l[0])
        elif len(l) == 2:
            if len(l[0]) > len(l[1]):
                clean_list.append(l[0])
            else:
                clean_list.append(l[1])
        elif len(l) == 3:
            clean_list.append(l[1])

        i += 1
    return clean_list


def weighted_sum(par, var, ind):
    """
    par: iterable object (e.g. list)
    var: pe.Var
    ind: index list for var
    """

    ws = 0

    p = 0
    for q in ind:
        if par[p] != 0:
            ws += par[p] * var[q]
        p += 1


    return ws


def weighted_sum_positive(par, var, ind):
    """
    Only positive entries of par are considered
    par: iterable object (e.g. list)
    var: pe.Var
    ind: index list for var
    """

    ws = 0

    p = 0
    for q in ind:
        if par[p] > 0:
            ws += par[p] * var[q]
        p += 1


    return ws

class LifeCycleInventory:
    """

    """
    def __init__(self, name):
        self.name = name
        self.m = None
        self.n = None
        self.A = None
        self.p = None
        self.b = None
        self.v = None
        self.processes = []
        self.intermediate_flows = None
        self.lp = None
        self.connector = {}
        self.scale = None

        self.model = None
        self.objective = None
        self.solver_used = None
        self.solver_timer = 0

    def import_connector(self, connector):
        self.connector = connector

    def import_from_excel(self, filename, sheetname, sheetname2):

        xls = pd.ExcelFile(filename)
        data = xls.parse(sheetname)

        self.m = len2(df_to_list(data.iloc[14:, 2:3]))  # Number of intermediate flows / rows in A

        self.n = len2(df_to_list(data.iloc[2:3, 2:]))  # Number of processes / columns in A

        self.p = df_to_list(data.iloc[14:14 + self.m, 1:2])  # Production capacity vector

        self.A = data.iloc[14:14 + self.m, 2:2 + self.n]  # Technology matrix

        self.b = df_to_list(data.iloc[14 + self.m + 1:14 + self.m + 2, 2:2 + self.n])  # elementary flow vector

        self.processes = replace_redundant_names(remove_apostrophes(df_to_list(data.iloc[2:3, 2:2 + self.n])))

        self.intermediate_flows = remove_apostrophes(replace_redundant_names(df_to_list(data.iloc[14:14 + self.m, 0:1])))

        data_endoflife = xls.parse(sheetname2)

        self.v = df_to_list(data_endoflife.iloc[0:self.m, 11:12])  # End-of-life emissions vector

    def set_up_lp(self, scale):

        self.scale = scale
        self.lp = pe.Block()
        self.lp.s_set = pe.Set(initialize=self.processes)
        self.lp.y_set = pe.Set(initialize=self.intermediate_flows)
        self.lp.s_set.construct()
        self.lp.y_set.construct()
        ub = 10 ** 18 / scale
        self.lp.s = pe.Var(self.lp.s_set, initialize=0, bounds=(0, ub))
        self.lp.s.construct()
        self.lp.y = pe.Var(self.lp.y_set, initialize=0, bounds=(-ub, ub))  # Mill gas balance causes negative d
        self.lp.y.construct()

        self.lp.obj_cradle2gate = pe.Var(initialize=0, bounds=(-ub, ub))
        self.lp.obj_gate2grave = pe.Var(initialize=0, bounds=(-ub, ub))

    def construct_demand_constraints(self):

        self.lp.define_y = pe.ConstraintList()
        self.lp.define_y.construct()

        self.lp.demand_constraints = pe.ConstraintList()
        self.lp.demand_constraints.construct()

        self.lp.capacity_constraints1 = pe.ConstraintList()
        self.lp.capacity_constraints1.construct()

        self.lp.capacity_constraints2 = pe.ConstraintList()
        self.lp.capacity_constraints2.construct()

        u = 0
        while u < len(self.intermediate_flows):

            A_row = df_to_list(self.A.iloc[u:u + 1, :])

            connect = 0
            if self.intermediate_flows[u] in self.connector.keys():
                connect = self.connector[self.intermediate_flows[u]]

            self.lp.define_y.add(
                expr=weighted_sum(A_row, self.lp.s, self.processes) + connect - self.lp.y[self.intermediate_flows[u]] == 0)

            if self.p[u] > 0:
                'Set capacity constraints for chemical products. No connectors needed, as no chemical with specified prod. cap. is connected'
                self.lp.capacity_constraints1.add(
                    expr=weighted_sum_positive(A_row, self.lp.s, self.processes) + connect - self.p[u] / self.scale >= 0)

                self.lp.capacity_constraints2.add(
                    expr=self.lp.y[self.intermediate_flows[u]] >= 0)

            else:
                self.lp.demand_constraints.add(expr=self.lp.y[self.intermediate_flows[u]] == 0)

            u += 1

    def deactivate_process(self, process_name):
        try:
            type(self.lp.deactivated_processes)
        except AttributeError:
            self.lp.deactivated_processes = pe.ConstraintList()
            self.lp.deactivated_processes.construct()

        self.lp.deactivated_processes.add(expr=self.lp.s[process_name] == 0)

    def activate_scenario(self, name, e=0):
        """
        name: name of scenario
        e: additional input for scenario
        """
        if name == 'Electricity Today':
            self.deactivate_process('EU-28: Electricity from wind power ts')
            self.deactivate_process('Electricity, user-defined')
        elif name == 'Electricity user-defined':
            self.deactivate_process('EU-28: Electricity from grid mix (2020)')

            self.deactivate_process('EU-28: Electricity from wind power ts')


            self.b[self.processes.index('Electricity, user-defined')] = e
        elif name == 'Electricity Best Case':
            self.deactivate_process('EU-28: Electricity from grid mix (2020)')
            self.deactivate_process('Electricity, user-defined')
        elif name == 'Separation GDP':
            self.deactivate_process('GDP today')
            self.deactivate_process('GDP best case')
            self.deactivate_process('Trennung BFG I, Energieaufwand aus Aspen')
            self.deactivate_process('Trennung BFG II, Energieaufwand aus Aspen')
            self.deactivate_process('Trennung COG, Energieaufwand aus Aspen')
            self.deactivate_process('ideale Trennung BFG, ohne Energieaufwand,  Zusammensetzung aus background data')
            self.deactivate_process('ideale Trennung COG, ohne Energieaufwand, Zusammensetzung aus background data')
        elif name == 'Separation GDP linearized':
            self.deactivate_process('Trennung BFG I, Energieaufwand aus Aspen')
            self.deactivate_process('Trennung BFG II, Energieaufwand aus Aspen')
            self.deactivate_process('Trennung COG, Energieaufwand aus Aspen')
            self.deactivate_process('ideale Trennung BFG, ohne Energieaufwand,  Zusammensetzung aus background data')
            self.deactivate_process('ideale Trennung COG, ohne Energieaufwand, Zusammensetzung aus background data')
        elif name == 'CCU high TRL only':
            self.deactivate_process('Benzene from CO2 (SC)')
            self.deactivate_process('CO from CO2 (SC)')
            self.deactivate_process('Ethylene from CO2 via H2')
            self.deactivate_process('Ethylene oxide from CO2 (SC)')
            self.deactivate_process('Propylene from CO2 (SC)')
            self.deactivate_process('Styrene from CO2 (SC)')
            self.deactivate_process('Toluene from CO2 (SC)')
            self.deactivate_process('Xylene (ORTHO) from CO2 (SC)')
            self.deactivate_process('Xylene (PARA) from CO2 (SC)')
            self.deactivate_process('Ethylene from CO2 via CH4')
        elif name == 'No high TRL CCU':
            # self.deactivate_process('Ethylene from CO2 via CH4')
            i = 0
            while i < 28:
                self.deactivate_process(self.processes[i])
                i += 1
        else:
            raise Warning('Unknown scenario for LCI')
        return

    def construct_objective(self):

        self.lp.define_cradle2gate = pe.Constraint(expr=self.lp.obj_cradle2gate == weighted_sum(self.b, self.lp.s, self.processes))
        self.lp.define_gate2grave = pe.Constraint(expr=self.lp.obj_gate2grave == weighted_sum(self.v, self.lp.y, self.intermediate_flows))

        self.lp.objective = pe.Objective(expr=self.lp.obj_cradle2gate + self.lp.obj_gate2grave, sense=pe.minimize)

        self.objective = self.lp.objective
