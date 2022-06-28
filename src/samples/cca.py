import pyomo.environ as pe
from utils.properties import molar_weight
from samples.separator import Separator

class CCA():
    """
    CO2 Chemical Absorption
    Must be combined with "Separator"
        m:              Model (for access to stream variables)
        sbm:            (Sub)-model, to which unit will belong
        initialize:     Must be "1" if unit is first of its class in current submodel
        n_sep:          Index of Separation Process
        i_in:           Index of input stream
        i_prod:         Index of product stream
        i_bp:           Index of by-product stream
    """
    def __init__(self, stream_in, stream_prod, stream_bp, zeta, k_prod, q):

        self.stream_in = stream_in
        self.stream_prod = stream_prod
        self.stream_bp = stream_bp
        self.zeta = zeta
        self.q = q
        self.k_prod = k_prod
        self.unit_block = pe.Block()

        self.set_constraints()

        self.unit_type = 'Chemical Absorption'
        self.unit_attributes = {'i_in': self.stream_in.i, 'i_prod': self.stream_prod.i, 'i_bp': self.stream_bp.i,
                                'k_prod': self.k_prod}

    def set_constraints(self):

        Separator(self.unit_block, self.stream_in, self.stream_prod, self.stream_bp, self.zeta, self.k_prod)

        self.unit_block.cca_heat = pe.Constraint(expr=self.q == 4200 / 1000 * self.stream_prod.n * molar_weight(self.k_prod))

        # Fixed temperature and pressure for ab/desorption
        self.unit_block.cca_temp_in = pe.Constraint(expr=self.stream_in.t == 40 + 273.15)
        self.unit_block.cca_temp_out = pe.Constraint(expr=self.stream_prod.t == 120 + 273.15)
        self.unit_block.cca_p_in = pe.Constraint(expr=self.stream_in.p == 1.5)
        self.unit_block.cca_p_prod = pe.Constraint(expr=self.stream_prod.p == self.stream_in.p)

        self.unit_block.cca_prod_k = pe.ConstraintList()
        self.unit_block.cca_prod_k.construct()

        for k in self.stream_in.substances:  # Product stream only contains target component
            if k != self.k_prod:
                self.unit_block.cca_prod_k.add(expr=self.stream_prod.y[k] == 0)

        self.unit_block.cca_prod_rec = pe.Constraint(expr=self.zeta <= 0.9)
