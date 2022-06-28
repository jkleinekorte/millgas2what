import matplotlib.pyplot as plt
import pickle
import numpy as np


def load_object(filename):
    with open(filename, 'rb') as input:
        object = pickle.load(input)

    return object


def plot_results_bfg(plot_name, results, options):

    x_data = []
    y_bfg_data = []
    y_h2_data = []
    y_co2_data = []
    y_co_data = []
    y_purge_data = []
    sum_data = []

    'Umwandlung in Liste und Aussortierung unsinniger Ergebnisse'

    for k in results['gdp'].keys():
        if k != 'options':
            if results['gdp'][k]['z'] != 0:  # Abstürze des Solvers wurden mit z=0 markiert
                x_data.append(results['gdp'][k]['x']*3600)
                y_bfg_data.append(results['gdp'][k]['c']['Mill gas BFG/BOFG [kg]']/1E+12)
                y_h2_data.append(results['gdp'][k]['bfg']['H2']/1E+12)
                y_co2_data.append(results['gdp'][k]['bfg']['CO2'] / 1E+12)
                y_co_data.append(results['gdp'][k]['c']['Carbon monoxide (CO) [kg]'] / 1E+12)
                sum_data.append(y_bfg_data[-1] + y_h2_data[-1] + y_co2_data[-1] + y_co_data[-1])

                if k != 0:
                    if y_gdp_temp > results['gdp'][k]['z']:  # Aussortierung von "lokalen Optima"
                        del x_data[-1]
                        del y_bfg_data[-1]
                        del y_h2_data[-1]
                        del y_co_data[-1]
                        del y_co2_data[-1]
                    if sum_data[-1] < sum_temp:
                        del x_data[-1]
                        del y_bfg_data[-1]
                        del y_h2_data[-1]
                        del y_co_data[-1]
                        del y_co2_data[-1]

                sum_temp = sum_data[-1]

                y_gdp_temp = results['gdp'][k]['z']


    sum_h2_data = []
    sum_co2_data = []
    sum_co_data = []
    sum_bfg_data = []
    sum_purge_data = []
    i = 0
    while i < len(x_data):
        sum_co_data.append((y_h2_data[i] + y_co_data[i]))
        sum_co2_data.append((sum_co_data[i] + y_co2_data[i]))
        sum_bfg_data.append(sum_co2_data[i] + y_bfg_data[i])
        i += 1

    # plot the data

    fig = plt.figure(
        figsize=options['size'],
        dpi=options['dpi'])  # Bei zu hoher Auflösung (dpi) wird das Diagramm nicht mehr angezeigt
    ax = fig.add_subplot(111, autoscale_on=False)

    if options['vlines']:
        ax.axvline(0.00957*1000, color='black', linestyle='--', linewidth=0.5)
        ax.axvline(0.386*1000, color='black', linestyle='--', linewidth=0.5)

    alpha = 0.5
    # alpha = 1

    ax.plot(x_data, y_h2_data, color='tab:blue', linewidth=0.5, alpha=alpha)
    ax.plot(x_data, sum_co_data, color='xkcd:turquoise', linewidth=0.5, alpha=alpha)
    ax.plot(x_data, sum_co2_data, color='black', linewidth=1.5)
    ax.plot(x_data, sum_bfg_data, color='black', linewidth=1.5)

    ax.fill_between(x_data, sum_co2_data, sum_bfg_data, facecolor='xkcd:grey', alpha=alpha,
                    label="Verbrennung")
    ax.fill_between(x_data, sum_co_data, sum_co2_data, facecolor='xkcd:green', alpha=alpha, label=r'$CO_2$')
    ax.fill_between(x_data, y_h2_data, sum_co_data, facecolor='xkcd:turquoise', alpha=alpha, label=r'$CO$')
    ax.fill_between(x_data, 0, y_h2_data, facecolor='tab:blue', alpha=alpha, label=r'$H_2$')

    if options['vlines']:
        ax.text(0.00957*1000 + 5, 0.1, 'Wind power',
                verticalalignment='bottom',
                horizontalalignment='left',
                rotation='vertical',
                color='black', fontsize=8)

        ax.text(0.386*1000 + 5, 0.1, 'EU Grid mix',
                verticalalignment='bottom',
                horizontalalignment='left',
                rotation='vertical',
                color='black', fontsize=8)

    # set the limits (or use autoscale)
    ax.set_xlim([0, max(x_data)])
    ax.set_ylim([0, 2.5])

    if options['legend']:
        ax.legend(loc='upper left', frameon=False)

    if options['labels']:
        if options['language'] == 'eng':
            ax.set_xlabel(r'Carbon Footprint of electricity in g $CO_2$-eq / kWh')
            ax.set_ylabel(r'Product streams of mill gas utilization in Gt / year')
        elif options['language'] == 'de':
            ax.set_xlabel(r'GHG-Emissionen Strom in g $CO_2$-eq / kWh')
            ax.set_ylabel(r'Massenströme in Gt / Jahr')

    # display the plot
    plt.show()

    fig.savefig(plot_name, transparent=True)


