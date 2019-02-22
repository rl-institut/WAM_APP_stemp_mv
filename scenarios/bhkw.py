
from oemof.solph import Flow, Bus, Investment, Transformer
from oemof.tools.economics import annuity

from stemp.scenarios import basic_setup
from stemp.constants import BHKW_FULL_LOAD_HOURS
from stemp.scenarios.basic_setup import AdvancedLabel, pe


class Scenario(basic_setup.BaseScenario):
    name = 'BHKW'
    needed_parameters = {
        'General': ['wacc', 'gas_price', 'gas_rate', 'bhkw_feedin_tariff'],
        'BHKW': [
            'capex', 'lifetime', 'conversion_factor_el', 
            'conversion_factor_th', 'co2_emissions', 'minimal_load'
        ],
        'demand': ['index', 'type']
    }

    def __init__(self, **parameters):
        self.b_gas = None
        super(Scenario, self).__init__(**parameters)
    
    def create_energysystem(self, **parameters):
        super(Scenario, self).create_energysystem()
    
        # Create oil bus
        self.b_gas = Bus(
            label=AdvancedLabel("b_gas", type='Bus'),
            balanced=False
        )
        self.energysystem.add(self.b_gas)
    
        # Add households separately or as whole district:
        self.add_households(parameters)    
    
    def add_technology(self, demand, timeseries, parameters):
        # Add bus from bhkw to net:
        b_bhkw_el = Bus(label=AdvancedLabel('b_bhkw_el', type='Bus'))
        b_net_el = Bus(
            label=AdvancedLabel('b_net_el', type='Bus'), balanced=False)
    
        # Add transformer to feed in bhkw_el to net:
        t_bhkw_net = Transformer(
            label=AdvancedLabel(
                f'transformer_from_{demand.name}_el',
                type='Transformer',
            ),
            inputs={
                b_bhkw_el: Flow(
                    variable_costs=-parameters['General']['bhkw_feedin_tariff']
                )
            },
            outputs={b_net_el: Flow()},
        )
        self.energysystem.add(b_bhkw_el, b_net_el, t_bhkw_net)
    
        capex = parameters[self.name]['capex']
        lifetime = parameters[self.name]['lifetime']
        wacc = parameters['General']['wacc'] / 100
        epc = annuity(capex, lifetime, wacc)
        invest = Investment(
            ep_costs=epc, minimum=float(parameters[self.name]['min_size'])
        )
        invest.capex = capex
        avg_gas_price = self.average_cost_per_year(
            parameters['General']['gas_price'],
            lifetime,
            parameters['General']['gas_rate']
        )

        if self.name == 'BIO_BHKW':
            pf_gas = parameters['General']['pf_biogas']
        else:
            pf_gas = parameters['General']['pf_gas']
    
        bhkw = Transformer(
            label=AdvancedLabel(
                'bhkw',
                type='Transformer',
                tags=('bhkw',)
            ),
            inputs={
                self.b_gas: Flow(
                    variable_costs=avg_gas_price,
                    investment=invest,
                    min=(
                            parameters[self.name]['minimal_load'] /
                            parameters[self.name]['conversion_factor_th']
                    ),
                    is_fossil=True,
                    co2_emissions=parameters[self.name]['co2_emissions']
                )
            },
            outputs={
                b_bhkw_el: Flow(
                    pf=parameters['General']['pf_bhkw_el']
                ),
                self.sub_b_th: Flow(pf=pf_gas)
            },
            conversion_factors={
                b_bhkw_el: (
                    parameters[self.name]['conversion_factor_el'] / 100),
                self.sub_b_th: (
                    parameters[self.name]['conversion_factor_th'] / 100)
            }
        )
        self.energysystem.add(bhkw)
    
        # Additional gas for peak load
        capex = parameters['Gas']['capex']
        lifetime = parameters['Gas']['lifetime']
        epc = annuity(capex, lifetime, wacc)
        invest = Investment(ep_costs=epc)
        invest.capex = capex
        gas_heating = Transformer(
            label=AdvancedLabel(
                f'{demand.name}_gas_heating', type='Transformer'),
            inputs={
                self.b_gas: Flow(
                    variable_costs=avg_gas_price,
                    investment=invest,
                    is_fossil=True,
                    co2_emissions=parameters['Gas']['co2_emissions']
                )
            },
            outputs={
                self.sub_b_th: Flow(variable_costs=parameters['Gas']['opex'])
            },
            conversion_factors={
                self.sub_b_th: parameters['Gas']['efficiency'] / 100
            }
        )
        self.energysystem.add(gas_heating)

    @staticmethod
    def get_optimum_bhkw_size(demand):
        demand.sort_values(ascending=False, inplace=True)
        partial_load_right = demand.iloc[BHKW_FULL_LOAD_HOURS - 1:8760].sum()

        # Search for optimum bkhw-size starting at minimum (full-load-hours):
        x_start = BHKW_FULL_LOAD_HOURS - 2
        while True:
            bhkw_size = demand.iloc[x_start]
            partial_load_left = -(
                    demand.iloc[:BHKW_FULL_LOAD_HOURS] - bhkw_size
            ).clip(upper=0).sum()
            if partial_load_left > partial_load_right:
                break
            x_start -= 1
        return demand.iloc[x_start + 1]

    @staticmethod
    def get_bhkw_capex(bhkw_size):
        if bhkw_size < 1:
            capex = 9.585 * 1e3
        elif 1 <= bhkw_size < 10:
            capex = 9.585 * bhkw_size ** -0.542 * 1e3
        elif 10 <= bhkw_size < 100:
            capex = 5.438 * bhkw_size ** -0.351 * 1e3
        elif 100 <= bhkw_size < 1000:
            capex = 4.907 * bhkw_size ** -0.352 * 1e3
        elif 1000 <= bhkw_size < 19000:
            capex = 460.89 * bhkw_size ** -0.015
        else:
            raise IndexError(f'No BHKW-capex found for size {bhkw_size}kW')
        return capex

    @staticmethod
    def get_bhkw_efficiency(bhkw_size):
        # Get eff:
        if bhkw_size < 1:
            raise IndexError(
                f'No BHKW-efficiency found for size {bhkw_size}kW')
        elif 1 <= bhkw_size < 10:
            eff = 21.794 * bhkw_size ** 0.108
        elif 10 <= bhkw_size < 100:
            eff = 22.56 * bhkw_size ** 0.1032
        elif 100 <= bhkw_size < 1000:
            eff = 25.416 * bhkw_size ** 0.0732
        elif 1000 <= bhkw_size < 19000:
            eff = 29.627 * bhkw_size ** 0.0498
        else:
            eff = 29.627
        return eff

    @classmethod
    def add_dynamic_parameters(cls, scenario, parameters):
        demand = cls.get_demand(
            scenario.session.demand_type,
            scenario.session.demand_id
        ).annual_total_demand()

        bhkw_size = cls.get_optimum_bhkw_size(demand)
        capex = cls.get_bhkw_capex(bhkw_size)
        eff = cls.get_bhkw_efficiency(bhkw_size)

        parameters[cls.name]['min_size'] = {
            'value': str(round(bhkw_size)),
            'value_type': 'hidden',
            'unit': 'kW'
        }
        parameters[cls.name]['capex'] = (
            parameters[cls.name]['capex'].new_child(
                {'value': str(round(capex))}
            )
        )
        parameters[cls.name]['conversion_factor_el'] = (
            parameters[cls.name]['conversion_factor_el'].new_child(
                {'value': str(int(eff))}
            )
        )
        return parameters

    @classmethod
    def is_available(cls, demand):
        bhkw_size = cls.get_optimum_bhkw_size(demand.annual_total_demand())
        try:
            cls.get_bhkw_capex(bhkw_size)
            cls.get_bhkw_efficiency(bhkw_size)
        except IndexError:
            return False
        return True

    @classmethod
    def get_data_label(cls, nodes):
        if nodes[0].name == 'bhkw':
            return 'Stromgutschrift'
        elif (
                nodes[0].name.startswith('b_bhkw_el') and
                nodes[1] is not None and
                nodes[1].name.startswith('transformer_from')
        ):
            return 'Stromgutschrift'
        elif (
                nodes[1] is not None and
                (
                    nodes[1].name == 'bhkw' or
                    nodes[1].name.endswith('gas_heating')
                )
        ):
            return 'Brennstoffkosten'
        elif nodes[0].name.endswith('gas_heating'):
            return 'Betriebskosten'
        else:
            return super(Scenario, cls).get_data_label(nodes)

    @classmethod
    def calculate_primary_factor_and_energy(cls, param_results, node_results):
        # Find nodes:
        bhkw, b_bhkw_el = next(filter(
            lambda x: (
                x[0].name == 'bhkw' and
                x[1] is not None and
                x[1].name == 'b_bhkw_el'
            ),
            param_results.keys()
        ))
        b_demand_th, demand_node = next(filter(
            lambda x: (
                x[0].name == 'b_demand_th' and
                x[1] is not None
                and x[1].name == 'demand_th'
            ),
            param_results.keys()
        ))
        b_gas, _ = next(filter(
            lambda x: x[0].name == 'b_gas',
            param_results.keys()
        ))

        # Calculate thermic contribution to primary factor:
        demand = sum(
            node_results.result[demand_node]['input'].values())
        gas_input = sum(
            node_results.result[b_gas]['output'].values())
        el_output = node_results.result[bhkw]['output'][b_bhkw_el]
        pf_gas = param_results[(bhkw, b_demand_th)]['scalars']['pf']
        pf_net = param_results[(bhkw, b_bhkw_el)]['scalars']['pf']

        pf = (
            pf_gas * gas_input / demand -
            pf_net * (0.9 * el_output / demand - 0.05)
        )
        primary_energy = demand * pf
        return pe(energy=primary_energy, factor=pf)
