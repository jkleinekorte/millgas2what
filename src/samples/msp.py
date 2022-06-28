import pyomo.environ as pe
from utils.properties import calc_alpha_msp
from samples.separator import Separator


class MSP():
    """
    Membrane Separation Process
    Must be combined with "Separator"
        stream_in:      Input stream, object of class 'stream'
        stream_prod:    Output stream, object of class 'stream'
        stream_ret:     Output stream, object of class 'stream'
    """

    def __init__(self, stream_in, stream_prod, stream_bp, zeta, k_prod):

        self.stream_in = stream_in
        self.stream_prod = stream_prod
        self.stream_ret = stream_bp
        self.zeta = zeta
        self.k_prod = k_prod
        self.unit_block = pe.Block()
        self.set_constraints()
        self.unit_type = 'Membrane Separation Process'
        self.unit_attributes = {'i_in': self.stream_in.i, 'i_prod': self.stream_prod.i, 'i_bp': self.stream_ret.i,
                                'k_prod': self.k_prod}


    def set_constraints(self):

        Separator(self.unit_block, self.stream_in, self.stream_prod, self.stream_ret, self.zeta, self.k_prod)

        self.unit_block.msp_p_lim_in = pe.Constraint(expr=self.stream_in.p <= 14)  # Pressure limit for membrane process
        self.unit_block.msp_p_lim_out = pe.Constraint(expr=self.stream_prod.p == 1)  # Pressure limit for membrane process
        self.unit_block.msp_func1 = pe.Constraint(expr=self.stream_in.p >= self.stream_prod.p)
        self.unit_block.msp_func2 = pe.Constraint(expr=self.zeta >= 0.1)  # Avoids the solution at n_prod = 0

        self.unit_block.msp_a18 = pe.Constraint(
            expr=self.stream_prod.p / self.stream_in.p == (self.stream_in.y[self.k_prod] / self.stream_prod.y[self.k_prod]) * (1 - self.zeta) / (
                    1 - self.stream_in.y[self.k_prod] * self.zeta))

        self.unit_block.msp_a20 = pe.ConstraintList()
        self.unit_block.msp_a20.construct()

        for k in self.stream_in.substances:
            if k != self.k_prod:
                if k != 'H2O':
                    self.unit_block.msp_a20.add(expr=self.stream_prod.n * self.stream_prod.y[k] == (
                            calc_alpha_msp(k, self.k_prod) * self.zeta * self.stream_in.y[k] * self.stream_in.n * self.stream_in.y[self.k_prod]) /
                            (self.stream_in.y[self.k_prod] * (2 - self.zeta - calc_alpha_msp(k, self.k_prod) * self.zeta
                            / (1 - self.stream_in.y[self.k_prod] * self.zeta)) - 2 *
                            self.stream_prod.y[self.k_prod] * self.stream_prod.p * (1 - calc_alpha_msp(k, self.k_prod)) / self.stream_in.p))

        self.unit_block.msp_t_prod = pe.Constraint(expr=self.stream_prod.t == self.stream_in.t)
