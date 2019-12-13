from stemp.scenarios import bhkw


class Scenario(bhkw.Scenario):
    name = "BIO_BHKW"
    needed_parameters = {
        "General": ["wacc", "gas_price", "gas_rate", "bhkw_feedin_tariff"],
        "BIO_BHKW": [
            "capex",
            "lifetime",
            "conversion_factor_el",
            "conversion_factor_th",
            "co2_emissions",
            "minimal_load",
        ],
        "demand": ["index", "type"],
    }

    @staticmethod
    def get_bhkw_capex(bhkw_size):
        if bhkw_size < 10:
            raise IndexError(f"No BIO-BHKW-capex found for size {bhkw_size}kW")
        elif 10 <= bhkw_size < 100:
            capex = 10.267 * bhkw_size ** -0.497 * 1e3
        elif 100 <= bhkw_size < 1000:
            capex = 4.276 * bhkw_size ** -0.325 * 1e3
        elif 1000 <= bhkw_size < 9000:
            capex = 1.0001 * bhkw_size ** -0.117
        else:
            raise IndexError(f"No BIO-BHKW-capex found for size {bhkw_size}kW")
        return capex

    @staticmethod
    def get_bhkw_efficiency(bhkw_size):
        if bhkw_size < 10:
            raise IndexError(f"No BIO-BHKW-efficiency found for size {bhkw_size}kW")
        elif 10 <= bhkw_size < 100:
            eff = 21.636 * bhkw_size ** 0.1149
        elif 100 <= bhkw_size < 1000:
            eff = 29.667 * bhkw_size ** 0.0503
        elif 1000 <= bhkw_size < 9000:
            eff = 31.577 * bhkw_size ** 0.0385
        else:
            raise IndexError(f"No BIO-BHKW-efficiency found for size {bhkw_size}kW")
        return eff
