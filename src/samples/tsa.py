import pyomo.environ as pe
from utils.properties import calc_c_p_solid
from utils.properties import molar_weight
from samples.separator import Separator

class TSA():
    """
    Temperature Swing Adsorption
    Must be combined with "Separator"

        stream_in:          Input stream, object of class 'stream'
        stream_prod:        Output stream, object of class 'stream'
        stream_bp:          Output stream, object of class 'stream'
    """
    def __init__(self, stream_in, stream_prod, stream_bp, zeta, k_prod, q, m_s, X_rich, X_lean):

        self.stream_in = stream_in
        self.stream_prod = stream_prod
        self.stream_bp = stream_bp
        self.zeta = zeta
        self.q = q
        self.k_prod = k_prod
        self.m_s = m_s  # Adsorbent mass flow [kg/s]
        self.X_rich = X_rich  # (mass) loading
        self.X_lean = X_lean  # (mass) loading
        self.t_ads = 50 + 273.15
        self.t_des = 250 + 273.15
        self.unit_block = pe.Block()
        self.set_constraints()
        self.unit_type = 'Temperature Swing Adsorption'
        self.unit_attributes = {'i_in': self.stream_in.i, 'i_prod': self.stream_prod.i, 'i_bp': self.stream_bp.i,
                                'k_prod': self.k_prod}

    def set_constraints(self):

        Separator(self.unit_block, self.stream_in, self.stream_prod, self.stream_bp, self.zeta, self.k_prod)

        self.unit_block.tsa_prod_rec_upper = pe.Constraint(expr=self.zeta <= 0.9)
        # self.unit_block.tsa_prod_rec_lower = pe.Constraint(expr=self.zeta >= 0.5)  # 13.07.2020

        self.unit_block.tsa_q = pe.Constraint(expr=0 == self.q - calc_c_p_solid('Zeolite') * self.m_s * 1000 * (self.t_des - self.t_ads))
        self.unit_block.tsa_mb = pe.Constraint(
            expr=self.stream_in.n * self.stream_in.y[self.k_prod] - self.stream_bp.n * self.stream_bp.y[self.k_prod] ==
                1 / molar_weight(self.k_prod) * self.m_s * 1000 * (self.X_rich - self.X_lean)
        )
        self.unit_block.tsa_x_rich = pe.Constraint(expr=self.X_rich == 0.02)
        self.unit_block.tsa_x_lean = pe.Constraint(expr=self.X_lean == 0.005)

        # Fixed temperatures for ad/desorption (Rabo et al.)
        self.unit_block.tsa_temp_in = pe.Constraint(expr=self.stream_in.t == self.t_ads)
        self.unit_block.tsa_temp_out = pe.Constraint(expr=self.stream_prod.t == self.t_des)

        self.unit_block.tsa_isobar = pe.Constraint(expr=self.stream_prod.p == self.stream_in.p)  # Isobaric process

        self.unit_block.tsa_prod_k = pe.ConstraintList()
        self.unit_block.tsa_prod_k.construct()

        for k in self.stream_in.substances:  # Product stream only contains target component
            if k != self.k_prod:
                self.unit_block.tsa_prod_k.add(expr=self.stream_prod.y[k] == 0)
