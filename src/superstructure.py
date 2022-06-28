import pyomo.environ as pe
import pyomo.gdp as gdp
from samples.compressor import Compressor
from samples.heatExchanger import HeatExchanger
from samples.separator import Separator
from samples.psa import PSA
from samples.tsa import TSA
from samples.msp import MSP
from samples.reactor import Reactor
from samples.mixer import Mixer
from samples.cca import CCA
from samples.splitter import Splitter
from utils.utils import Stream, sum_rule, sum_rule_heat
from utils.properties import molar_weight


class Superstructure():
    """
    This class sets up an flowsheet superstructure optimization problem
    """
    def __init__(self, name):
        """ Creates (concrete) pyomo Model"""
        self.name = name
        self.solver_used = None
        self.model = pe.ConcreteModel(name)
        self.setupSets()
        self.setupVariables()
        self.define_impacts()
        self.connect_list = None
        self.lci = None
        self.objective = None
        self.solver_timer = 0

    def import_lci(self, lci):
        self.lci = lci
        self.model.add_component('utilization', lci.lp)  # Add LP block to overall model
        self.objective = self.model.utilization.objective

    def define_impacts(self):
        """
        Defines impacts, required for separation-only objective function
        """
        self.model.impact_electricity = pe.Param(initialize=0.1072 / 1000)  # kg CO2 / kJ (grid mix 2020)
        # self.model.impact_electricity = pe.Param(initialize=0.002683 / 1000)  # kg CO2 / kJ (wind)
        self.model.impact_heat = pe.Param(initialize=0.0686 / 1000)  # kg CO2 / kJ (heat from NG)
        self.model.impact_co = pe.Param(initialize=0.579)  # kg CO2 / kg CO (conv CO prod)
        self.model.impact_h2 = pe.Param(initialize=10.8)  # kg CO2 / kg H2 (conv H2 prod)
        self.model.impact_co2 = pe.Param(initialize=1)  # kg CO2 / kg CO2
        self.model.impact_o2 = pe.Param(initialize=0.144)  # kg CO2 / kg O2
        self.model.impact_syngas_21 = pe.Param(initialize=1.9540)  # kg CO2 / kg SynGas
        self.model.impact_steam = pe.Param(initialize=0.237)  # kg CO2 / kg Steam

    def setupSets(self):
        """ Creates index sets required for variables """
        self.streams = {}  # Library for objects of class 'stream'
        self.units = {}  # Library for objects of units

        self.disjuncts = {}  # 04.06.2020 Added libraries for gdp
        self.disjunctions = {}
        self.disjunction_sets = {}

        self.model.streamSet = pe.Set()  # Indices: streams

        self.model.workSet = pe.Set()  # Indices: work

        self.model.heatSet = pe.Set()  # Indices: heat

        self.model.zetaSet = pe.Set()  # Indices: product recovery

        self.model.conversionSet = pe.Set()  # Indices: conversion

        self.model.splitSet = pe.Set()  # Indices: split ratio

        self.model.sorpSet = pe.Set()  # Indices: Ad or Absorption processes

        self.model.substances = pe.Set(initialize=['CO', 'CO2', 'H2', 'O2', 'N2', 'CH4', 'H2O'])

        self.model.subst_set = self.model.streamSet * self.model.substances


    def setupVariables(self):
        """ Initializes flowsheet variables, based on index sets """

        'Stream variables'

        self.model.p = pe.Var(self.model.streamSet, initialize=1, bounds=(1, 50))  # pressure in bar

        self.model.t = pe.Var(self.model.streamSet, initialize=300, bounds=(200, 2000))  # temperature in kelvin

        self.model.n = pe.Var(self.model.streamSet, initialize=10000, bounds=(0, 70000))  # flow rate in mol/s

        self.model.y = pe.Var(self.model.subst_set, initialize=0, bounds=(0, 1))  # mole fractions


        'Unit variables'
        self.model.w = pe.Var(self.model.workSet, initialize=0, bounds=(0, 2000))  # work in kW

        self.model.q = pe.Var(self.model.heatSet, initialize=0, bounds=(-5000, 10000))  # heat in kW

        self.model.zeta = pe.Var(self.model.zetaSet, initialize=0, bounds=(0, 1))  # product recovery

        self.model.conversion = pe.Var(self.model.conversionSet, initialize=0, bounds=(0, 1))  # reactor conversion

        self.model.split = pe.Var(self.model.splitSet, initialize=0, bounds=(0, 1))  # split ratio

        self.model.m_s = pe.Var(self.model.sorpSet, initialize=0, bounds=(0, 100))

        self.model.X_rich = pe.Var(self.model.sorpSet, initialize=0, bounds=(0, 10))

        self.model.X_lean = pe.Var(self.model.sorpSet, initialize=0, bounds=(0, 10))


    def create_streams(self, i_1, i_2=0, i_3=0):
        """ Creates required streams (up to three), if they do not exist already """
        if i_1 not in self.model.streamSet:  # Check if i_in exists as stream index
            self.model.streamSet.add(i_1)
            self.streams[i_1] = Stream(i_1, self.model.n[i_1], self.model.t[i_1], self.model.p[i_1], self.model.y, self.model.substances)
        if i_2 != 0 and i_2 not in self.model.streamSet:
            self.model.streamSet.add(i_2)  # Check if i_prod exists as stream index
            self.streams[i_2] = Stream(i_2, self.model.n[i_2], self.model.t[i_2], self.model.p[i_2], self.model.y, self.model.substances)
        if i_3 != 0 and i_3 not in self.model.streamSet:  # Check if i_bp is required and exists as stream index
            self.model.streamSet.add(i_3)
            self.streams[i_3] = Stream(i_3, self.model.n[i_3], self.model.t[i_3], self.model.p[i_3], self.model.y, self.model.substances)

    def initial_stream(self, i, n, t, p, y):
        """
        Sets up initial stream with index i
        n:  molar flow rate [mol/s], if n=0 optimization DoF
        t:  temperature [Kelvin]
        p:  pressure [bar]
        y:  mole fractions [-]
        y can either be a string to call a pre-defined set of mole fractions ('COG')
        or a dictionary with individual mole fractions for each substance
        """

        self.create_streams(i)

        try:
            type(self.model.initial_p)

        except AttributeError:
            self.model.initial_n = pe.ConstraintList()
            self.model.initial_t = pe.ConstraintList()
            self.model.initial_p = pe.ConstraintList()
            self.model.initial_y = pe.ConstraintList()


        self.model.initial_t.add(expr=self.model.t[i] == t)
        self.model.initial_p.add(expr=self.model.p[i] == p)

        if n != 0:
            self.model.initial_n.add(expr=self.model.n[i] == n)
            self.streams[i].stream_type = 'Fixed (initial)'
        else:
            self.streams[i].stream_type = 'Fixed (utility)'

        if y == 'B(O)FG':
            y_init = {'CO': 0.24, 'CO2': 0.22, 'H2': 0.04, 'O2': 0, 'N2': 0.47, 'CH4': 0, 'H2O': 0.03}  # BFG/BOFG Mix
        elif y == 'COG':
            y_init = {'CO': 0.04, 'CO2': 0.01, 'H2': 0.62, 'O2': 0, 'N2': 0.06, 'CH4': 0.22, 'H2O': 0.05}  # COG
        else:
            y_init = {}
            for k in self.model.substances:
                if k in y.keys():
                    y_init[k] = y[k]
                else:
                    y_init[k] = 0

        for k in self.model.substances:
            self.model.initial_y.add(expr=self.model.y[i, k] == y_init[k])

    def mix_streams(self, name, i_in_1, i_in_2, i_out):

        self.create_streams(i_in_1, i_in_2, i_out)
        self.units[name] = Mixer(self.streams[i_in_1], self.streams[i_in_2], self.streams[i_out])
        self.model.add_component(name, self.units[name].unit_block)

    def prepare_unit(self, unit_type, name, i_in, i_prod, i_bp, k_prod):
        """
        Sets up a new unit and saves it in the units library without adding
        its block to the model. Used by create_unit and create_unit_disjunct
        """
        if unit_type == 'Compressor':
            self.model.workSet.add(name)
            self.units[name] = Compressor(self.streams[i_in], self.streams[i_prod], self.model.w[name])
        elif unit_type == 'Heat Exchanger':
            self.model.heatSet.add(name)
            self.units[name] = HeatExchanger(self.streams[i_in], self.streams[i_prod], self.model.q[name])
        elif unit_type == 'CCA':
            self.model.zetaSet.add(name)
            self.model.heatSet.add(name)
            self.units[name] = CCA(self.streams[i_in], self.streams[i_prod], self.streams[i_bp], self.model.zeta[name],
                                   k_prod, self.model.q[name])
        elif unit_type == 'Splitter':
            self.model.splitSet.add(name)
            self.units[name] = Splitter(self.streams[i_in], self.streams[i_prod], self.streams[i_bp],
                                        self.model.split[name])
        elif unit_type == 'TSA':
            self.model.sorpSet.add(name)
            self.model.zetaSet.add(name)
            self.model.heatSet.add(name)
            self.units[name] = TSA(self.streams[i_in], self.streams[i_prod], self.streams[i_bp], self.model.zeta[name],
                                   k_prod, self.model.q[name], self.model.m_s[name], self.model.X_rich[name],
                                   self.model.X_lean[name])
        elif unit_type == 'PSA':
            self.model.zetaSet.add(name)
            self.units[name] = PSA(self.streams[i_in], self.streams[i_prod], self.streams[i_bp], self.model.zeta[name],
                                   k_prod)
        elif unit_type == 'MSP':
            self.model.zetaSet.add(name)
            self.units[name] = MSP(self.streams[i_in], self.streams[i_prod], self.streams[i_bp], self.model.zeta[name],
                                   k_prod)

    def create_unit(self, unit_type, name, i_in, i_prod, i_bp=0, k_prod=0):
        """
        unit_type: Type of the unit to be created, e.g. 'Compressor'
        name: Name of the unit to be created, e.g. 'C1'
        i_in: Index of input stream, e.g. 1
        i_prod: Index of output (product) stream, e.g. 2
        i_bp: (optional) Index of output (by-product) stream
        """

        self.create_streams(i_in, i_prod, i_bp)

        self.prepare_unit(unit_type, name, i_in, i_prod, i_bp, k_prod)

        self.model.add_component(name, self.units[name].unit_block)  # This line is different for disjuncts


    def create_disjunct(self, name_disjunction, name_disjunct):
        """ Creates a new disjunct"""

        " Create empty disjunct and add it to model "
        if name_disjunct not in self.disjuncts.keys():
            self.disjuncts[name_disjunct] = gdp.Disjunct()
            self.model.add_component(name_disjunct, self.disjuncts[name_disjunct])

            " Prepares disjunction to be created  "
            if name_disjunction not in self.disjunction_sets.keys():
                self.disjunction_sets[name_disjunction] = []

            self.disjunction_sets[name_disjunction].append(self.disjuncts[name_disjunct])

    def create_disjunctions(self):
        """
        04.06.
        Creates all necessary disjunctions, must be enforced after all
        disjuncts are created
        """
        for name_disjunction in self.disjunction_sets.keys():
            self.disjunctions[name_disjunction] = gdp.Disjunction(expr=self.disjunction_sets[name_disjunction])
            self.model.add_component(name_disjunction, self.disjunctions[name_disjunction])

    def create_disjunct_unit(self, name_disjunction, name_disjunct, unit_type, name, i_in, i_prod, i_bp=0, k_prod=0):

        self.create_streams(i_in, i_prod, i_bp)

        self.prepare_unit(unit_type, name, i_in, i_prod, i_bp, k_prod)

        self.units[name].unit_attributes['disjunct'] = name_disjunct

        self.create_disjunct(name_disjunction, name_disjunct)

        self.disjuncts[name_disjunct].add_component(name, self.units[name].unit_block)

    def create_reactor(self, name, i_in, i_out, reaction1, reaction2=0):
        """
        name: Name of the reactor to be created, e.g. 'R1'
        i_in: Index of input stream, e.g. 1
        i_out: Index of output (product) stream, e.g. 2
        reaction1: Chemical reaction, e.g. WGS
        reaction2: (optional)
        """
        self.create_streams(i_in, i_out)
        self.model.heatSet.add(name)

        self.model.conversionSet.add(name + reaction1)
        if reaction2 == 0:
            self.units[name] = Reactor(self.streams[i_in], self.streams[i_out], self.model.q[name], reaction1, self.model.conversion[name + reaction1])
        else:
            self.model.conversionSet.add(name + reaction2)
            self.units[name] = Reactor(self.streams[i_in], self.streams[i_out], self.model.q[name], reaction1, self.model.conversion[name + reaction1], reaction2, self.model.conversion[name + reaction2])

        self.model.add_component(name, self.units[name].unit_block)

    def create_disjunct_reactor(self, name_disjunction, name_disjunct, name, i_in, i_out, reaction1, reaction2=0):
        """
        name: Name of the reactor to be created, e.g. 'R1'
        i_in: Index of input stream, e.g. 1
        i_out: Index of output (product) stream, e.g. 2
        reaction1: Chemical reaction, e.g. WGS
        reaction2: (optional)
        """
        self.create_streams(i_in, i_out)
        self.model.heatSet.add(name)

        self.model.conversionSet.add(name + reaction1)
        if reaction2 == 0:
            self.units[name] = Reactor(self.streams[i_in], self.streams[i_out], self.model.q[name], reaction1, self.model.conversion[name + reaction1])
        else:
            self.model.conversionSet.add(name + reaction2)
            self.units[name] = Reactor(self.streams[i_in], self.streams[i_out], self.model.q[name], reaction1, self.model.conversion[name + reaction1], reaction2, self.model.conversion[name + reaction2])

        self.units[name].unit_attributes['disjunct'] = name_disjunct

        self.create_disjunct(name_disjunction, name_disjunct)

        self.disjuncts[name_disjunct].add_component(name, self.units[name].unit_block)

    def setupConstraints(self):
        """
        Sets up further constraints, which do not belong to a certain unit operation,
        e.g. product requirements
        """

    def setupObjective(self):
        """ Separation only objective function, not required for overall model """
        self.model.objective = pe.Objective(expr=
                                            - molar_weight('CO') * self.model.impact_co * self.model.n[20]
                                            - molar_weight('CO2') * self.model.impact_co2 * self.model.n[8]
                                            - molar_weight('H2') * self.model.impact_h2 * self.model.n[11]
                                            + self.model.impact_heat * self.model.q['TSA1']
                                            + self.model.impact_heat * self.model.q['CCA1']
                                            + self.model.impact_heat * self.model.q['HE3']
                                            + self.model.impact_heat * self.model.q['HE5']
                                            + self.model.impact_heat * self.model.q['R2_CDR']
                                            + self.model.impact_heat * self.model.q['R2_POR']
                                            - molar_weight('H2') * self.model.impact_h2 * self.model.n[33]
                                            - molar_weight({'H2': 0.67, 'CO': 0.33}) * self.model.impact_syngas_21 *
                                            self.model.n[38]
                                            + molar_weight('O2') * self.model.impact_o2 * self.model.n[22] * self.model.y[
                                                22, 'O2']
                                            + molar_weight('CO2') * (-1) * self.model.n[22] * self.model.y[22, 'CO2']
                                            + self.model.impact_electricity * sum_rule(self.model.w, self.model.workSet)
                                            , sense=pe.minimize)

        self.objective = self.model.objective