def plot_results_cog(plot_name, results, options):

    x_data = []
    y_cog_data = []
    y_h2_data = []
    y_ch4_data = []
    y_sg11_data = []
    y_sg21_data = []
    sum_data = []

    y_purge_data = []

    for k in results['gdp'].keys():
        if k != 'options':
            if results['gdp'][k]['z'] != 0:
                if results['gdp'][k]['c']['SYNTHESIS GAS (2:1)'] <= 1E+9:
                    x_data.append(results['gdp'][k]['x']*3600)
                    y_cog_data.append(results['gdp'][k]['c']['Mill gas COG [kg]']/1E+9)
                    y_sg11_data.append(results['gdp'][k]['c']['SYNTHESIS GAS (1:1)']/1E+9)
                    y_sg21_data.append(results['gdp'][k]['c']['SYNTHESIS GAS (2:1)']/1E+9)
                    y_ch4_data.append(results['gdp'][k]['c']['Methane (CH4) [kg]']/1E+9)
                    y_h2_data.append(results['gdp'][k]['cog']['H2']/1E+9)
                    sum_data.append(y_cog_data[-1]+y_sg11_data[-1]+y_sg21_data[-1]+y_ch4_data[-1]+y_h2_data[-1])
                    # Verbesserung der MB_Einhaltung
                    # y_purge_data.append(results['gdp'][k]['cog']['N2']/1E+9)

                if k != 0:
                    if y_gdp_temp > results['gdp'][k]['z']:
                        del x_data[-1]
                        del y_cog_data[-1]
                        del y_h2_data[-1]
                        del y_ch4_data[-1]
                        del y_sg11_data[-1]
                        del y_sg21_data[-1]
                    if sum_data[-1] > 1.01 * sum_temp:  # Aussortierung von "lokalen Optima". Der Wert von 1.01 ist rein empirisch.
                        del x_data[-1]
                        del y_cog_data[-1]
                        del y_h2_data[-1]
                        del y_ch4_data[-1]
                        del y_sg11_data[-1]
                        del y_sg21_data[-1]

                sum_temp = sum_data[-1]
                y_gdp_temp = results['gdp'][k]['z']

    sum_h2_data = []
    sum_ch4_data = []
    sum_sg11_data = []
    sum_sg21_data = []
    sum_cog_data = []
    sum_purge_data = []
    i = 0
    while i < len(x_data):
        # sum = y_h2_data[i] + y_ch4_data[i] + y_sg11_data[i] + y_sg21_data[i] + y_cog_data[i]
        sum_sg11_data.append(y_sg11_data[i])
        sum_h2_data.append((y_h2_data[i] + y_sg11_data[i]))
        sum_ch4_data.append(sum_h2_data[i] + y_ch4_data[i])
        sum_cog_data.append((sum_ch4_data[i] + y_cog_data[i]))
        # sum_purge_data.append((sum_cog_data[i] + y_purge_data[i]))
        i += 1

    # plot the data

    fig = plt.figure(
        figsize=options['size'],
        dpi=options['dpi'])  # Bei zu hoher Auflösung (dpi) wird das Diagramm nicht mehr angezeigt
    ax = fig.add_subplot(111, autoscale_on=False)
    if options['vlines']:
        ax.axvline(0.00957*1000, color='black', linestyle='--', linewidth=0.5)
        ax.axvline(0.386*1000, color='black', linestyle='--', linewidth=0.5)

    alpha = 1

    ax.plot(x_data, sum_ch4_data, color='black', linewidth=1.5)
    ax.plot(x_data, sum_h2_data, color='tab:blue', linewidth=0.5, alpha=alpha)
    ax.plot(x_data, sum_sg11_data, color='xkcd:purple', linewidth=0.5, alpha=alpha)
    # ax.plot(x_data, sum_sg21_data, color='black', linewidth=1.5)


    ax.fill_between(x_data, sum_ch4_data, sum_cog_data, facecolor='xkcd:grey', alpha=alpha, label="Verbrennung")
    # ax.fill_between(x_data, sum_sg11_data, sum_sg21_data, facecolor='xkcd:lavender', alpha=alpha, label="SynGas 2:1")
    ax.fill_between(x_data, sum_ch4_data, sum_h2_data, facecolor='tab:orange', alpha=alpha, label=r'$CH_4$')
    ax.fill_between(x_data, sum_h2_data, sum_sg11_data, facecolor='tab:blue', alpha=alpha, label=r'$H_2$')
    ax.fill_between(x_data, sum_sg11_data, 0, facecolor='xkcd:purple', alpha=alpha, label="SynGas 1:1")
    ax.plot(x_data, sum_cog_data, color='black', linewidth=1.5)


    if options['vlines']:
        ax.text(0.00957*1000 + 5, 6, 'Wind power',
                verticalalignment='bottom',
                horizontalalignment='left',
                rotation='vertical',
                color='black', fontsize=8)

        ax.text(0.386*1000 + 5, 16, 'EU Grid mix',
                verticalalignment='bottom',
                horizontalalignment='left',
                rotation='vertical',
                color='black', fontsize=8)

    # set the limits (or use autoscale)
    ax.set_xlim([0, max(x_data)])
    ax.set_ylim([0, 50])

    if options['legend']:
        ax.legend(loc='upper left', frameon=False)

    if options['labels']:
        if options['language'] == 'eng':
            ax.set_xlabel(r'Carbon Footprint of electricity in g $CO_2$-eq / kWh')
            ax.set_ylabel(r'Product streams of mill gas utilization in Mt / year')
        elif options['language'] == 'de':
            ax.set_xlabel(r'GHG-Emissionen Strom in g $CO_2$-eq / kWh')
            ax.set_ylabel(r'Massenströme in Mt / Jahr')

    # display the plot
    plt.show()

    fig.savefig(plot_name, transparent=True)


