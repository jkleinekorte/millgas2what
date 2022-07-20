function [results] = millgas2what()
%% MILLGAS2WHAT - function to optimize the supply chain of mill gas utilities
% Inputs:       "Life Cycle Inventory_v11.xlsx" is load in the function
% Outputs:      x, which is the scaling vector in LCA matrix notation
%               h, impact of optimized system
%               S, Matrix with all mass flows between processes

%% general settings & import data from excel
close all;
path = genpath(pwd);
addpath(path);
load('rwth_farben.mat');
T = [ blau; blau50; gruen; maigruen; bordeaux; schwarz; magenta; tuerkis;petrol; orange]; 
set(0,'DefaultAxesColorOrder',T, 'defaultAxesFontSize', 16); %, 'defaultAxesFont', '')

filename = 'Life Cycle Inventory_v22.xlsx';    

[A,A_ineq,Aeq,B,b_ineq,beq,Q,v,process_legend] = getMatrices(filename);
ub = 1e20*ones(size(Aeq,2),1);

%% definition of calculation scenarios
best_case = [354,171];                      % schaltet Today-Prozesse aus
today = [353,172];                          % schaltet best_case Prozesse aus
idealSep = [171:175];                         % schaltet Aspen-Trennung aus
AspenSep = [169:172];                         % schaltet ideale Trennung aus
GDP = [169:170, 174:175];
low = [];                                   % lässt alle CCU-Technologien an
high = [34,47:58];                             % schaltet CCU mit low TRL aus
inclM2X = [];                               % includiert alle Methanol 2 X Prozesse
noM2X = [35:37,40:46];                            % schaltet alle Methanol 2 X Prozesse aus

%% ------------ choose calculation scenario manually --------------------
separation = GDP; %, AspenSep];  % Wahl: idealSep, AspenSep, [idealSep, AspenSep] für Szenario ohne Hüttengasverwendung
scenario = best_case;   % Wahl: best_case oder today
TRL = low;              % Wahl: low, high
M2X = inclM2X;          % Wahl: inclM2X, noM2X
name_scenario = 'today';
%% settings für Fehlersuche
test = [56:58,335]; % 304 = DAC, 351 = NG to heat, 352 = Heat to NG, 356 = WGS reactor

%% set up of the optimization problem
toDelete            = [separation,scenario, TRL, M2X, test];
toDelete_ideal     = [idealSep,scenario, TRL, M2X, test];
toDelete_benchmark  = [idealSep, AspenSep,GDP,scenario, TRL, M2X, test];
toDelete_fossil     = [idealSep, AspenSep,GDP,scenario, high, noM2X, 1:28, test];

[~, h, S]                       = optimization(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete);
[~, h_benchmark, S_benchmark]   = optimization(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete_benchmark);
[~, h_fossil, S_fossil]   = optimization(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete_fossil);
[~, h_ideal, ~]   = optimization(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete_ideal);

reductionPotential = h-h_benchmark;
reductionPotential_fossil = h - h_fossil;
reductionPotential_ideal = h_ideal-h_benchmark;
reductionPotential_fossil_ideal = h_ideal - h_fossil;

%% prepare Sankey
sankey1 = getDeltaSankey(S_benchmark-S_fossil, A);
sankey2 = getDeltaSankey(S-S_fossil, A);
sankey3 = getDeltaSankey(S-S_benchmark, A);

%% plot contribution (Verbund exkludiert, da Sektoren gekoppelt)
contributions_fossil = calc_sectorContribution(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete_fossil);
contributions_benchmark = calc_sectorContribution(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete_benchmark);
 
allContributions = [contributions_fossil, contributions_benchmark];

% contributions_fossil = calc_singleContributions(A,A_ineq,Aeq,B,b_ineq,beq,Q,v, toDelete_fossil);
% contributions_benchmark = calc_singleContributions(A,A_ineq,Aeq,B,b_ineq,beq,Q,v, toDelete_benchmark);

