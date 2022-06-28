import pyomo.environ as pe
import time
from utils.save_results import clean_value
import pyomo.solvers


class Solver():
    """ Finalizes, transforms and/or solves the model"""

    def __init__(self):
        self.lci = None
        self.lci_model = None


    def solve_gdp(self, s):
        """
        Solves a gdp model without transformation, using gdpopt
        s: object of class superstructure
        """

        self.lci = s.lci
        self.lci_model = s.model.utilization

        s.solver_used = 'gdpopt (ipot/glpk)' #'gdpopt (ipot/cbc)'
        # s.solver_used = 'gdpopt (baron/gurobi)'
        start = time.time()
        tee = True
        pe.SolverFactory('gdpopt').solve(s.model,
                                         tee=tee,
                                         # time_limit=1000,
                                         nlp_solver='ipopt',
                                         # nlp_solver_args={'tol': 1E-5},
                                         constraint_tolerance=1E-10,
                                         mip_solver='glpk',
                                         #mip_solver='cbc',
                                         init_strategy='set_covering',
                                         # mip_solver = 'gurobi',
                                         # mip_solver_args={'timelimit': 1000}
                                         )


        # pe.SolverFactory('gdpbb').solve(s.model, solver='ipopt', tee=tee)
        end = time.time()
        s.solver_timer = end - start

    def solve_lp(self, lci, solver_name):
        """
        Solves linear tcm model
        """
        self.lci = lci
        self.lci_model = lci.lp
        start = time.time()

        if solver_name == 'glpk':
            pe.SolverFactory('glpk').solve(lci.model, tee=True, timelimit=1000)
            lci.solver_used = 'glpk'
        elif solver_name == 'gurobi':
            pe.SolverFactory('gurobi').solve(lci.model, tee=True)  # Wie gebe ich gurobi ein Zeitlimit vor?
            lci.solver_used = 'gurobi'
        else:
            raise SystemError('Unknown LP solver')

        # lp_solver = pe.SolverFactory('glpk')
        # lp_solver.options['tmlim'] = 1000
        # lp_solver.solve(lci.model, tee=True)

        end = time.time()
        lci.solver_timer = end - start
