function EoL = calc_incinaration(model,s)

name_element = model.waste_code.chemical_formula.flows;
name_model = model.meta_data_flows(2:end,1);
type_flow = model.meta_data_flows(2:end,2);

y = model.matrices.A.mean_values*s;

load('input\M_e.mat');
%% Calculate Carbon emissions of Flows
mol_mass = model.waste_code.chemical_formula.values * M_e;
carbon = model.waste_code.chemical_formula.values(:,8) *44 ./ mol_mass;

%% Match with flows

carbon_model = zeros(size(y,1),1);

%% Build y_fos
for i = 1:size(name_element,1)
index = find(strcmp(name_model,name_element(i)));
    if ~isempty(index) && type_flow{index} ~= 2
        carbon_model(index,:) = carbon(i,:);
    end
end

carbon_model(isnan(carbon_model))  =0;

EoL = carbon_model' * y;

end