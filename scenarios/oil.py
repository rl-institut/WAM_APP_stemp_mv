
from oemof.solph import Flow, Transformer, Bus, Investment
from oemof.tools.economics import annuity

from stemp.scenarios import basic_setup
from stemp.scenarios.basic_setup import AdvancedLabel


class Scenario(basic_setup.PrimaryInputScenario):
    name = 'Oil'
    needed_parameters = {
        'General': ['wacc', 'oil_price', 'oil_rate'],
        'Oil': ['lifetime', 'capex', 'opex', 'efficiency', 'co2_emissions'],
        'demand': ['index', 'type']
    }
    
    def create_energysystem(self, **parameters):
        super(Scenario, self).create_energysystem()
    
        # Create oil bus
        b_oil = Bus(label=AdvancedLabel("b_oil", type='Bus'), balanced=False)
        self.energysystem.add(b_oil)
    
        # Add households separately or as whole district:
        self.add_households(
            parameters
        )    
    
    def add_technology(self, demand, timeseries, parameters):
        # Get investment parameters:
        wacc = parameters['General']['wacc'] / 100
        capex = parameters[self.name]['capex']
        lifetime = parameters[self.name]['lifetime']
        epc = annuity(capex, lifetime, wacc)
        avg_oil_price = self.average_cost_per_year(
            parameters['General']['oil_price'],
            lifetime,
            parameters['General']['oil_rate']
        )
    
        # Get subgrid busses:
        sub_b_th = self.find_element_in_groups(f'b_demand_th')
        b_oil = self.find_element_in_groups('b_oil')
        invest = Investment(ep_costs=epc)
        invest.capex = capex
        oil_heating = Transformer(
            label=AdvancedLabel(
                f'{demand.name}_oil_heating',
                type='Transformer',
                tags=('primary_source', )
            ),
            inputs={
                b_oil: Flow(
                    variable_costs=avg_oil_price,
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
        oil_heating.pf = (
            parameters['General']['pf_oil'] /
            parameters[self.name]['efficiency'] * 100
        )
        oil_heating.pf_net = parameters['General']['pf_net']
        self.energysystem.add(oil_heating)

    @classmethod
    def get_data_label(cls, nodes):
        if nodes[1] is not None and nodes[1].name.endswith('oil_heating'):
            return 'Brennstoffkosten'
        elif (
                nodes[0] is not None and
                nodes[0].name.endswith('oil_heating')
        ):
            return 'Betriebskosten'
        else:
            return super(Scenario, cls).get_data_label(nodes)
