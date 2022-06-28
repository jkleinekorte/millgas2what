import pyomo.environ as pe


def shomate_parameter(j, k, t):
    """
    j: Index of Parameter (1-7)
    k: Substance
    t: Temperature in 1000 K
    """
    shomate_param = {}
    shomate_param[1, 'CO'] = 25.56
    shomate_param[2, 'CO'] = 6.096
    shomate_param[3, 'CO'] = 4.05
    shomate_param[4, 'CO'] = -2.67
    shomate_param[5, 'CO'] = 0.131
    shomate_param[6, 'CO'] = -118
    shomate_param[7, 'CO'] = -110.52
    shomate_param[1, 'CO2'] = 24.99
    shomate_param[2, 'CO2'] = 55.19
    shomate_param[3, 'CO2'] = -33.69
    shomate_param[4, 'CO2'] = 7.95
    shomate_param[5, 'CO2'] = -0.14
    shomate_param[6, 'CO2'] = -403.61
    shomate_param[7, 'CO2'] = -393.52
    shomate_param[1, 'H2'] = 33.066
    shomate_param[2, 'H2'] = -11.363
    shomate_param[3, 'H2'] = 11.43
    shomate_param[4, 'H2'] = -2.77
    shomate_param[5, 'H2'] = -0.158
    shomate_param[6, 'H2'] = -9.98
    shomate_param[7, 'H2'] = 0
    if pe.value(t) < 0.7:
        shomate_param[1, 'O2'] = 31.32
        shomate_param[2, 'O2'] = -20.23
        shomate_param[3, 'O2'] = 57.86
        shomate_param[4, 'O2'] = -36.5
        shomate_param[5, 'O2'] = -0.0073
        shomate_param[6, 'O2'] = -8.903
        shomate_param[7, 'O2'] = 0
    else:
        shomate_param[1, 'O2'] = 30.032
        shomate_param[2, 'O2'] = 8.77
        shomate_param[3, 'O2'] = -3.988
        shomate_param[4, 'O2'] = 0.788
        shomate_param[5, 'O2'] = -0.741
        shomate_param[6, 'O2'] = -11.324
        shomate_param[7, 'O2'] = 0
    if pe.value(t) < 0.5:
        shomate_param[1, 'N2'] = 33.066
        shomate_param[2, 'N2'] = -11.363
        shomate_param[3, 'N2'] = 11.43
        shomate_param[4, 'N2'] = -2.77
        shomate_param[5, 'N2'] = -0.158
        shomate_param[6, 'N2'] = -9.98
        shomate_param[7, 'N2'] = 0
    else:
        shomate_param[1, 'N2'] = 19.505
        shomate_param[2, 'N2'] = 19.887
        shomate_param[3, 'N2'] = -8.598
        shomate_param[4, 'N2'] = 1.369
        shomate_param[5, 'N2'] = 0.527
        shomate_param[6, 'N2'] = -4.935
        shomate_param[7, 'N2'] = 0
    shomate_param[1, 'CH4'] = -0.703
    shomate_param[2, 'CH4'] = 108.477
    shomate_param[3, 'CH4'] = -42.521
    shomate_param[4, 'CH4'] = 5.862
    shomate_param[5, 'CH4'] = 0.678
    shomate_param[6, 'CH4'] = -76.843
    shomate_param[7, 'CH4'] = -74.873
    shomate_param[1, 'H2O'] = 30.092
    shomate_param[2, 'H2O'] = 6.8323
    shomate_param[3, 'H2O'] = 6.7934
    shomate_param[4, 'H2O'] = -2.5344
    shomate_param[5, 'H2O'] = 0.0843
    shomate_param[6, 'H2O'] = -250.88
    shomate_param[7, 'H2O'] = -241.82

    return shomate_param[j, k]


def calc_kappa(stream):
    t = stream.t / 1000
    c_p = 0
    for k in stream.substances:
        c_p = c_p + stream.y[k] * (
                    shomate_parameter(1, k, t) + shomate_parameter(2, k, t) * t + shomate_parameter(3, k, t)
                    * t ** 2 + shomate_parameter(4, k, t) * t ** 3 + shomate_parameter(5, k, t) * t ** (-2))
    kappa = c_p / (c_p - 8.314)
    return kappa


def calc_enthalpy(stream):
    t = stream.t / 1000
    h = 0
    for k in stream.substances:
        h = h + stream.y[k] * (
                    shomate_parameter(1, k, t) * t + shomate_parameter(2, k, t) * t ** 2 / 2 + shomate_parameter(3, k,
                                                                                                                 t)
                    * t ** 3 / 3 + shomate_parameter(4, k, t) * t ** 4 / 4 - shomate_parameter(5, k, t) / t +
                    shomate_parameter(6, k, t) - shomate_parameter(7, k, t))
    h /= 1000
    return h  # enthalpy in MJ/mol


def calc_beta_psa(k_prod):
    if k_prod == 'H2':
        beta = 0.02
    elif k_prod == 'CO2':
        beta = 0.024
    return beta


def calc_alpha_msp(k, k_prod):  # calculate relative permeability alpha(k/k_prod) for MSP
    if k_prod == 'H2':
        permeability = {'CO': 2.4, 'CH4': 2.3, 'CO2': 38, 'H2': 55 * 3, 'O2': 8.3, 'N2': 1.4, 'H2O': 1}
        alpha = permeability[k] / permeability[k_prod]
    if k_prod == 'CO2':
        # permeance_ratio = {'CO': 140/2, 'CH4': 200/2, 'H2': 175/2, 'O2': 200/2, 'N2': 160/2, 'H2O': 160/2}
        permeance_ratio = {'CO': 140, 'CH4': 200, 'H2': 175, 'O2': 200, 'N2': 160, 'H2O': 160}
        alpha = 1 / permeance_ratio[k]
    return alpha


def molar_weight(k):
    """ Returns the molar weight of a component or a set of mole fractions"""
    mw_comp = {'CO': 28, 'CO2': 44, 'H2O': 18, 'H2': 2, 'O2': 32, 'N2': 28, 'CH4': 16}
    if k == 'COG':
        k = {'CO': 0.042, 'CO2': 0.012, 'H2': 0.621, 'O2': 0, 'N2': 0.059, 'CH4': 0.225, 'H2O': 0.041}
    elif k == 'B(O)FG':
        k = {'CO': 0.25, 'CO2': 0.217, 'H2': 0.037, 'O2': 0, 'N2': 0.456, 'CH4': 0, 'H2O': 0.04}
    if type(k) == dict:
        mw = 0
        for c in k.keys():
            mw = mw + k[c] * mw_comp[c]
    elif type(k) == str:
        if k in mw_comp.keys():
            mw = mw_comp[k]
    return mw / 1000  # Molar weight in kg/mol


def calc_c_p_solid(k):  # Heat capacity in kJ / kg / K
    if k == 'Zeolite':
        c_p = 1 #0.32 * 4.19
        # c_p = 0.7  # pure silica (very optimistic)
    return c_p / 1000  # MJ / kg / K
