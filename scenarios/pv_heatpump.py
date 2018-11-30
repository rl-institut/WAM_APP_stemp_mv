
import pandas
import sqlahelper

from oemof.solph import Flow, Transformer, Investment, Source, Bus
from oemof.tools.economics import annuity

from stemp.oep_models import OEPTimeseries
from stemp.scenarios import basic_setup, heat
from stemp.scenarios.basic_setup import AdvancedLabel


def get_timeseries():
    session = sqlahelper.get_session()
    temp = session.query(OEPTimeseries).filter_by(
        name='Temperature').first().data
    pv = session.query(OEPTimeseries).filter_by(
        name='PV').first().data
    timeseries = pandas.DataFrame({'temp': temp, 'pv': pv})
    return timeseries


class Scenario(basic_setup.BaseScenario):
    name = 'PV_Heatpump'
    needed_parameters = {
        'General': ['wacc', 'pv_feedin_tariff', 'net_costs'],
        'PV': ['lifetime', 'capex', 'opex_fix'],
        'HP': ['lifetime', 'capex'],
        'demand': ['index', 'type']
    }

    def create_energysystem(self, **parameters):
        super(Scenario, self).create_energysystem()

        timeseries = get_timeseries()

        # Add households separately or as whole district:
        self.add_households(
            parameters,
            timeseries
        )

    def add_technology(self, demand, timeseries, parameters):
        # Get subgrid busses:
        sub_b_th = self.find_element_in_groups(f'b_{demand.name}_th')

        # Add electricity busses:
        sub_b_el = Bus(label=AdvancedLabel(
            f'b_{demand.name}_el', type='Bus', belongs_to=demand.name))
        b_el_net = Bus(
            label=AdvancedLabel('b_el_net', type='Bus'), balanced=False)
        self.energysystem.add(sub_b_el, b_el_net)

        # get investment parameters
        wacc = parameters['General']['wacc'] / 100

        # Add heat pump:
        capex = parameters['HP']['capex']
        lifetime = parameters['HP']['lifetime']
        epc = annuity(capex, lifetime, wacc)
        hp_invest = Investment(ep_costs=epc)
        hp_invest.capex = capex
        COP = heat.cop_heating(timeseries['temp'], type_hp='air')

        hp = Transformer(
            label=AdvancedLabel(
                f"{demand.name}_heat_pump",
                type='Transformer',
                belongs_to=demand.name
            ),
            inputs={
                sub_b_el: Flow(
                    investment=hp_invest,
                    co2_emissions=parameters['HP']['co2_emissions']
                )
            },
            outputs={sub_b_th: Flow()},
            conversion_factors={sub_b_th: COP}
        )

        # Add pv system:
        capex = parameters['PV']['capex']
        lifetime = parameters['PV']['lifetime']
        opex_fix = parameters['PV']['opex_fix']
        epc = annuity(capex, lifetime, wacc) + opex_fix
        pv_invest = Investment(ep_costs=epc, maximum=demand.max_pv_size)
        pv_invest.capex = capex
        pv = Source(
            label=AdvancedLabel(
                f"{demand.name}_pv",
                type='Source',
                belongs_to=demand.name
            ),
            outputs={
                sub_b_el: Flow(
                    actual_value=timeseries['pv'],
                    fixed=True,
                    investment=pv_invest,
                    co2_emissions=parameters['PV']['co2_emissions']
                )
            }
        )

        # Add transformer to get electricty from net for heat pump:
        t_net_el = Transformer(
            label=AdvancedLabel(
                f'transformer_net_to_{demand.name}_el',
                type='Transformer',
                belongs_to=demand.name
            ),
            inputs={
                b_el_net: Flow(
                    variable_costs=parameters['General']['net_costs']
                )
            },
            outputs={sub_b_el: Flow()},
        )

        # Add transformer to feed in pv to net:
        t_pv_net = Transformer(
            label=AdvancedLabel(
                f'transformer_from_{demand.name}_el',
                type='Transformer',
                belongs_to=demand.name
            ),
            inputs={
                sub_b_el: Flow(
                    variable_costs=-parameters['General']['pv_feedin_tariff']
                )
            },
            outputs={b_el_net: Flow()},
        )
        self.energysystem.add(
            hp,
            pv,
            t_pv_net,
            t_net_el
        )
