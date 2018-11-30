
from stemp.scenarios import bhkw


BHKW_SIZE_PEAK_FACTOR = 3.33


class Scenario(bhkw.Scenario):
    name = 'BIO_BHKW'
    needed_parameters = {
        'General': ['wacc', 'gas_price', 'gas_rate', 'bhkw_feedin_tariff'],
        'BIO_BHKW': [
            'capex', 'lifetime', 'conversion_factor_el',
            'conversion_factor_th', 'co2_emissions', 'minimal_load'
        ],
        'demand': ['index', 'type']
    }

    @classmethod
    def add_dynamic_parameters(cls, scenario, parameters):
        demand = cls.get_demand(
            scenario.session.demand_type,
            scenario.session.demand_id
        )
        max_heat_demand = max(demand.annual_heat_demand())
    
        # Estimate bhkw size:
        bhkw_size = max_heat_demand * BHKW_SIZE_PEAK_FACTOR
    
        # Get capex:
        if bhkw_size < 10:
            raise IndexError(f'No BHKW-capex found for size {bhkw_size}kW')
        elif 10 <= bhkw_size < 100:
            capex = 10.267 * bhkw_size ** - 0.497 * 1e3
        elif 100 <= bhkw_size < 1000:
            capex = 4.276 * bhkw_size ** - 0.325 * 1e3
        elif 1000 <= bhkw_size < 9000:
            capex = 1.0001 * bhkw_size ** - 0.117
        else:
            raise IndexError(f'No BHKW-capex found for size {bhkw_size}kW')
    
        # Get eff:
        if bhkw_size < 10:
            raise IndexError(
                f'No BHKW-efficiency found for size {bhkw_size}kW')
        elif 10 <= bhkw_size < 100:
            eff = 21.636 * bhkw_size ** 0.1149
        elif 100 <= bhkw_size < 1000:
            eff = 29.667 * bhkw_size ** 0.0503
        elif 1000 <= bhkw_size < 9000:
            eff = 31.577 * bhkw_size ** 0.0385
        else:
            raise IndexError(
                f'No BHKW-efficiency found for size {bhkw_size}kW')
    
        parameters[cls.name]['capex'] = (
            parameters[cls.name]['capex'].new_child({'value': str(capex)}))
        parameters[cls.name]['conversion_factor_el'] = (
            parameters[cls.name]['conversion_factor_el'].new_child(
                {'value': str(int(eff))}
            )
        )