def plot_results(plot_name, results, options):

    x_conv_data = []
    y_conv_data = []

    for k in results['conv'].keys():
        if k != 'options':
            y_conv_data.append(results['conv'][k]['z']/1E+12)
            x_conv_data.append(results['conv'][k]['x']*3600)

    x_data = []
    y1_data = []
    y2_data = []
    delta_y_data = []


    for k in results['gdp'].keys():
        if k != 'options':
            if results['gdp'][k]['z'] != 0:
                x_data.append(results['gdp'][k]['x']*3600)
                y1_data.append(results['gdp'][k]['z']/1E+12)
                y2_data.append(results['tcm'][k]['z']/1E+12)
                delta_y_data.append((results['tcm'][k]['z'] - results['gdp'][k]['z'])/1E+12*10)

                if k != 0:
                    if y_gdp_temp > results['gdp'][k]['z']:
                        del x_data[-1]
                        del y1_data[-1]
                        del y2_data[-1]
                        del delta_y_data[-1]

                y_gdp_temp = results['gdp'][k]['z']

    # plot the data

    fig = plt.figure(
        figsize=options['size'],
        dpi=options['dpi'])  # Bei zu hoher Auflösung (dpi) wird das Diagramm nicht mehr angezeigt
    ax = fig.add_subplot(111, autoscale_on=False)

    ax.axvline(0.00957*1000, color='xkcd:grey', linestyle='--', linewidth=0.5)
    ax.axvline(0.386*1000, color='xkcd:grey', linestyle='--', linewidth=0.5)

    ax.plot(x_conv_data, y_conv_data, color='black', label='Benchmark', linewidth=0.5)
    ax.plot(x_data, y2_data, color='tab:blue', label='Opt. Chem.', linewidth=1.5)
    ax.plot(x_data, y1_data, color='tab:orange', label='Verbund', linewidth=1.5)

    # ax.plot(x_data, delta_y_data, color='xkcd:black')

    if options['vlines']:
        ax.text(0.00957*1000 + 5, 0.2, 'Wind power',
                verticalalignment='bottom',
                horizontalalignment='left',
                rotation='vertical',
                color='xkcd:grey', fontsize=8)

        ax.text(0.386*1000 + 5, 0.2, 'EU Grid mix',
                verticalalignment='bottom',
                horizontalalignment='left',
                rotation='vertical',
                color='xkcd:grey', fontsize=8)

    # set the limits (or use autoscale)
    ax.set_xlim([0, max(x_data)])
    ax.set_ylim([0, 6])

    if options['legend']:
        ax.legend(loc='lower right', frameon=False)

    if options['labels']:
        if options['language'] == 'eng':
            ax.set_xlabel(r'Carbon Footprint of electricity in g $CO_2$-eq / kWh')
            ax.set_ylabel(r'Cradle-to-grave GHG emissions in Gt $CO_2$-eq / year')
        if options['language'] == 'de':
            ax.set_xlabel(r'GHG-Emissionen Strom in g $CO_2$-eq / kWh')
            ax.set_ylabel(r'GHG-Emissionen Chemieindustrie (Cradle-to-grave) in Gt $CO_2$-eq / Jahr')


    # display the plot
    plt.show()

    fig.savefig(plot_name, transparent=True)


