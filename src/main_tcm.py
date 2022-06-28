import pyomo.environ as pe
from lci import LifeCycleInventory
from utils.save_results import ResultManager
from utils.solve_model import Solver

lci = LifeCycleInventory('millgas2what')

lci.model = pe.ConcreteModel('millgas2what')

scale = 1000000000

'Ströme des Stahlwerks als Parameter'

lci.model.cog_steelMill = pe.Param(initialize=39700000000 / scale)  # in kg, scaled
lci.model.bfg_steelMill = pe.Param(initialize=1740550000000 / scale) # in kg, scaled
lci.model.electricity_steelMill = pe.Param(initialize=-2298568545000 / scale)
lci.model.heat_steelMill = pe.Param(initialize=-894991475000 / scale)


'Definition der Verbindungspunkte'

connect_list = ['Mill gas COG [kg]',  'Mill gas BFG/BOFG [kg]', 'Electricity [MJ]', 'Heat [MJ]']

connector_lp = {}
lci.model.connect_lp = pe.Var(connect_list, initialize=0, bounds=(-10000, 10000))

for c in connect_list:
    connector_lp[c] = lci.model.connect_lp[c]

'Gesamtbilanzen'

lci.model.cog_balance = pe.Constraint(expr=0 == - lci.model.cog_steelMill + lci.model.connect_lp['Mill gas COG [kg]'])
lci.model.bfg_balance = pe.Constraint(expr=0 == - lci.model.bfg_steelMill + lci.model.connect_lp['Mill gas BFG/BOFG [kg]'])
lci.model.electricity_balance = pe.Constraint(expr=0 == - lci.model.electricity_steelMill + lci.model.connect_lp['Electricity [MJ]'])
lci.model.heat_balance = pe.Constraint(expr=0 == - lci.model.heat_steelMill + lci.model.connect_lp['Heat [MJ]'])

'Ab hier wird das Modell mit der LCI-Klasse zusammengebaut'

lci.import_from_excel('Life Cycle Inventory_v19.xlsx', 'A-Matrix', 'End of life')
lci.set_up_lp(scale)
lci.import_connector(connector_lp)  # Durch deaktivieren dieser Zeile wird nur die Chem. Ind. betrachtet

# lci.activate_scenario('Electricity Today')
lci.activate_scenario('Electricity Best Case')
# lci.activate_scenario('Electricity user-defined', 0.1072)

lci.activate_scenario('Separation GDP')  # Schaltet alle linearen Prozesse für Hüttengastrennung aus

lci.activate_scenario('CCU high TRL only')
# lci.activate_scenario('No high TRL CCU')  # Durch aktivieren dieser Zeile werden die high TRL CCU-Prozesse deaktiviert und das konevntionelle Szenario erzeugt
lci.deactivate_process('CARBON DIOXIDE - ammonia plant')
lci.deactivate_process('Water gas shift reaction')
lci.lp.ammonia_constraint = pe.Constraint(expr=lci.lp.s['AMMONIA FROM NATURAL GAS BY STEAM REFORMING BY ICI "AMV" PROCESS incl CO2 capture'] - 228.9 <= 0)
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

results = ResultManager(lci)
