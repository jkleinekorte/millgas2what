# millgas2what

Responsible for this repository is johanna.kleinekorte@rwth-aachen.de.

# Introduction 
This repository provides all non-licensed parts of the code to reproduce the results published in the paper "What shall we do with steel mill off-gas: Polygeneration systems minimizing greenhouse gas emissions" (DOI: to be added after submission)

# Getting Started
Set up an environment with the defined dependencies in environment.yaml. The packages „Pyomo“ und „Pyomo Solver“ must be installed. Installing licensed solvers such as Gurobi is optional.

The following descriptions of the files should help you to get started:
Script main_overall
Runs the model including the separation system (GDP). The results are saved using "save_results".

Script main_tcm
Runs only the model of the chemcical industry (which then equals the technology choice model (TCM), published e.g. in https://doi.org/10.1021/acs.est.6b04270 and https://doi.org/10.1073/pnas.1821029116). The results are saved using "save_results". 

Script solve_model
Solves the optimization problem. Herein, you can select different solvers and solving strategies. For the publication, we used GDPopt with the LOA strategy (https://pyomo.readthedocs.io/en/stable/contributed_packages/gdpopt.html).
As sub-solver, we used glpk and ipopt. 

Script save_results
Saves the results for the solved optimization (TCM or GDP). You can chose between different options: 
•	Display results? Shows the results in the command line
•	Save results as excel file? Stores the results as excel 
•	Save superstructure object? stores the overall model as file

Script repeated_solving_el_impact
Solves TCM and GDP for varying electricity impacts (i.e., figure 5 in the paper). The results are not saved using save_results, as the file becomes to large. Instead, the values of the model variables are stored in a dictionary. As an example, we provide you the dictionary created for Figure 5 in the paper: 20200816_v19_pcest7_100_complete 

Script plot
Plots the results dictionary
The results are casted into a list and nonsensical values are filtered (see documentation in the code).

Excel Life Cycle Inventory
Unfortunately, we are not allowed to share the inventory file due to licensing reasons. If you can prove that you have a valid licence for the IHS data, please contact me. 

Class Superstructure
Contains all functions to create a flowsheet and to setup the GDP optimization problem.

Class LifeCycleInventory
•	Reads the Life Cycle Inventory from the excel file 
•	Setup the linear optimization problem of the chemical industry
•	Allows to deactivate specific processes (useful to calculate different scenarios)

# Build and Test
Unfortunately, we have no tests or deployment pipeline yet. But feel free to change that.

# Contribute
One interesting option to improve the code would be to use the IDAES package (https://github.com/IDAES) for the process units. 





