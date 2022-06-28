import pyomo.environ as pe
from utils.properties import calc_kappa, calc_enthalpy


class Compressor():
    """
    Compressor model
        stream_in:      Input stream, object of class 'stream'
        stream_out:     Output stream, object of class 'stream'
    """
    def __init__(self, stream_in, stream_out, w):
        self.w = w
        self.stream_in = stream_in
        self.stream_out = stream_out
        self.unit_block = pe.Block()
        self.set_constraints()
        self.unit_type = 'Compressor'
        self.unit_attributes = {'i_in': self.stream_in.i, 'i_out': self.stream_out.i}

    def set_constraints(self):
        self.unit_block.comp_istr = pe.Constraint(
                expr=self.stream_out.t / self.stream_in.t == (self.stream_out.p / self.stream_in.p) ** ((calc_kappa(self.stream_in) - 1) / calc_kappa(self.stream_in)))

        self.unit_block.comp_mb = pe.Constraint(
            expr=self.stream_out.n == self.stream_in.n)

        self.unit_block.comp_cb = pe.ConstraintList()
        self.unit_block.comp_cb.construct()

        for k in self.stream_in.substances:
            if k != 'H2O':
                self.unit_block.comp_cb.add(expr=self.stream_out.y[k] == self.stream_in.y[k])  # component balances

        self.unit_block.comp_eb = pe.Constraint(expr=self.w == (calc_enthalpy(self.stream_out) - calc_enthalpy(self.stream_in)) / 0.7 * self.stream_in.n)  # energy balance

        self.unit_block.comp_cc = pe.Constraint(expr=self.stream_out.y['H2O'] == 1 - self.stream_out.y['CO'] - self.stream_out.y['CO2']
                              - self.stream_out.y['H2'] - self.stream_out.y['O2'] - self.stream_out.y['N2'] - self.stream_out.y['CH4'])

