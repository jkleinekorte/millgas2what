def calc_dHr(reaction):
    if reaction == 'WGSR':  # Water Gas Shift Reaction: CO + H2O = CO2 + H2
        dHr = -41.1  # kJ/mol
    elif reaction == 'SMR':  # Steam Methane Reaction: CH4 + H2O = CO + 3H2 (parallel to WGSR)
        dHr = 234.7  # kJ/mol
    elif reaction == 'CDR':  # Carbon Dioxide Reforming: CO2 + CH4 = 2CO + 2H2
        dHr = 247  # kJ/mol
    elif reaction == 'POR':  # Partial Oxidation Reaction: CH4 + 0.5O2 = CO + 2H2
        dHr = -35.9  # kJ/mol
    else:
        raise SystemError("Unknown chemical reaction")
    return dHr/1000  # MJ / mol


def calc_k_key(reaction):
    if reaction == 'WGSR':
        k_key = 'CO'
    elif reaction == 'SMR' or reaction == 'CDR' or reaction == 'POR':
        k_key = 'CH4'
    else:
        raise SystemError("Unknown chemical reaction")
    return k_key


def calc_ny(reaction, k):
    if reaction == 'WGSR':
        ny = {'CO': -1, 'CO2': 1, 'H2': 1, 'H2O': -1, 'O2': 0, 'N2': 0, 'CH4': 0, 'sum': 0}
    elif reaction == 'SMR':
        ny = {'CO': 1, 'CO2': 0, 'H2': 3, 'H2O': -1, 'O2': 0, 'N2': 0, 'CH4': -1, 'sum': 2}
    elif reaction == 'CDR':
        ny = {'CO': 2, 'CO2': -1, 'H2': 2, 'H2O': 0, 'O2': 0, 'N2': 0, 'CH4': -1, 'sum': 2}
    elif reaction == 'POR':
        ny = {'CO': 1, 'CO2': 0, 'H2': 2, 'H2O': 0, 'O2': -0.5, 'N2': 0, 'CH4': -1, 'sum': 1.5}
    else:
        raise SystemError("Unknown chemical reaction")
    return ny[k]