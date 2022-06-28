import pyomo.environ as pe
from utils.properties import calc_enthalpy
from utils.reactions import calc_dHr, calc_k_key, calc_ny


class Reactor():
    """
    Reactor model (conversion based), up to two independent chemical reactions
    """

    def __init__(self, stream_in, stream_out, q, reaction1, conversion1, reaction2=0, conversion2=0):
        self.stream_in = stream_in
        self.stream_out = stream_out
        self.q = q

        self.reaction1 = reaction1
        self.conversion1 = conversion1
        self.k_key1 = calc_k_key(self.reaction1)

        self.reaction2 = reaction2

        self.unit_attributes = {'i_in': self.stream_in.i, 'i_out': self.stream_out.i, 'reaction 1': self.reaction1}

        if self.reaction2 != 0:
            self.unit_attributes['reaction 2'] = self.reaction2
            self.conversion2 = conversion2
            self.k_key2 = calc_k_key(self.reaction2)

        self.unit_block = pe.Block()
        self.set_constraints()
        self.unit_type = 'Reactor'

    def set_constraints(self):

        # Constraints independent from number and type of reactions

        # self.unit_block.react_p = pe.Constraint(expr=self.stream_out.p == self.stream_in.p)

        self.unit_block.react_cc = pe.Constraint(
            expr=1 == self.stream_out.y['CO'] + self.stream_out.y['CO2'] + self.stream_out.y['CH4'] + self.stream_out.y[
                'H2O'] + self.stream_out.y['H2'] + self.stream_out.y['O2'] + self.stream_out.y['N2'])

        self.unit_block.react_cb = pe.ConstraintList()
        self.unit_block.react_cb.construct()

        # Constraints dependent from number of reactions

        if self.reaction2 == 0:

            self.unit_block.react_mb = pe.Constraint(
                expr=self.stream_in.n * (1 + calc_ny(self.reaction1, 'sum') * self.conversion1 * self.stream_in.y[self.k_key1]) == self.stream_out.n)

            for k in self.stream_in.substances:
                if k != 'H2O':
                    self.unit_block.react_cb.add(
                        expr=self.stream_out.n * self.stream_out.y[k] == self.stream_in.n * self.stream_in.y[k] -
                             calc_ny(self.reaction1, k) / calc_ny(self.reaction1, self.k_key1) * self.conversion1 *
                             self.stream_in.n * self.stream_in.y[self.k_key1])

            self.unit_block.react_eb = pe.Constraint(
                expr=self.stream_in.n * calc_enthalpy(self.stream_in) - self.conversion1 * self.stream_in.n *
                     self.stream_in.y[self.k_key1] * calc_dHr(self.reaction1) + 0.7 * self.q == calc_enthalpy(
                    self.stream_out) * self.stream_out.n)

        else:

            self.unit_block.react_mb = pe.Constraint(expr=self.stream_in.n * (
                    1 + calc_ny(self.reaction1, 'sum') * self.conversion1 * self.stream_in.y[self.k_key1] + calc_ny(
                    self.reaction2, 'sum') * self.conversion2 * (self.stream_in.y[self.k_key2] - calc_ny(self.reaction1, self.k_key2) / calc_ny(self.reaction1, self.k_key1) * self.conversion1 * self.stream_in.y[self.k_key1])) == self.stream_out.n)

            self.unit_block.react_eb = pe.Constraint(expr=self.stream_in.n * (
                        calc_enthalpy(self.stream_in) - self.conversion1 * self.stream_in.y[self.k_key1] * calc_dHr(
                    self.reaction1) - self.conversion2 * (self.stream_in.y[self.k_key2] - calc_ny(self.reaction1, self.k_key2) / calc_ny(self.reaction1, self.k_key1) * self.conversion1 * self.stream_in.y[self.k_key1]) * calc_dHr(
                    self.reaction2)) == calc_enthalpy(self.stream_out) * self.stream_out.n)

            for k in self.stream_in.substances:
                if k != 'H2O':
                    self.unit_block.react_cb.add(expr=self.stream_out.n * self.stream_out.y[k] == self.stream_in.n * (
                                self.stream_in.y[k] - calc_ny(self.reaction1, k) / calc_ny(self.reaction1,
                                                                                           self.k_key1) * self.conversion1 *
                                self.stream_in.y[self.k_key1] - calc_ny(self.reaction2, k) / calc_ny(self.reaction2, self.k_key2) * self.conversion2 * (
                                self.stream_in.y[self.k_key2] - calc_ny(self.reaction1, self.k_key2) / calc_ny(self.reaction1, self.k_key1) * self.conversion1 * self.stream_in.y[self.k_key1])))

        # Constraints dependent from type of reaction

        if self.reaction1 == 'WGSR':
            # self.unit_block.react_t = pe.Constraint(expr=self.stream_in.t >= 200 + 273.15)
            self.unit_block.react_conversion1 = pe.Constraint(expr=self.conversion1 == 0.96)

            self.unit_block.react_t_in_lb = pe.Constraint(expr=self.stream_in.t >= 600)
            self.unit_block.react_t_in_ub = pe.Constraint(expr=self.stream_in.t <= 800)
            self.unit_block.react_t_out_lb = pe.Constraint(expr=self.stream_out.t >= 600)
            self.unit_block.react_t_out_ub = pe.Constraint(expr=self.stream_out.t <= 800)

        elif self.reaction1 == 'CDR':
            self.unit_block.react_t_in_lb = pe.Constraint(expr=self.stream_in.t >= 1143)
            self.unit_block.react_t_in_ub = pe.Constraint(expr=self.stream_in.t <= 1313)
            self.unit_block.react_t_out_lb = pe.Constraint(expr=self.stream_out.t >= 1143)
            self.unit_block.react_t_out_ub = pe.Constraint(expr=self.stream_out.t <= 1313)
            self.unit_block.react_p = pe.Constraint(expr=self.stream_out.p == 1)
            self.unit_block.react_conversion1 = pe.Constraint(expr=self.conversion1 == 0.9)

        elif self.reaction1 == 'POR':
            # self.unit_block.react_t = pe.Constraint(expr=self.stream_in.t == 1073)  # gdpopt returns error
            self.unit_block.react_t = pe.Constraint(expr=self.stream_in.t >= 1000)
            self.unit_block.react_q = pe.Constraint(expr=self.q == 0)
            self.unit_block.react_conversion1 = pe.Constraint(expr=self.conversion1 == 0.95)

        elif self.reaction1 == 'SMR' and self.reaction2 == 'WGSR':
            self.unit_block.react_t_in_lb = pe.Constraint(expr=self.stream_in.t >= 1153)
            self.unit_block.react_t_in_ub = pe.Constraint(expr=self.stream_in.t <= 1300)
            self.unit_block.react_t_out_lb = pe.Constraint(expr=self.stream_out.t >= 1153)
            self.unit_block.react_t_out_ub = pe.Constraint(expr=self.stream_out.t <= 1300)
            # self.unit_block.react_p_in = pe.Constraint(expr=self.stream_in.p == 20)
            self.unit_block.react_p_out = pe.Constraint(expr=self.stream_out.p == self.stream_in.p)
            self.unit_block.react_conversion1 = pe.Constraint(expr=self.conversion1 == 0.815)
            self.unit_block.react_conversion2 = pe.Constraint(expr=self.conversion2 == 0.402)