def plot_results_co2(plot_name, results, options):

    x_data = []
    c_co2_data = []
    s_ammonia_co2_data = []
    s_aircap_co2_data = []

    for k in results['gdp'].keys():
        if k != 'options':
            if results['gdp'][k]['z'] != 0:
                x_data.append(results['gdp'][k]['x']*3600)

                s_ammonia_co2_data.append((results['gdp'][k]['s']['AMMONIA FROM NATURAL GAS BY STEAM REFORMING BY ICI "AMV" PROCESS incl CO2 capture'] * 1.2)/1E+12)
                c_co2_data.append((results['gdp'][k]['c']['Carbon dioxide (CO2) [kg]'] + results['gdp'][k]['s']['AMMONIA FROM NATURAL GAS BY STEAM REFORMING BY ICI "AMV" PROCESS incl CO2 capture'] * 1.2)/1E+12)
                s_aircap_co2_data.append((results['gdp'][k]['s']['CARBON DIOXIDE - air capture'] + results['gdp'][k]['c']['Carbon dioxide (CO2) [kg]'] + results['gdp'][k]['s']['AMMONIA FROM NATURAL GAS BY STEAM REFORMING BY ICI "AMV" PROCESS incl CO2 capture'] * 1.2)/1E+12)

                if k != 0:
                    if y_gdp_temp > results['gdp'][k]['z']:
                        del x_data[-1]
                        del c_co2_data[-1]
                        del s_ammonia_co2_data[-1]
                        del s_aircap_co2_data[-1]

                y_gdp_temp = results['gdp'][k]['z']

    # plot the data
    fig = plt.figure(
        figsize=options['size'],
        dpi=options['dpi'])  # Bei zu hoher Auflösung (dpi) wird das Diagramm nicht mehr angezeigt
    ax = fig.add_subplot(111, autoscale_on=False)
    ax.plot(x_data, s_ammonia_co2_data, linewidth=0.5, color='green', alpha=0.2)
    ax.plot(x_data, c_co2_data, linewidth=0.5, color='green', alpha=0.5)

    ax.plot(x_data, s_aircap_co2_data, color='xkcd:black', linewidth=1)
    # ax.plot(x_data, s_aircap_co2_data, color='green', linewidth=1)

    ax.fill_between(x_data, c_co2_data, s_aircap_co2_data, facecolor='green', alpha=0.2, label="Direct Air Capture")
    ax.fill_between(x_data, s_ammonia_co2_data, c_co2_data , facecolor='green', alpha=0.5, label="Hüttengas-Trennung")
    ax.fill_between(x_data, 0, s_ammonia_co2_data, facecolor='green', alpha=0.9, label="Ammoniak-Anlage")

    if options['vlines']:
        ax.axvline(0.00957*1000, color='black', linestyle='--', linewidth=0.5)
        ax.axvline(0.386*1000, color='black', linestyle='--', linewidth=0.5)

        ax.text(0.00957*1000 + 5, 0.4, 'Wind power',
                verticalalignment='bottom',
                horizontalalignment='left',
                rotation='vertical',
                color='black', fontsize=8)

        ax.text(0.386*1000 + 5, 0.4, 'EU Grid mix',
                verticalalignment='bottom',
                horizontalalignment='left',
                rotation='vertical',
                color='black', fontsize=8)



    # set the limits (or use autoscale)
    ax.set_xlim([0, max(x_data)])
    ax.set_ylim([0, 3.5])

    # ax.set_title('Impact chemical industry with mill gas utilization')

    if options['legend']:
        ax.legend(loc='upper right', frameon=False)

    if options['labels']:
        if options['language'] == 'eng':
            ax.set_xlabel(r'Carbon Footprint of electricity in g $CO_2$-eq / kWh')
            ax.set_ylabel(r'Amount of captured $CO_2$ per source in Gt / year')
        elif options['language'] == 'de':
            ax.set_xlabel(r'GHG-Emissionen Strom in g $CO_2$-eq / kWh')
            ax.set_ylabel(r'Menge $CO_2$ pro Quelle in Gt / Jahr')


    # display the plot
    plt.show()

    fig.savefig(plot_name, transparent=True)


name = '20200816_v19_pcest7_100_complete'
results = load_object(name)
options = {'size': [11/2.54, 10/2.54], 'dpi': 1000, 'labels': False, 'legend': True, 'vlines': True, 'language': 'de'}

plot_results_bfg('20200904_plot_bfg_mass', results, options)
plot_results_cog('20200904_plot_cog_mass', results, options)
plot_results_co2('20200907_v19_amount_co2_4', results, options)
plot_results('20200908_v19_objective_3', results, options)

# print(results)


