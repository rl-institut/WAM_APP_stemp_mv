def calc_hp_heating_supply_temp(temp, heating_system, **kwargs):
    """
    Generates an hourly supply temperature profile depending on the ambient
    temperature.
    For ambient temperatures below t_heat_period the supply temperature
    increases linearly to t_sup_max with decreasing ambient temperature.
    Parameters
    temp -- pandas Series with ambient temperature
    heating_system -- string specifying the heating system (floor heating or
        radiator)
    """
    # outdoor temp upto which is heated:
    t_heat_period = kwargs.get("t_heat_period", 20)
    # design outdoor temp:
    t_amb_min = kwargs.get("t_amb_min", -14)

    # minimum and maximum supply temperature of heating system
    if heating_system == "floor heating":
        t_sup_max = kwargs.get("t_sup_max", 35)
        t_sup_min = kwargs.get("t_sup_min", 20)
    elif heating_system == "radiator":
        t_sup_max = kwargs.get("t_sup_max", 55)
        t_sup_min = kwargs.get("t_sup_min", 20)
    else:
        t_sup_max = kwargs.get("t_sup_max", 55)
        t_sup_min = kwargs.get("t_sup_min", 20)

    # calculate parameters for linear correlation for supply temp and
    # ambient temp
    slope = (t_sup_min - t_sup_max) / (t_heat_period - t_amb_min)
    y_intercept = t_sup_max - slope * t_amb_min

    # calculate supply temperature
    t_sup_heating = slope * temp + y_intercept
    t_sup_heating[t_sup_heating < t_sup_min] = t_sup_min
    t_sup_heating[t_sup_heating > t_sup_max] = t_sup_max

    return t_sup_heating


def cop_heating_floor(temp, type_hp, **kwargs):
    """
    Returns the COP of a heat pump for heating.
    Parameters
    temp -- pandas Series with ambient or brine temperature
    type_hp -- string specifying the heat pump type (air or brine)
    """
    cop_max = kwargs.get("cop_max", 7)
    if type_hp == "air":
        eta_g = kwargs.get("eta_g", 0.3)  # COP/COP_max
    elif type_hp == "brine":
        eta_g = kwargs.get("eta_g", 0.4)  # COP/COP_max
    else:
        eta_g = kwargs.get("eta_g", 0.4)  # COP/COP_max
    # get supply temperatures
    t_sup_fh = calc_hp_heating_supply_temp(temp, "floor heating")

    # calculate COP for floor heating and radiators
    cop_hp_heating_fh = eta_g * ((273.15 + t_sup_fh) / (t_sup_fh - temp))
    cop_hp_heating_fh[cop_hp_heating_fh > cop_max] = cop_max

    cop_hp_heating_fh.clip(lower=0.0, inplace=True)

    return cop_hp_heating_fh
