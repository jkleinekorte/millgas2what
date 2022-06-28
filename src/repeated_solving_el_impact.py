import pyomo.environ as pe
from lci import LifeCycleInventory
from superstructure import Superstructure
from utils.properties import molar_weight
from utils.utils import sum_rule
from utils.save_results import ResultManager
from utils.solve_model import Solver
import time as time
import pickle


def range_len(start, stop, len):
    step = (stop - start) / (len - 1)
    list = []
    i = start
    while i < stop:
        list.append(i)
        i += step
    list.append(stop)
    return list


def rep_solve_tcm(x):
    lci = LifeCycleInventory('millgas2what')

    lci.model = pe.ConcreteModel('millgas2what')

    scale = 1000000000

    'Ströme des Stahlwerks als Parameter'

    lci.model.cog_steelMill = pe.Param(initialize=39700000000 / scale)  # in kg, scaled
    lci.model.bfg_steelMill = pe.Param(initialize=1740550000000 / scale)  # in kg, scaled
    lci.model.electricity_steelMill = pe.Param(initialize=-2298568545000 / scale)
    lci.model.heat_steelMill = pe.Param(initialize=-894991475000 / scale)

    'Definition der Verbindungspunkte'

    connect_list = ['Mill gas COG [kg]', 'Mill gas BFG/BOFG [kg]', 'Electricity [MJ]', 'Heat [MJ]']

    connector_lp = {}
    lci.model.connect_lp = pe.Var(connect_list, initialize=0, bounds=(-10000, 10000))

    for c in connect_list:
        connector_lp[c] = lci.model.connect_lp[c]

    'Gesamtbilanzen'

    lci.model.cog_balance = pe.Constraint(
        expr=0 == - lci.model.cog_steelMill + lci.model.connect_lp['Mill gas COG [kg]'])
    lci.model.bfg_balance = pe.Constraint(
        expr=0 == - lci.model.bfg_steelMill + lci.model.connect_lp['Mill gas BFG/BOFG [kg]'])
    lci.model.electricity_balance = pe.Constraint(
        expr=0 == - lci.model.electricity_steelMill + lci.model.connect_lp['Electricity [MJ]'])
    lci.model.heat_balance = pe.Constraint(expr=0 == - lci.model.heat_steelMill + lci.model.connect_lp['Heat [MJ]'])

    'Ab hier wird das Modell mit der LCI-Klasse zusammengebaut'

    lci.import_from_excel('Life Cycle Inventory_v19.xlsx', 'A-Matrix', 'End of life')
    lci.set_up_lp(scale)
    lci.import_connector(connector_lp)  # Durch deaktivieren dieser Zeile wird nur die Chem. Ind. betrachtet

    # lci.activate_scenario('Electricity Today')
    # lci.activate_scenario('Electricity Best Case')
    lci.activate_scenario('Electricity user-defined', x)

    lci.activate_scenario('Separation GDP')  # Schaltet alle linearen Prozesse für Hüttengastrennung aus

    # lci.deactivate_process('CARBON DIOXIDE as emission to air')

    # lci.deactivate_process('AMMONIA FROM NATURAL GAS BY STEAM REFORMING BY ICI "AMV" PROCESS incl CO2 capture')

    lci.activate_scenario('CCU high TRL only')
    # lci.activate_scenario('No high TRL CCU')
    lci.deactivate_process('CARBON DIOXIDE - ammonia plant')
    lci.deactivate_process('Water gas shift reaction')
    lci.lp.ammonia_constraint = pe.Constraint(
        expr=lci.lp.s['AMMONIA FROM NATURAL GAS BY STEAM REFORMING BY ICI "AMV" PROCESS incl CO2 capture'] - 228.9 <= 0)
    lci.deactivate_process('TDI - neue Route_v2 exklusive Methylformate production')
    lci.deactivate_process('Polycarbonate - neue Route')
    lci.deactivate_process('Methylformate productionaus TDI neue Route v2')

    lci.construct_demand_constraints()
    lci.construct_objective()

    lci.model.add_component('lp', lci.lp)

    'Lösen und Ergebnisse darstellen'

    # lci.model.pprint()

    solver = Solver()
    solver.solve_lp(lci, 'glpk')
    # solver.test_feasibility() # Muss an neue Demand-Constraints angepasst werden

    results = {'x': x, 'z': pe.value(lci.objective) * lci.scale}

    return results


