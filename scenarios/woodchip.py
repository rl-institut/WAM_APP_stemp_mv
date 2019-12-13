from oemof.solph import Flow, Transformer, Bus, Investment
from oemof.tools.economics import annuity

from stemp.scenarios import basic_setup
from stemp.scenarios.basic_setup import AdvancedLabel


class Scenario(basic_setup.PrimaryInputScenario):
    name = "Woodchip"
    needed_parameters = {
        "General": ["wacc", "woodchip_price"],
        "Woodchip": [
            "lifetime",
            "capex",
            "opex",
            "efficiency",
            "co2_emissions",
            "min_size",
        ],
        "demand": ["index", "type"],
    }

    def __init__(self, **parameters):
        self.b_woodchip = None
        super(Scenario, self).__init__(**parameters)

    def create_energysystem(self, **parameters):
        super(Scenario, self).create_energysystem()

        # Create woodchip bus
        self.b_woodchip = Bus(
            label=AdvancedLabel("b_woodchip", type="Bus"), balanced=False
        )
        self.energysystem.add(self.b_woodchip)

        # Add households separately or as whole district:
        self.add_households(parameters)

    def add_technology(self, demand, timeseries, parameters):
        # Get investment parameters:
        wacc = parameters["General"]["wacc"] / 100
        capex = parameters[self.name]["capex"]
        lifetime = parameters[self.name]["lifetime"]
        epc = annuity(capex, lifetime, wacc)

        # Get subgrid busses:
        invest = Investment(ep_costs=epc)
        invest.capex = capex
        woodchip_heating = Transformer(
            label=AdvancedLabel(
                f"{demand.name}_woodchip_heating",
                type="Transformer",
                tags=("primary_source",),
            ),
            inputs={
                self.b_woodchip: Flow(
                    variable_costs=parameters["General"]["woodchip_price"],
                    investment=invest,
                    is_fossil=True,
                    co2_emissions=parameters[self.name]["co2_emissions"],
                    min_size=(
                        parameters[self.name]["min_size"]
                        / (parameters[self.name]["efficiency"] / 100)
                    ),
                )
            },
            outputs={self.sub_b_th: Flow(variable_costs=parameters[self.name]["opex"])},
            conversion_factors={
                self.sub_b_th: parameters[self.name]["efficiency"] / 100
            },
        )
        woodchip_heating.pf = (
            parameters["General"]["pf_wood"] / parameters[self.name]["efficiency"] * 100
        )
        woodchip_heating.pf_net = parameters["General"]["pf_net"]
        self.energysystem.add(woodchip_heating)

    @classmethod
    def get_data_label(cls, nodes, suffix=False):
        if nodes[1] is not None and nodes[1].name.endswith("woodchip_heating"):
            return "Brennstoffkosten"
        elif nodes[0] is not None and nodes[0].name.endswith("woodchip_heating"):
            return "Betriebskosten"
        else:
            return super(Scenario, cls).get_data_label(nodes)
