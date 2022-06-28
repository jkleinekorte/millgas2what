import pyomo.environ as pe
from utils.properties import calc_beta_psa
from samples.separator import Separator


class PSA():
    """
    Pressure Swing Adsorption
    Must be combined with "Separator"

        stream_in:          Input stream, object of class 'stream'
        stream_prod:        Output stream, object of class 'stream'
        stream_bp:          Output stream, object of class 'stream'

    """
    def __init__(self, stream_in, stream_prod, stream_bp, zeta, k_prod):
        self.stream_in = stream_in
        self.stream_prod = stream_prod
        self.stream_bp = stream_bp
        self.zeta = zeta
        self.k_prod = k_prod
        self.unit_block = pe.Block()
        self.set_constraints()

        self.unit_type = 'Pressure Swing Adsorption'
        self.unit_attributes = {'i_in': self.stream_in.i, 'i_prod': self.stream_prod.i, 'i_bp': self.stream_bp.i, 'k_prod': self.k_prod}


    def set_constraints(self):

        Separator(self.unit_block, self.stream_in, self.stream_prod, self.stream_bp, self.zeta, self.k_prod)

        self.unit_block.psa_p_lim = pe.Constraint(expr=self.stream_in.p <= 30)  # ?
        self.unit_block.psa_a23 = pe.Constraint(expr=self.stream_prod.p / self.stream_in.p == self.stream_in.y[self.k_prod] * (1 - self.zeta / (1 - calc_beta_psa(self.k_prod))))

        self.unit_block.psa_prod_k = pe.ConstraintList()
        self.unit_block.psa_prod_k.construct()

        for k in self.stream_in.substances:
            if k != self.k_prod:
                self.unit_block.psa_prod_k.add(expr=self.stream_prod.y[k] == 0)

        self.unit_block.psa_t_prod = pe.Constraint(expr=self.stream_prod.t == self.stream_in.t)