def rep_solve_gdp(x):
    """ Separation System / Flowsheet construction """

    # COG Separation

    s = Superstructure("Combined Model")

    s.initial_stream(31, 0, 300, 1, 'COG')
    s.create_unit('Compressor', 'C3', 31, 32)
    s.create_unit('PSA', 'PSA3', 32, 33, 34, 'H2')

    s.create_unit('Splitter', 'S5', 34, 35, 36)

    s.create_streams(37)
    s.model.p_35 = pe.Constraint(expr=s.model.p[37] == 1)
    s.model.t_35 = pe.Constraint(expr=s.model.t[37] == 300)
    s.model.cc_35 = pe.Constraint(expr=1 == sum_rule(s.streams[37].y, s.streams[37].substances))

    s.mix_streams('M3', 36, 37, 38)

    s.create_unit('Heat Exchanger', 'HE5', 38, 39)

    s.create_disjunct_reactor('methane_reforming', 'por', 'R2_POR', 39, 40, 'POR')
    s.create_disjunct_reactor('methane_reforming', 'cdr', 'R2_CDR', 39, 40, 'CDR')

    s.model.cdr.y_37 = pe.Constraint(expr=s.model.y[37, 'CO2'] == 1)
    s.model.cdr.add = pe.Constraint(expr=s.model.n[37] == 1 * s.model.n[36] * s.model.y[36, 'CH4'])
    s.model.cdr.q_constr = pe.Constraint(expr=s.model.q['R2_POR'] == 0)

    s.model.por.y_37 = pe.Constraint(expr=s.model.y[37, 'O2'] == 1)
    s.model.por.add = pe.Constraint(expr=s.model.n[37] == 0.48 * s.model.n[36] * s.model.y[36, 'CH4'])
    s.model.por.q_constr = pe.Constraint(expr=s.model.q['R2_CDR'] == 0)

    # B(O)FG Separation

    s.initial_stream(1, 0, 300, 1, 'B(O)FG')

    s.create_unit('Heat Exchanger', 'HE1', 1, 2)

    s.create_unit('TSA', 'TSA1', 2, 3, 4, 'CO')

    s.create_unit('Splitter', 'S1', 3, 20, 21)

    s.initial_stream(22, 0, 400, 1, {'H2O': 1})
    s.model.add_h2o = pe.Constraint(expr=s.model.n[22] == s.model.n[21])

    s.mix_streams('M1', 21, 22, 23)

    s.create_unit('Heat Exchanger', 'HE3', 23, 24)

    s.create_reactor('R1', 24, 25, 'WGSR')

    s.mix_streams('M2', 25, 4, 5)

    s.create_unit('Heat Exchanger', 'HE4', 5, 6)

    s.create_unit('Compressor', 'C1', 6, 7)

    s.create_disjunct_unit('co2_bofg', 'cca_1', 'CCA', 'CCA1', 7, 8, 9, 'CO2')
    s.create_disjunct_unit('co2_bofg', 'psa_1', 'PSA', 'PSA1', 7, 8, 9, 'CO2')
    s.model.psa_1.q_cca = pe.Constraint(expr=s.model.q['CCA1'] == 0)
    s.model.psa_1.t6_constraint = pe.Constraint(expr=s.model.t[6] >= 273.15 + 30)

    # s.model.t6_constraint = pe.Constraint(expr=s.model.t[6] >= 273.15 + 30)
    # s.create_unit('PSA', 'PSA1', 7, 8, 9, 'CO2')

    # s.create_unit('CCA', 'CCA1', 7, 8, 9, 'CO2')

    s.create_unit('Compressor', 'C2', 9, 10)

    s.create_unit('PSA', 'PSA2', 10, 11, 12, 'H2')

    scale = 1000000000

    'Ströme des Stahlwerks als Parameter'

    s.model.cog_steelMill = pe.Param(initialize=39700000000 / scale)  # in kg, scaled
    s.model.bfg_steelMill = pe.Param(initialize=1740550000000 / scale)  # in kg, scaled

    s.model.electricity_steelMill = pe.Param(initialize=-2298568545000 / scale)
    s.model.heat_steelMill = pe.Param(initialize=-894991475000 / scale)

    s.connect_list = ['Mill gas COG [kg]', 'Hydrogen (H2) [kg]', 'Electricity [MJ]', 'Heat [MJ]', 'SYNTHESIS GAS (1:1)',
                      'SYNTHESIS GAS (2:1)', 'Carbon dioxide (CO2) [kg]', 'Methane (CH4) [kg]', 'Oxygen (O2) [kg]',
                      'Mill gas BFG/BOFG [kg]', 'Carbon monoxide (CO) [kg]', 'CO2 to atm [kg]', 'STEAM [kg]'
                      ]

    connector_lp = {}
    s.model.connect_lp = pe.Var(s.connect_list, initialize=0, bounds=(-10000, 10000))

    for c in s.connect_list:
        connector_lp[c] = s.model.connect_lp[c]

    # Hier kann eingestellt werden, welcher Anteil der Hüttengase verwertet werden darf
    # x = 0.0001  # ACHTUNG! x = 0 führt zu infeasible
    # s.model.force_cog = pe.Constraint(expr=s.model.n[31] <= x * s.model.cog_steelMill / molar_weight('COG'))
    # s.model.force_bfg = pe.Constraint(expr=s.model.n[1] <= x * s.model.bfg_steelMill / molar_weight('B(O)FG'))

    s.model.cog_balance = pe.Constraint(
        expr=0 == - s.model.cog_steelMill + s.model.connect_lp['Mill gas COG [kg]'] + s.model.n[31] * molar_weight(
            'COG'))
    s.model.bfg_balance = pe.Constraint(
        expr=0 == - s.model.bfg_steelMill + s.model.connect_lp['Mill gas BFG/BOFG [kg]'] + s.model.n[1] * molar_weight(
            'B(O)FG'))
    s.model.el_balance = pe.Constraint(expr=0 == - s.model.connect_lp['Electricity [MJ]'] - sum_rule(s.model.w,
                                                                                                     s.model.workSet) + s.model.electricity_steelMill)
    s.model.heat_balance = pe.Constraint(
        expr=0 == - s.model.connect_lp['Heat [MJ]'] - sum_rule(s.model.q, s.model.heatSet) + s.model.heat_steelMill)
    s.model.co2_atm_balance = pe.Constraint(
        expr=0 == s.model.connect_lp['CO2 to atm [kg]'] - s.model.n[12] * molar_weight('CO2') * (
                s.model.y[12, 'CO2'] + s.model.y[12, 'CO']))
    # s.model.co2_atm_balance = pe.Constraint(expr=0 == s.model.connect_lp['CO2 to atm [kg]'] - s.model.n[12] * molar_weight('CO2') * (s.model.y[12, 'CO2'] + s.model.y[12, 'CO']) * 0.05)
    # s.model.co2_atm_balance = pe.Constraint(expr=0 == s.model.connect_lp['CO2 to atm [kg]'])
    s.model.steam_balance = pe.Constraint(
        expr=0 == s.model.connect_lp['STEAM [kg]'] + s.model.n[22] * molar_weight('H2O'))
    s.model.co_balance = pe.Constraint(
        expr=0 == s.model.connect_lp['Carbon monoxide (CO) [kg]'] - s.model.n[20] * molar_weight('CO'))
    s.model.ch4_balance = pe.Constraint(
        expr=s.model.connect_lp['Methane (CH4) [kg]'] == s.model.n[35] * s.model.y[35, 'CH4'] * molar_weight('CH4'))
    s.model.h2_balance = pe.Constraint(
        expr=s.model.connect_lp['Hydrogen (H2) [kg]'] == s.model.n[33] * molar_weight('H2') + s.model.n[
            11] * molar_weight('H2'))

    # s.model.cdr.syngas11_balance = pe.Constraint(expr=s.model.connect_lp['SYNTHESIS GAS (1:1)'] == s.model.n[40] * molar_weight({'H2': 0.5, 'CO': 0.5}))  # N2 wird als SynGas angenommen
    s.model.cdr.syngas11_balance = pe.Constraint(expr=s.model.connect_lp['SYNTHESIS GAS (1:1)'] == s.model.n[40] * (
                s.model.y[40, 'H2'] * molar_weight('H2') + s.model.y[40, 'CO'] * molar_weight('CO')))
    s.model.por.syngas11_balance = pe.Constraint(expr=s.model.connect_lp['SYNTHESIS GAS (1:1)'] == 0)

    # s.model.por.syngas21_balance = pe.Constraint(expr=s.model.connect_lp['SYNTHESIS GAS (2:1)'] == s.model.n[40] * molar_weight({'H2': 0.67, 'CO': 0.33}))  # N2 wird als SynGas angenommen
    s.model.por.syngas21_balance = pe.Constraint(expr=s.model.connect_lp['SYNTHESIS GAS (2:1)'] == s.model.n[40] * (
                s.model.y[40, 'H2'] * molar_weight('H2') + s.model.y[40, 'CO'] * molar_weight('CO')))
    s.model.cdr.syngas21_balance = pe.Constraint(expr=s.model.connect_lp['SYNTHESIS GAS (2:1)'] == 0)

    s.model.cdr.co2_balance = pe.Constraint(
        expr=s.model.connect_lp['Carbon dioxide (CO2) [kg]'] == - s.model.n[37] * molar_weight('CO2') + s.model.n[
            8] * molar_weight('CO2'))
    s.model.por.co2_balance = pe.Constraint(
        expr=s.model.connect_lp['Carbon dioxide (CO2) [kg]'] == s.model.n[8] * molar_weight('CO2'))
    # s.model.cdr.co2_balance = pe.Constraint(expr=s.model.connect_lp['Carbon dioxide (CO2) [kg]'] == 0)
    # s.model.por.co2_balance = pe.Constraint(expr=s.model.connect_lp['Carbon dioxide (CO2) [kg]'] == 0)
    s.model.por.o2_balance = pe.Constraint(
        expr=s.model.connect_lp['Oxygen (O2) [kg]'] == - s.model.n[37] * molar_weight('O2'))
    s.model.cdr.o2_balance = pe.Constraint(expr=s.model.connect_lp['Oxygen (O2) [kg]'] == 0)

    # s.model.no_co2_sep = pe.Constraint(expr=s.model.n[8] * molar_weight('CO2') == 147)
    # s.model.no_h2_sep = pe.Constraint(expr=s.model.n[11] == 0)

    """ Set up TCM """

    lci = LifeCycleInventory('millgas2what')

    lci.import_from_excel('Life Cycle Inventory_v19.xlsx', 'A-Matrix', 'End of life')
    lci.set_up_lp(scale)
    lci.import_connector(connector_lp)  # Durch deaktivieren dieser Zeile wird nur die Chem. Ind. betrachtet

    # lci.activate_scenario('Electricity Today')
    # lci.activate_scenario('Electricity Best Case')
    lci.activate_scenario('Electricity user-defined', x)

    lci.activate_scenario('Separation GDP')  # Schaltet alle linearen Prozesse für Hüttengastrennung aus

    # lci.deactivate_process('CARBON DIOXIDE as emission to air')

    # lci.deactivate_process('AMMONIA FROM NATURAL GAS BY STEAM REFORMING BY ICI "AMV" PROCESS incl CO2 capture')

    lci.activate_scenario('CCU high TRL only')
    lci.deactivate_process('CARBON DIOXIDE - ammonia plant')
    lci.deactivate_process('Water gas shift reaction')
    lci.lp.ammonia_constraint = pe.Constraint(
        expr=lci.lp.s['AMMONIA FROM NATURAL GAS BY STEAM REFORMING BY ICI "AMV" PROCESS incl CO2 capture'] - 228.9 <= 0)
    lci.deactivate_process('TDI - neue Route_v2 exklusive Methylformate production')
    lci.deactivate_process('Polycarbonate - neue Route')
    lci.deactivate_process('Methylformate productionaus TDI neue Route v2')

    lci.construct_demand_constraints()
    lci.construct_objective()

    s.import_lci(lci)

    s.create_disjunctions()

    """ Solve overall model """

    solver = Solver()

    """ Save values in dict"""

    ind_var = {}
    c_val = {}
    rec_val = {}
    heat_val = {}
    el_val = {}
    s_dict = {}
    cog_dict = {}
    bfg_dict = {}

    # LCI-Prozesse, die verfolgt werden sollen
    s_dict_list = ['CARBON DIOXIDE as emission to air', 'INC Carbon monoxide',
                   'treatment of blast furnace gas, in power plant, DE', 'Verbrennung COG in BHKW',
                   'AMMONIA FROM NATURAL GAS BY STEAM REFORMING BY ICI "AMV" PROCESS incl CO2 capture',
                   'CARBON DIOXIDE - air capture', 'Electricity, user-defined']

    try:
        solver.solve_gdp(s)
        obj = pe.value(s.objective)
        for d in s.disjuncts.keys():
            ind_var[d] = pe.value(s.disjuncts[d].indicator_var)
        for c in s.connect_list:
            c_val[c] = pe.value(connector_lp[c]) * lci.scale
        for c in s.model.zetaSet:
            rec_val[c] = pe.value(s.model.zeta[c])
        for c in s.model.heatSet:
            heat_val[c] = pe.value(s.model.q[c]) * lci.scale
        for c in s.model.workSet:
            el_val[c] = pe.value(s.model.w[c]) * lci.scale
        for i in s_dict_list:
            s_dict[i] = pe.value(s.model.utilization.s[i]) * lci.scale
        'Diagramme für COG / B(O)FG'
        cog_dict['H2'] = pe.value(s.model.n[33]) * molar_weight({'H2': 1}) * lci.scale
        cog_dict['N2'] = pe.value(s.model.n[35]) * pe.value(s.model.y[35, 'N2']) * molar_weight({'N2': 1}) * lci.scale

        bfg_dict['H2'] = pe.value(s.model.n[11]) * molar_weight({'H2': 1}) * lci.scale
        cog_dict['N2'] = pe.value(s.model.n[12]) * pe.value(s.model.y[12, 'N2']) * molar_weight({'N2': 1}) * lci.scale
        bfg_dict['CO2'] = pe.value(s.model.n[8]) * molar_weight({'CO2': 1}) * lci.scale

    except ValueError:
        obj = 0

    return {'x': x, 'z': obj * lci.scale, 'i': ind_var, 'c': c_val, 'rec': rec_val, 'q': heat_val, 'w': el_val,
            's': s_dict, 'cog': cog_dict, 'bfg': bfg_dict}


x_vector = range_len(0.002, 0.2, 30)

results_tcm = {}
results_gdp = {}

n = 0
while n < len(x_vector):
    results_tcm[n] = rep_solve_tcm(x_vector[n])
    print('TCM solved', n + 1)
    results_gdp[n] = rep_solve_gdp(x_vector[n])
    print('GDP solved', n + 1)
    n += 1

results = {'tcm': results_tcm, 'gdp': results_gdp}


def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


# name = input("enter file name")
save_object(results, '20200825_v19_tcm')
