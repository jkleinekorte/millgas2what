import pyomo.environ as pe
from datetime import date
import xlsxwriter as xw
import os.path
import pickle
from superstructure import Superstructure
from lci import LifeCycleInventory


def clean_value(v, e=0.0001):
    # if type(v) is pe.SimpleVar:
    v = pe.value(v)
    # e = 0.0001
    if v < e:
        if v > -e:  # Numerische Fehler liegen im Bereich 10^(-7)
            v = 0
    return v


class ResultManager():
    """
    Saves and displays results of optimization
    28.06.2020:
    """

    def __init__(self, s):

        """
        s: object of class Superstructure or LifeCycleInventory
        """

        self.s = s
        self.lci = None

        if type(self.s) == Superstructure:
            if type(self.s.lci) is not None:
                self.lci = self.s.lci

        if type(self.s) == LifeCycleInventory:
            self.lci = self.s

        input_disp = input("Display results? (y/n)")
        if input_disp == 'y':
            self.display_results()

        input_save = input("Save results as excel file? (y/n)")
        if input_save == 'y':
            self.save_excel()

        input_save2 = input("Save superstructure object? (y/n)")
        if input_save2 == 'y':
            self.save_superstructure()

    def display_results(self):
        """ s: object of class superstructure or lci """

        if type(self.s) == Superstructure:
            for d in self.s.disjuncts.keys():
                print('Indicator variable', d)
                self.s.disjuncts[d].indicator_var.display()

        self.s.objective.display()

        self.s.model.display()

    def save_excel(self):

        ymd = date.today().strftime("%Y%m%d")
        name = input("enter file name") + ".xlsx"

        workbook = xw.Workbook(ymd + '_' + name)  # xlsxwriter can only create new files, not open/modify existing ones (--> pandas)

        worksheet = workbook.add_worksheet('results')

        worksheet.write(0, 0, self.s.name)

        worksheet.write(0, 2, "Impact (objective function)")

        worksheet.write(0, 4, "kg CO2-eq/year")

        worksheet.write(0, 6, "Solver")
        worksheet.write(0, 7, self.s.solver_used)

        worksheet.write(0, 10, "Time (solver)")
        worksheet.write(0, 11, self.s.solver_timer)
        worksheet.write(0, 12, "s")

        worksheet.write(0, 3, pe.value(self.s.objective) * self.lci.scale)

        if type(self.s) is Superstructure:
            worksheet.write(2, 0, "Streams")
            worksheet.write(2, 1, "Type")
            worksheet.write(2, 2, "n [mol/year]")
            worksheet.write(2, 3, "t [°C]")
            worksheet.write(2, 4, "p [bar]")

            n_subst = 1
            for k in self.s.model.substances:
                worksheet.write(2, 4 + n_subst, "y_" + k)
                n_subst += 1

            n_streams = 1
            for i in self.s.model.streamSet:
                worksheet.write(2 + n_streams, 0, i)
                worksheet.write(2 + n_streams, 2, clean_value(self.s.model.n[i]) * self.lci.scale)
                worksheet.write(2 + n_streams, 3, pe.value(self.s.model.t[i]) - 273.15)
                worksheet.write(2 + n_streams, 4, pe.value(self.s.model.p[i]))
                worksheet.write(2 + n_streams, 1, self.s.streams[i].stream_type)

                n_subst = 1
                for k in self.s.model.substances:
                    worksheet.write(2 + n_streams, 4 + n_subst, pe.value(self.s.model.y[i, k]))
                    n_subst += 1

                n_streams += 1

            worksheet.write(n_streams + 3, 0, "Utilities")
            worksheet.write(n_streams + 3, 1, "Heat [MJ/year]")
            worksheet.write(n_streams + 3, 4, "Electricity [MJ/year]")

            n_heat = 1
            for h in self.s.model.heatSet:
                worksheet.write(n_streams + 3 + n_heat, 0, h)
                worksheet.write(n_streams + 3 + n_heat, 1, pe.value(self.s.model.q[h]) * self.lci.scale)
                n_heat += 1

            n_el = 1
            for e in self.s.model.workSet:
                worksheet.write(n_streams + 3 + n_el, 3, e)
                worksheet.write(n_streams + 3 + n_el, 4, pe.value(self.s.model.w[e]) * self.lci.scale)
                n_el += 1

        if type(self.s) is Superstructure:
            self.save_excel_flowsheet(workbook)

        if type(self.lci) is not None:
            self.save_excel_lci(workbook)

        workbook.close()

    def save_excel_flowsheet(self, workbook):

        worksheet2 = workbook.add_worksheet('flowsheet')

        worksheet2.write(0, 0, 'Units')

        n_unit = 2
        for u in self.s.units.keys():
            worksheet2.write(n_unit, 0, u)
            worksheet2.write(n_unit + 1, 0, self.s.units[u].unit_type)
            u_attr = 1

            for a in self.s.units[u].unit_attributes.keys():
                worksheet2.write(n_unit, u_attr, a)
                worksheet2.write(n_unit + 1, u_attr, self.s.units[u].unit_attributes[a])
                u_attr += 1


            if 'disjunct' in self.s.units[u].unit_attributes.keys():
                worksheet2.write(n_unit, u_attr, 'active')
                worksheet2.write(n_unit + 1, u_attr,
                                pe.value(self.s.disjuncts[self.s.units[u].unit_attributes['disjunct']].indicator_var))

            n_unit += 3

    def save_excel_lci(self, workbook):

        worksheet3 = workbook.add_worksheet('scaling vector')
        worksheet3.write(0, 0, 'Process')
        worksheet3.write(0, 1, 's')
        n = 0
        for p in self.lci.processes:
            worksheet3.write(n + 1, 0, p)
            worksheet3.write(n + 1, 1, clean_value(self.lci.lp.s[p]) * self.lci.scale)
            n += 1

        worksheet4 = workbook.add_worksheet('sankey matrix')
        n = 1
        for p in self.lci.processes:
            worksheet4.write(0, n, p)
            n += 1

        n = 1
        for i in self.lci.intermediate_flows:
            worksheet4.write(n, 0, i)
            n += 1

        k = 0
        for p in self.lci.processes:
            j = 0
            while j < len(self.lci.intermediate_flows):
                worksheet4.write(j + 1, k + 1, self.lci.A.iloc[j, k] * clean_value(
                    self.lci.lp.s[p]) * self.lci.scale)
                j += 1
            k += 1

        if type(self.s) is Superstructure:

            worksheet4.write(0, k + 1, 'Separation System')
            f = 0
            while f < len(self.s.lci.intermediate_flows):
                if self.s.lci.intermediate_flows[f] in self.s.connect_list:
                    worksheet4.write(f + 1, k + 1, clean_value(
                        self.s.model.connect_lp[self.s.lci.intermediate_flows[f]]) * self.s.lci.scale)
                else:
                    worksheet4.write(f + 1, k + 1, 0)
                f += 1

    def save_superstructure(self):
        def save_object(obj, filename):
            with open(filename, 'wb') as output:  # Overwrites any existing file.
                pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)

        name = input("enter file name")
        save_object(self.s, name)
