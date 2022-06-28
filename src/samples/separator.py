import pyomo.environ as pe
from utils.utils import sum_rule

class Separator():
    """
    Adds some general separation unit constraints to a unit block
    """
    def __init__(self, block, stream_in, stream_prod, stream_bp, zeta, k_prod):
        self.zeta = zeta
        self.stream_in = stream_in
        self.stream_prod = stream_prod
        self.stream_bp = stream_bp
        self.k_prod = k_prod
        self.unit_block = block
        self.set_constraints()

    def set_constraints(self):

        self.unit_block.sep_mb = pe.Constraint(expr=self.stream_in.n == self.stream_prod.n + self.stream_bp.n)

        self.unit_block.sep_cb = pe.ConstraintList()
        self.unit_block.sep_cb.construct()

        for k in self.stream_in.substances:
            if k != 'H2O':
                self.unit_block.sep_cb.add(expr=self.stream_in.n * self.stream_in.y[k] == self.stream_prod.n * self.stream_prod.y[k] + self.stream_bp.n* self.stream_bp.y[k])

        self.unit_block.sep_prodrec = pe.Constraint(expr=self.stream_prod.n * self.stream_prod.y[self.k_prod] == self.zeta * self.stream_in.n * self.stream_in.y[self.k_prod])

        self.unit_block.sep_cc_prod = pe.Constraint(expr=1 == sum_rule(self.stream_prod.y, self.stream_in.substances))

        self.unit_block.sep_cc_bp = pe.Constraint(expr=1 == sum_rule(self.stream_bp.y, self.stream_in.substances))

        self.unit_block.sep_p_bp = pe.Constraint(expr=self.stream_in.p == self.stream_bp.p)
        self.unit_block.sep_t_bp = pe.Constraint(expr=self.stream_in.t == self.stream_bp.t)

