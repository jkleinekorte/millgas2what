import pyomo.environ as pe
from utils.utils import sum_rule


class Splitter():
    """
    Splits a stream
    """
    def __init__(self, stream_in, stream_prod, stream_bp, split):
        self.stream_in = stream_in
        self.stream_prod = stream_prod
        self.stream_bp = stream_bp
        self.split = split
        self.unit_block = pe.Block()
        self.set_constraints()
        self.unit_type = 'Splitter'
        self.unit_attributes = {'i_in': self.stream_in.i, 'i_prod': self.stream_prod.i, 'i_bp': self.stream_bp.i}

    def set_constraints(self):

        self.unit_block.split_p_prod = pe.Constraint(expr=self.stream_in.p == self.stream_prod.p)
        self.unit_block.split_t_prod = pe.Constraint(expr=self.stream_in.t == self.stream_prod.t)
        self.unit_block.split_p_bp = pe.Constraint(expr=self.stream_in.p == self.stream_bp.p)
        self.unit_block.split_t_bp = pe.Constraint(expr=self.stream_in.t == self.stream_bp.t)

        self.unit_block.split_split = pe.Constraint(expr=self.stream_in.n * self.split == self.stream_prod.n)
        self.unit_block.split_mb = pe.Constraint(expr=self.stream_in.n == self.stream_bp.n + self.stream_prod.n)

        self.unit_block.split_cb = pe.ConstraintList()
        self.unit_block.split_y = pe.ConstraintList()
        self.unit_block.split_cb.construct()
        self.unit_block.split_y.construct()

        for k in self.stream_in.substances:
            if k != 'H2O':
                self.unit_block.split_y.add(expr=self.stream_in.y[k] == self.stream_prod.y[k])
                self.unit_block.split_cb.add(expr=self.stream_in.y[k] == self.stream_bp.y[k])
                # self.unit_block.split_cb.add(expr=self.stream_in.n * self.stream_in.y[k] == self.stream_prod.n * self.stream_prod.y[k] + self.stream_bp.n * self.stream_bp.y[k])

        self.unit_block.split_cc_prod = pe.Constraint(
            expr=1 == sum_rule(self.stream_prod.y, self.stream_in.substances))

        self.unit_block.split_cc_bp = pe.Constraint(
            expr=1 == sum_rule(self.stream_bp.y, self.stream_in.substances))
