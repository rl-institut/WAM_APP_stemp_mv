
from oemof.solph import Flow, Transformer, Bus, Investment
from oemof.tools.economics import annuity

from stemp.scenarios.basic_setup import PrimaryInputScenario, AdvancedLabel


class Scenario(PrimaryInputScenario):
    name = 'Gas'
    needed_parameters = {
        'General': ['wacc', 'gas_price', 'gas_rate'],
        'Gas': ['lifetime', 'capex', 'opex', 'efficiency', 'co2_emissions'],
        'demand': ['index', 'type']
    }
    
    def create_energysystem(self, **parameters):
        super(Scenario, self).create_energysystem()
    
        # Create oil bus
        b_gas = Bus(label=AdvancedLabel("b_gas", type='Bus'), balanced=False)
        self.energysystem.add(b_gas)
    
        # Add households separately or as whole district:
        self.add_households(parameters)    
    
    def add_technology(self, demand, timeseries, parameters):
        # Get investment parameters:
        wacc = parameters['General']['wacc'] / 100
        capex = parameters[self.name]['capex']
        lifetime = parameters[self.name]['lifetime']
        epc = annuity(capex, lifetime, wacc)
        avg_gas_price = self.average_cost_per_year(
            parameters['General']['gas_price'],
            lifetime,
            parameters['General']['gas_rate']
        )
    
        # Get subgrid busses:
        sub_b_th = self.find_element_in_groups(f'b_demand_th')
        b_gas = self.find_element_in_groups('b_gas')
        invest = Investment(ep_costs=epc)
        invest.capex = capex
        gas_heating = Transformer(
            label=AdvancedLabel(
                f'{demand.name}_gas_heating',
                type='Transformer',
                tags=('primary_source', )
            ),
            inputs={
                b_gas: Flow(
                    variable_costs=avg_gas_price,
                    investment=invest,
                    is_fossil=True,
                    co2_emissions=parameters[self.name]['co2_emissions']
                )
            },
            outputs={
                sub_b_th: Flow(variable_costs=parameters[self.name]['opex'])},
            conversion_factors={
                sub_b_th: parameters[self.name]['efficiency'] / 100}
        )
        gas_heating.pf = (
            parameters['General']['pf_gas'] /
            parameters[self.name]['efficiency'] * 100
        )
        gas_heating.pf_net = parameters['General']['pf_net']
        self.energysystem.add(gas_heating)

    @classmethod
    def get_data_label(cls, nodes, suffix=False):
        if not suffix:
            if nodes[1] is not None and nodes[1].name.endswith('gas_heating'):
                return 'Gasheizung'
            elif (
                    nodes[0] is not None and
                    nodes[0].name.endswith('gas_heating')
            ):
                return 'Gasheizung'
            else:
                return super(Scenario, cls).get_data_label(nodes)
        else:
            if nodes[1] is not None and nodes[1].name.endswith('gas_heating'):
                return ' (Gas)'
            elif (
                    nodes[0] is not None and
                    nodes[0].name.endswith('gas_heating')
            ):
                return ' (OPEX)'
            else:
                return super(Scenario, cls).get_data_label(nodes, suffix=True)
