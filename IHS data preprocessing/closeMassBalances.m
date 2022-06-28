function [impacts] = closeMassBalances

[~, ~, data] = xlsread('Life Cycle Inventory_v15.xlsx','A16:LV137');

flows_of_interest = data;
flows_of_interest([17,25,26,33,42:44,47,52,64,65,67,91:93,96,97],:) = [];
legend_flows = flows_of_interest(:,1);
inventories = cell2mat(flows_of_interest(:,3:end));
inventories(75,:) = inventories(75,:) * 1000; % Umrechnung von m³ in kg

[num, ~, ~] = xlsread('Life Cycle Inventory_v15.xlsx','A139:LV139');
CC = num;

[~, ~, data] = xlsread('Life Cycle Inventory_v15.xlsx','Stoffdaten');

flows = data(3:end,1);
MW = cell2mat(data(3:end,3));
composition = cell2mat(data(3:end,4:end));
composition(isnan(composition)) = 0;

inventories_molar = inventories./MW;
wastes = zeros(4, length(inventories_molar));
for i = 1:length(inventories)
    elementalFlows = inventories_molar(:,i).*composition;
    diff = sum(elementalFlows,1);
    wastes(1,i) = -diff(1)*MW(21);                                      % C-Bilanz über CO2
    diff(3) = diff(3)-diff(1)*2;
    temp_waste = -diff(2)/2*MW(102);                                    % H-Bilanz über H2O
    if temp_waste > 0
        wastes(2,i) = temp_waste;                                       % Wasser als waste water
    else
        wastes(3,i) = temp_waste/1000;                                  % Wasser als Process water
    end
    diff(3) = diff(3)-diff(2);
end

index = find((abs(sum(inventories,1))==1)|abs(sum(inventories,1))<1e-3);
wastes(:,index) = 0;
wastes(4,:) = CC;
end