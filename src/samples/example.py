import pyomo.environ as pe
import pyomo.gdp as gdp

m = pe.ConcreteModel()

m.unit1 = gdp.Disjunct()
m.unit2 = gdp.Disjunct()

m.unit1.constraint = pe.Constraint()
m.unit2.constraint = pe.Constraint()

m.unit1_or_unit2 = gdp.Disjunction(expr=[m.unit1, m.unit2])