%% plot dependency on electricity
plot_dependency_electricityImpact(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete, toDelete_ideal, toDelete_benchmark,...
toDelete_fossil, process_legend)

% plot_electricityAvailability(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete,...
%     toDelete_benchmark, toDelete_fossil);

%% plot Merit order curve
results_MO_benchmark = calc_MO(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete, toDelete_benchmark);
results_MO_ideal = calc_MO(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete_ideal, toDelete_benchmark);
results_MO_fossil = calc_MO(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete, toDelete_fossil);
results_MO_fossil_ideal = calc_MO(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete_ideal, toDelete_fossil);

plotMO(results_MO_benchmark, ['benchmark, ',name_scenario])
% plot_MO_singleProcess(results_MO_benchmark, process_legend, ['benchmark, ',name_scenario])

%% plot absolute reductionPotential
plotAbsolutePotential(results_MO_benchmark,results_MO_fossil,results_MO_ideal,results_MO_fossil_ideal, name_scenario);
plotMOAndPotentialInOne(results_MO_benchmark,results_MO_fossil, name_scenario);

%% save results
results_globalDemand.deltaS = sankey;
results_globalDemand.S = S;
results_globalDemand.S_benchmark = S_benchmark;
results_globalDemand.redPotential = reductionPotential;
results.globalDemand = results_globalDemand;

try
    results.MO_benchmark = results_MO_benchmark;
    results.MO_fossil = results_MO_fossil;
catch
    warning('The merit order was not calculated')
end

save(['results\Results_',name_scenario,'.mat'],'results');
end
function [A,A_ineq,Aeq,B,b_ineq,beq,Q,v, process_legend] = getMatrices(filename)
set_eq_constraints = [22,23,33,47,64,65,91:93,118,119];
A       = xlsread (filename,1,'C16:MU137');     % A - Technology Matrix
B       = xlsread (filename,1,'C139:MU139');    % B - Elementary Flow Matrix
b_pos   = xlsread (filename,1,'B16:B137');      % inequality vector (values of production) - Überproduktion erlaubt
Q       = [1];                                  % Characterization Matrix
v       = xlsread(filename,3,'L2:L123')';        % end of life emissions
Aeq = A(set_eq_constraints,:);

[~,process_legend,~] = xlsread('Legende_Prozesse.xlsx',1);

A_ineq = A;
A_ineq(set_eq_constraints,:)=0;
A_pos = A_ineq;
A_pos(A_pos<0) = 0;
A_ineq = [A_ineq;A_pos];

b_pos(set_eq_constraints,:) = 0;

