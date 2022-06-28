import pyomo.environ as pe
from utils.properties import calc_enthalpy

class Mixer():
    def __init__(self, stream_in_1, stream_in_2, stream_out):
        self.stream_in_1 = stream_in_1
        self.stream_in_2 = stream_in_2
        self.stream_out = stream_out
        self.unit_block = pe.Block()
        self.set_constraints()
        self.unit_type = 'Mixer'
        self.unit_attributes = {'i_in_1': self.stream_in_1.i, 'i_in_2': self.stream_in_2.i, 'i_out': self.stream_out.i}

    def set_constraints(self):
        self.unit_block.mix_mb = pe.Constraint(expr=self.stream_out.n == self.stream_in_1.n + self.stream_in_2.n)

        self.unit_block.mix_cb = pe.ConstraintList()
        self.unit_block.mix_cb.construct()

        for k in self.stream_in_1.substances:
            if k != 'H2O':
                self.unit_block.mix_cb.add(expr=self.stream_out.y[k] * self.stream_out.n == self.stream_in_1.y[k] * self.stream_in_1.n + self.stream_in_2.y[k] * self.stream_in_2.n)  # component balances

        self.unit_block.mix_eb = pe.Constraint(expr=calc_enthalpy(self.stream_out) * self.stream_out.n == calc_enthalpy(self.stream_in_1) * self.stream_in_1.n + calc_enthalpy(self.stream_in_2) * self.stream_in_2.n)  # energy balance

        self.unit_block.mix_cc = pe.Constraint(expr=self.stream_out.y['H2O'] == 1 - self.stream_out.y['CO'] - self.stream_out.y['CO2']
                              - self.stream_out.y['H2'] - self.stream_out.y['O2'] - self.stream_out.y['N2'] - self.stream_out.y['CH4'])

        if pe.value(self.stream_in_1.p) >= pe.value(self.stream_in_2.p):
            self.unit_block.mix_p = pe.Constraint(expr=self.stream_in_2.p == self.stream_out.p)
        else:
            self.unit_block.mix_p = pe.Constraint(expr=self.stream_in_1.p == self.stream_out.p)