b_ineq = [zeros(1,size(A,1))';b_pos];       % first part of inequality constraints A*s>=b -> only positive production
beq = zeros(1,size(Aeq,1))';                % equality constraints -> fixed market capacities
beq(3) = 2.30e+12;                          % demand of electricity in steel mills
beq(4) = 8.94991e+11;                       % demand of heat in steel mills
beq(5)= -1.74055e+12;                       % usage of 1.74055e12 kg BFG + BOFG (global per year)
beq(6)= -3.97e+10;                          % usage of 3.97E+10 kg COG (global per year)

end

function [x, h, S] = optimization(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete)

A(:,toDelete) = 0;
A_ineq(:,toDelete) = 0;
Aeq(:,toDelete) = 0;
B(:,toDelete) = 0;

%% Parameters for Linear Programming

f = Q * B + v * A;                                                          % f is our objective (z) Q*B = cradle to gate emissions, A*v = end of life
lb = zeros (size(Aeq,2), 1);                                                % The vector has the length of the second dimension of A (here: column)

ub(357) = 220/1.2*1e9;                                                          % limitation of CO2 capture from ammonia plant
%ub(357) = 12e10;
%options = optimoptions('linprog','Algorithm','dual-simplex','Display','none','OptimalityTolerance', 1e-10);
%options = optimoptions(@linprog, 'Preprocess', 'none','display','off', 'Algorithm','interior-point','MaxIterations',5e4);
options = optimoptions(@linprog,'Algorithm','dual-simplex', 'OptimalityTolerance', 1e-10);

scaling = 1e9;
%% Linear Programming
[x,~,exitflag] = linprog (f , -1*A_ineq, -1*b_ineq/scaling, Aeq, beq/scaling, lb, ub/scaling,options);   % exitflag give me the reason linprog stopped

x = x*scaling;                                                                  % scale back x = s in TCM

% h = f*x;                                                                    % environmental impact of optimized system

h_C2G = Q * B*x;
h_G2G = v * A*x;

h = [h_C2G,h_G2G];
S=A.*x';
end

function [sankey] = getDeltaSankey(deltaS,Aeq)
[~, col] = find(abs(deltaS)>1e2); col = unique(col);                        % ermittelt alle Prozesse, die nicht gleich bleiben und filtert numerische Schwnakungen raus

a = sign(Aeq(:,col));
b = sign(deltaS(:,col));
tokeep = [];

for i=1:length(col)
    if isequal(a(:,i),b(:,i))
        tokeep(end+1) = i;
    end
end

col = col(tokeep);

sankey = 0*Aeq;
sankey(:,col) = deltaS(:,col);                                                  % löscht alles, was gleich bleibt und die avoided burden
end

function plot_dependency_electricityImpact(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete,toDelete_ideal, ...
    toDelete_benchmark, toDelete_fossil, process_legend)

potential_chemical = [];
potential_integrated_GDP = [];
potential_integrated_ideal = [];
potential_fossil = [];

electricity_integrated_GDP = [];
electricity_integrated_ideal = [];
electricity_chemical = [];
electricity_fossil = [];
    
index = [];
counter = 0;
x_all = [];
deltax = [];
controlResults = [];
%beq(beq>0|beq<0) = 0;         % schaltet das Stahlwerk ab

for i=0:0.0005:0.15
    counter = counter + 1;
    B(353) = i;
    B(354) = i;
    [x, h, ~] = optimization(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete);
    [x_ideal, h_ideal, ~] = optimization(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete_ideal);
    [x_benchmark, h_benchmark, ~] = optimization(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete_benchmark);
    [x_fossil, h_fossil, ~] = optimization(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete_fossil);
    
    x_all(:,counter) = x;
    deltax = x-x_benchmark;
    deltax(deltax<1e-2)=0;
    x_delta(:,counter) = deltax;
    index(end+1) = i*3.6*1000;
    potential_integrated_GDP(end+1,:) = h;
    potential_integrated_ideal(end+1,:) = h_ideal;
    potential_chemical(end+1,:) = h_benchmark;
    potential_fossil(end+1,:) = h_fossil;
    
    electricity_integrated_GDP(end+1) = 0.3650*x(167)+ 0.3960*x(168)+x(353)+x(354);

    electricity_integrated_ideal(end+1) = 0.3650*x_ideal(167)+ 0.3960*x_ideal(168)+x_ideal(353)+x_ideal(354);
    electricity_chemical(end+1) = 0.3650*x_benchmark(167)+ 0.3960*x_benchmark(168)+x_benchmark(353)+x_benchmark(354);
    electricity_fossil(end+1) = 0.3650*x_fossil(167)+ 0.3960*x_fossil(168)+x_fossil(353)+x_fossil(354);
    
    controlResults(:,end+1) = A*x;
end
%endOfLife = 8.11; % Verbrennen des globalen Chemiedemands % 20.8; % Verbrennen des kompletten Marktvolumens [Gt]
fig1 = figure();
plot(index,sum(potential_fossil,2)*1e-12, 'Color',[0,0,0],'LineWidth',1)
hold on
plot(index,sum(potential_chemical,2)*1e-12, 'Color',[246/255, 168/255, 0/255],'LineWidth',1)
plot(index,sum(potential_integrated_GDP,2)*1e-12, 'Color',[87/255, 171/255, 39/255],'LineWidth',1)
% plot(index,sum(potential_integrated_ideal,2)*1e-12,'--', 'Color',[87/255, 171/255, 39/255],'LineWidth',1)

% Plot in kWh
plot([0.00957*1000, 0.00957*1000],[0 6],'--','Color',[156/255, 158/255, 159/255],'LineWidth',1)
plot([0.386*1000, 0.386*1000],[0 6],'--','Color',[156/255, 158/255, 159/255],'LineWidth',1)
hold off
% xlabel('global warming impact [kg CO_{2,eq}/MJ]');
xlabel('GHG emissions electricity [g CO_{2,eq}/kWh]');
xlim([0 500]);
ylabel({'GHG emissions (cradle-to-grave)'; 'of steel and chemical industry'; '[Gt CO_{2,eq}]'});
legend('Fossil chemical industry','Optimized chemical industry','Polygeneration','Location','southeast');
end

function plot_electricityAvailability(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete, ...
    toDelete_benchmark, toDelete_fossil)

potential_chemical = [];
potential_integrated_GDP = [];
potential_fossil = [];

electricity_integrated_GDP = [];
electricity_chemical = [];
electricity_fossil = [];
    
index = [];
counter_i = 0;

electricity_impacts = [0, 0.002658333, 0.005, 0.01, 0.025, 0.05, 0.107222222, 0.15];
% electricity_impacts = [0.002658333];


for i=1:length(electricity_impacts)
    B(353) = electricity_impacts(i);
    B(354) = electricity_impacts(i);
    counter_i = counter_i + 1;
    counter_j = 0;
    
    for j = 0:1:40
        counter_j = counter_j + 1;
        ub(353) = j*1e12*3.6+ 3228130179100.28;
        ub(354) = j*1e12*3.6+ 3228130179100.28;
        [x, h, ~] = optimization(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub,toDelete);
        [x_benchmark, h_benchmark, ~] = optimization(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete_benchmark);
        [x_fossil, h_fossil, ~] = optimization(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete_fossil);

        potential_integrated_GDP(counter_i,counter_j) = sum(h);
        potential_chemical(counter_i,counter_j) = sum(h_benchmark);
        potential_fossil(counter_i,counter_j) = sum(h_fossil);

        electricity_integrated_GDP(counter_i,counter_j) = 0.3650*x(167)+ 0.3960*x(168)+x(353);
        electricity_chemical(counter_i,counter_j) = 0.3650*x_benchmark(167)+ 0.3960*x_benchmark(168)+x_benchmark(353);
        electricity_fossil(counter_i,counter_j) = 0.3650*x_fossil(167)+ 0.3960*x_fossil(168)+x_fossil(353);
    end
end

fig1 = figure();
plot([0:40],potential_fossil(7,:)*1e-12,...
'Color',[0, 0, 0],'LineWidth',1)
hold on
for i = 1:length(electricity_impacts)
    plot([0:40],potential_chemical(i,:)*1e-12,...
    'Color',[246/255, 168/255, 0/255],'LineWidth',1)
    plot([0:40],potential_integrated_GDP(i,:)*1e-12,...
    'Color',[87/255, 171/255, 39/255],'LineWidth',1)
end
hold off
xlabel({'Additional electricity demand [PWh]'});
ylabel({'GHG emissions (cradle-to-grave)'; 'of the steel and chemical industry'; '[Gt CO_{2,eq}]'});
legend('Fossil chemical industry','Optimized chemical industry','Polygeneration','Location','southwest');
end

function [results] = calc_MO(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete, toDelete_benchmark)
% ggf To do für Zukunft: die Constraints für global demands an Strom und
% Wärme (= Bedarf des Stahlwerks für globale Hüttengas-Menge) auch linear
% mit der Hüttengas-menge variieren

counter=0;

upperBound = abs(beq(5)+beq(6));
delta_x = [];
x = [];

fraction_BFG = beq(5)/(beq(5)+beq(6));

for i=linspace(1,upperBound,1000)
    
    counter=counter+1;
    beq(5)=-i*fraction_BFG; % Anteil an BFG+BOFG
    beq(6)=-i*(1-fraction_BFG); % Anteil COG
    
    millgas(counter,1)=i*fraction_BFG;
    millgas(counter,2)=i*(1-fraction_BFG);
    millgasTotal(counter) = sum(millgas(counter,:),2);
    
    [x, h, S] = optimization(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete);
    [x_benchmark, h_benchmark, S_benchmark] = optimization(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete_benchmark);
    
    potential(counter) = sum(h_benchmark - h);
    
    x_all(:,counter) = x;
    
    delta = x-x_benchmark;
    delta(delta<1e-2)=0;
    delta_x(:,counter) = delta;
    
    if counter~=1
        impact_per_kg(counter)=(potential(counter)-potential(counter-1))/(millgasTotal(counter)-millgasTotal(counter-1));
        impact_per_COG(counter) = (potential(counter)-potential(counter-1))/(millgas(counter,2)-millgas(counter-1,2));
    end
    
    sankey{counter} = getDeltaSankey(S-S_benchmark, A);
end



results.sankey = sankey;
results.millgas = [millgas, -millgasTotal'];
results.delta_x = delta_x;
results.x = x_all;
results.reductionPotential = potential;
results.impacts = impact_per_kg;
results.impacts_COG = impact_per_COG;
end

function plotMO(results, scenario)
%millgas = -results.millgas(:,3);
millgas = results.millgas(:,2); %plot only COG
impact_per_kg = results.impacts;
impact_per_COG = results.impacts_COG;

fig1 = figure;
plot(millgas/1e9, impact_per_COG,'LineWidth',1)
xlabel('Available COG [Mt]');
ylabel({'GHG savings'; '[kg CO_{2,eq}/kg COG]'});
end

function plot_MO_singleProcess(results,process_legend, scenario)
millgas = -results.millgas(:,3);

masses = results.x;
masses(347,:) = masses(347,:)*0.083;    % Korrektur des H2 aus NG (es werden nicht 1 kg, sondern nur 0.083 produziert)
masses(167,:) = masses(167,:)*2.7;    % Korrektur Verbrennen BFG
masses(168,:) = masses(168,:)*37.1;    % Korrektur Verbrennen COG
masses(end+1,:) = masses(169,:)*0.002672725 + masses(170,:)*0.138679461 ...
    + masses(171,:)*0.125944584 + masses(171,:)*28;        % Berechnung H2 aus Hüttengasen 
masses(end+1,:) = masses(170,:)*0.402101896 + masses(171,:)*0.251889169 ...
    + masses(172,:)*16;                                    % Berechnung CH4 aus Hüttengasen	  
masses(end+1,:) = masses(169,:)*0.219831618 + masses(170,:)*0.13114005 + masses(172,:)*31;                  % Berechnung CO aus Hüttengasen 
masses(end+1,:) = masses(169,:)*0.317519711 + masses(170,:)*0.060315284 + ...
    masses(171,:)*-0.151133501 + masses(172,:)*918;       % Berechnung CO2 aus Hüttengasen
masses(end+1,:) = masses(169,:)*0.435921422 + masses(170,:)*0.185515193;                                    % Berechnung N2 aus Hüttengasen 
masses(end+1,:) = masses(171,:)*0.251889169;                                                                % Berechnung SynGas (1:1) aus Hüttengasen 

gradients = zeros(size(masses));
for i = 1:size(masses,2)-1
    gradients(:,i) = masses(:,i+1)-masses(:,i);
end
maxGradient = max(abs(gradients),[],2);
masses = masses(maxGradient>1,:)/1e12;
processes = process_legend(maxGradient>1);

fig1 = figure;
if strcmp(scenario,'today')
    plot(millgas/1e12, masses([1:2,8:10,14,25,29:33],:),'LineWidth',1)
    xlabel('Available steel mill off-gases [Gt]');
    ylabel('Mass flows [Gt]');
    legend(processes([1:2,8:10,14,25,29:33]), 'Location','northwest','FontSize',8);
    ylim([0 0.03])
else
    plot(millgas/1e12, masses([1,2,5,6,16:18],:),'LineWidth',1)
    xlabel('Available steel mill off-gases [Gt]');
    ylabel('Mass flows [Gt]');
    ylim([0 0.5])
    legend(processes([1,2,5,6,16:18]), 'Location','east','FontSize',8);
end
% savefig(fig1,['figures\Dependency_processes_gasAvailability_',scenario,'.fig']);
end

function plotAbsolutePotential(results_benchmark, results_fossil, results_ideal,results_fossil_ideal,scenario)
%millgas = -results_benchmark.millgas(:,3);
millgas = results_benchmark.millgas(:,2);   %nur COG plotten, da BFG nicht verwendet wird
pot1 = results_benchmark.reductionPotential;
pot2 = results_fossil.reductionPotential;
pot3 = results_ideal.reductionPotential;
pot4 = results_fossil_ideal.reductionPotential;

fig1 = figure;
% plot(millgas/1e12,pot2(2:end)/1e9, 'Color',[0,0,0]);
plot(millgas/1e9,pot2/1e9, 'Color',[0,0,0],'LineWidth',1);
hold on
% plot(millgas/1e12,pot4/1e12,'--', 'Color',[0,0,0],'LineWidth',1);
plot(millgas/1e9,pot1/1e9, 'Color',[87/255, 171/255, 39/255],'LineWidth',1);
% plot(millgas/1e12,pot3/1e12, '--','Color',[87/255, 171/255, 39/255],'LineWidth',1);
hold off
xlabel('Available COG [Mt]');
ylabel('GHG savings [Mt CO_{2,eq}]');
% legend('Reduction potential to business-as-usual','Reduction potential to optimised chemical industry',...
%     'Location','southoutside'); %'southeast');
% savefig(fig1,['figures\Dependency_reductionPotential_gasAvailability_absolute_',scenario,'.fig']);
end

function plotMOAndPotentialInOne(results_benchmark, results_fossil, scenario)
millgas = -results_benchmark.millgas(:,3);
impact_per_kg = results_benchmark.impacts;

pot1 = results_benchmark.reductionPotential;
pot2 = results_fossil.reductionPotential;

fig1 = figure;
subplot(2,1,1);

plot(millgas/1e12,pot2/1e9, 'Color',[0,0,0]);
hold on
plot(millgas/1e12,pot1/1e9, 'Color',[87/255, 171/255, 39/255]);
hold off
%xlabel('Available steel mill off-gases [Gt]');
ylabel('GHG savings [Mt CO_{2,eq}]');
legend('GHG savings to fossil chemical industry','Reduction potential to optimized chemical industry',...
    'Location','southeast');

subplot(2,1,2);
plot(millgas/1e12, impact_per_kg)
xlabel('Available steel mill off-gases [Gt]');
ylabel({'GHG savings per kg steel mill off-gas'; '[kg CO_{2,eq}/kg steel mill off-gas]'});

% savefig(fig1,['figures\Dependency_reductionPotential_gasAvailability_allInOne_',scenario,'.fig']);
end

function [h] = calc_sectorContribution(A,A_ineq,Aeq,B,b_ineq,beq,Q,v,ub, toDelete)

[x_chemicals, h_chemicals, ~] = optimization(A,A_ineq,Aeq,B,b_ineq,zeros(size(Aeq,1),1),Q,v,ub, toDelete);
[x_steel, h_steel, ~] = optimization(A,A_ineq(1:size(A,1),:),Aeq,B,b_ineq(1:size(A,1)),beq,Q,v,ub, toDelete);

h = [h_chemicals; h_steel];
end
