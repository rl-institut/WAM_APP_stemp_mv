import logging

from meta.models import Category, Source, Assumption
from stemp import constants
from stemp.db_population.population_utils import get_meta_from_json


def delete_assumptions():
    Assumption.objects.filter(app_name="stemp").delete()
    Source.objects.filter(app_name="stemp").delete()


def insert_assumptions():
    technology_category = Category(
        name="Heiztechnologien", description="Parameter für Heiztechnologien",
    )
    technology_category.save()
    net()
    gas(technology_category)
    oil(technology_category)
    woodchip(technology_category)
    bhkw(technology_category)
    pv(technology_category)
    hp(technology_category)
    warmwater()
    primary_factors()


def net():
    net_category = Category(name="Stromnetz", description="Annahmen für das Stromnetz",)
    net_category.save()
    net_source = Source(
        meta_data=get_meta_from_json("net", encoding="ISO-8859-1"),
        app_name="stemp",
        category=net_category,
    )
    net_source.save()

    Assumption(
        name="Netzkosten",
        description="Netznutzungsentgelt in E/kWh",
        value=0.23,
        unit="€/kWh",
        app_name="stemp",
        category=net_category,
        source=net_source,
    ).save()


def gas(category):
    gas_source = Source(
        meta_data=get_meta_from_json("gas", encoding="ISO-8859-1"),
        app_name="stemp",
        category=category,
    )
    gas_source.save()

    assumption_category = Category(
        name="Gasheizung", description="Parameter für die Gasheizung",
    )
    assumption_category.save()
    Assumption(
        name="Investitionskosten",
        description=(
            "Investitionskosten für die Gasheizung. "
            "Annahme berechnet auf Grundlage von BDEW-Quelle (S. 46, 6-FH_typisch_03 Erdgas): "
            "3800€ (Wärmeerzeuger) / 17.5 kW (Heizlast) ~= 300 €/kW (aufgerundet, da Daten aus Jahr 2016)"
        ),
        value=300,
        unit="€/kW",
        app_name="stemp",
        category=assumption_category,
        source=gas_source,
    ).save()
    Assumption(
        name="Erdgaspreis",
        description="Preis für Erdgas in €/kWh",
        value=0.057,
        unit="€/kWh",
        app_name="stemp",
        category=assumption_category,
        source=gas_source,
    ).save()
    Assumption(
        name="Gaspreis-Steigerungsrate",
        description="Gaspreis-Steigerungsrate pro Jahr ",
        value=3,
        unit="%",
        app_name="stemp",
        category=assumption_category,
        source=gas_source,
    ).save()
    Assumption(
        name="Lebenszeit",
        description="Lebenszeit für Gasheizungen",
        value=20,
        unit="Jahre",
        app_name="stemp",
        category=assumption_category,
        source=gas_source,
    ).save()
    Assumption(
        name="Effizienz",
        description="Brennwert der Gasheizung",
        value=84,
        unit="%",
        app_name="stemp",
        category=assumption_category,
        source=gas_source,
    ).save()
    Assumption(
        name="CO2 Emissionsfaktor",
        description="CO2 Emissionen",
        value=228,
        unit="g/kWh",
        app_name="stemp",
        category=assumption_category,
        source=gas_source,
    ).save()
    logging.info(f"Gas assumptions uploaded.")


def oil(category):
    oil_source = Source(
        meta_data=get_meta_from_json("oil", encoding="ISO-8859-1"),
        app_name="stemp",
        category=category,
    )
    oil_source.save()
    assumption_category = Category(
        name="Ölheizung", description="Parameter für die Ölheizung",
    )
    assumption_category.save()
    Assumption(
        name="Investitionskosten",
        description=(
            "Investitionskosten für die Ölheizung. "
            "Annahme berechnet auf Grundlage von BDEW-Quelle (S. 46, 6-FH_typisch_07 Heizöl): "
            "6000€ (Wärmeerzeuger) / 17.5 kW (Heizlast) ~= 400 €/kW (aufgerundet, da Daten aus Jahr 2016)"
        ),
        value=400,
        unit="€/kW",
        app_name="stemp",
        category=assumption_category,
        source=oil_source,
    ).save()
    Assumption(
        name="Heizölpreis (Einzelhaushalt)",
        description=(
            "Preis für Heizöl in €/kWh. "
            "Es findet sich ein Heizölpreis von 0.065 €/kwh, "
            "für einen Einzelhaushalt wird ein leicht verteuerter Preis angenommen."
        ),
        value=0.067,
        unit="€/kWh",
        app_name="stemp",
        category=assumption_category,
        source=oil_source,
    ).save()
    Assumption(
        name="Heizölpreis (Viertel)",
        description=(
            "Preis für Heizöl in €/kWh. "
            "Es findet sich ein Heizölpreis von 0.065 €/kwh, "
            "für ein Viertel wird ein leicht verbilligter Preis angenommen."
        ),
        value=0.064,
        unit="€/kWh",
        app_name="stemp",
        category=assumption_category,
        source=oil_source,
    ).save()
    Assumption(
        name="Heizölpreis-Steigerungsrate",
        description="Heizölpreis-Steigerungsrate pro Jahr ",
        value=5,
        unit="%",
        app_name="stemp",
        category=assumption_category,
        source=oil_source,
    ).save()
    Assumption(
        name="Lebenszeit",
        description="Lebenszeit für Ölheizungen",
        value=20,
        unit="Jahre",
        app_name="stemp",
        category=assumption_category,
        source=oil_source,
    ).save()
    Assumption(
        name="Effizienz",
        description="Brennwert der Ölheizung",
        value=88,
        unit="%",
        app_name="stemp",
        category=assumption_category,
        source=oil_source,
    ).save()
    Assumption(
        name="CO2 Emissionsfaktor",
        description="CO2 Emissionen",
        value=312,
        unit="g/kWh",
        app_name="stemp",
        category=assumption_category,
        source=oil_source,
    ).save()
    logging.info(f"Oil assumptions uploaded.")


def woodchip(category):
    woodchip_source = Source(
        meta_data=get_meta_from_json("woodchip", encoding="ISO-8859-1"),
        app_name="stemp",
        category=category,
    )
    woodchip_source.save()
    assumption_category = Category(
        name="Holzhackschnitzelheizung",
        description="Parameter für die Holzhackschnitzelheizung",
    )
    assumption_category.save()
    Assumption(
        name="Investitionskosten",
        description=(
            "Investitionskosten für die Holzhackschnitzel-Heizung. "
            "Annahme berechnet auf Grundlage von BDEW-Quelle (S. 52, 6-FH_typisch_13 Pellets): "
            "(15200 € (Wärmeerzeuger) + 2400 € (Regelung) + 4700 € (Brennstofflagerung) ) / 17.5 kW (Heizlast) ~= 1300 €/kW (aufgerundet, da Daten aus Jahr 2016)"
        ),
        value=1300,
        unit="€/kW",
        app_name="stemp",
        category=assumption_category,
        source=woodchip_source,
    ).save()
    Assumption(
        name="Holzhackschnitzel-Preis",
        description="Preis für Holzhackschnitzel in €/kWh",
        value=0.032,
        unit="€/kWh",
        app_name="stemp",
        category=assumption_category,
        source=woodchip_source,
    ).save()
    Assumption(
        name="Lebenszeit",
        description="Lebenszeit für Holzhackschnitzel-Heizungen",
        value=20,
        unit="Jahre",
        app_name="stemp",
        category=assumption_category,
        source=woodchip_source,
    ).save()
    Assumption(
        name="Effizienz",
        description="Brennwert der Holzhackschnitzel-Heizungen",
        value=90,
        unit="%",
        app_name="stemp",
        category=assumption_category,
        source=woodchip_source,
    ).save()
    Assumption(
        name="CO2 Emissionsfaktor",
        description="CO2 Emissionen der Holzhackschnitzel-Heizung",
        value=29,
        unit="g/kWh",
        app_name="stemp",
        category=assumption_category,
        source=woodchip_source,
    ).save()
    logging.info(f"Woodchip assumptions uploaded.")


def bhkw(category):
    bhkw_source = Source(
        meta_data=get_meta_from_json("bhkw", encoding="ISO-8859-1"),
        app_name="stemp",
        category=category,
    )
    bhkw_source.save()
    assumption_category = Category(
        name="Blockheizkraftwerk (BHKW, Erdgas & Biogas)",
        description="Parameter für Blockheizkraftwerke",
    )
    assumption_category.save()
    Assumption(
        name="Investitionskosten",
        description=(
            "Investitionskosten für die Erdgas- und Biogas-BHKWs. "
            "Die Investitionskosten sind als Kostenfunktion abhängig von der Leistung der Anlage hinterlegt. "
            "Die Daten für die Kostenfunktion stammen von ASUE (siehe Quelle)."
        ),
        value="f(Leistung)",
        unit="€/kW",
        app_name="stemp",
        category=assumption_category,
        source=bhkw_source,
    ).save()
    Assumption(
        name="Lebenszeit",
        description="Lebenszeit für BHKWs",
        value=15,
        unit="Jahre",
        app_name="stemp",
        category=assumption_category,
        source=bhkw_source,
    ).save()
    Assumption(
        name="Wirkungsgrad (elektrisch)",
        description=(
            "Elektrischer Wirkungsgrad des BHKWS."
            "Der elektrische Wirkungsgrad ist als Funktion abhängig von der Leistung der Anlage hinterlegt. "
            "Die Daten für die Funktion stammen von ASUE (siehe Quelle)."
        ),
        value="f(Leistung)",
        unit="%",
        app_name="stemp",
        category=assumption_category,
        source=bhkw_source,
    ).save()
    Assumption(
        name="Wirkungsgrad (thermisch)",
        description="Thermischer Wirkungsgrad des BHKWS",
        value=55,
        unit="%",
        app_name="stemp",
        category=assumption_category,
        source=bhkw_source,
    ).save()
    Assumption(
        name="CO2 Emissionsfaktor (Erdgas-BHKW)",
        description="CO2 Emissionen eines Erdgas-BHKWs",
        value=228,
        unit="g/kWh",
        app_name="stemp",
        category=assumption_category,
        source=bhkw_source,
    ).save()
    Assumption(
        name="CO2 Emissionsfaktor (Biogas-BHKW)",
        description="CO2 Emissionen eines Biogas-BHKWs",
        value=71,
        unit="g/kWh",
        app_name="stemp",
        category=assumption_category,
        source=bhkw_source,
    ).save()
    Assumption(
        name="Minimallast (Erdgas-BHKW)",
        description=(
            "Das Ergas-BHKW muss eine Mindestleistung abrufen, "
            "d.h. die Anlage muss mindestens die angegeben Leistung bereitstellen."
        ),
        value=20,
        unit="%",
        app_name="stemp",
        category=assumption_category,
        source=bhkw_source,
    ).save()
    Assumption(
        name="Minimallast (Biogas-BHKW)",
        description=(
            "Das Biogas-BHKW muss eine Mindestleistung abrufen, "
            "d.h. die Anlage muss mindestens die angegeben Leistung bereitstellen."
        ),
        value=0,
        unit="%",
        app_name="stemp",
        category=assumption_category,
        source=bhkw_source,
    ).save()
    Assumption(
        name="Einspeisevergütung (BHKW)",
        description="Einspeisevergütung eines BHKW bei Einspeisung in das Stromnetz",
        value=0.08,
        unit="€/kWh",
        app_name="stemp",
        category=assumption_category,
        source=bhkw_source,
    ).save()
    logging.info(f"BHKW assumptions uploaded.")


def pv(category):
    pv_source = Source(
        meta_data=get_meta_from_json("pv", encoding="ISO-8859-1"),
        app_name="stemp",
        category=category,
    )
    pv_source.save()
    assumption_category = Category(
        name="Photovoltaik", description="Parameter für die Photovoltaikanlage",
    )
    assumption_category.save()
    Assumption(
        name="Investitionskosten",
        description="Investitionskosten für Photovoltaikanlagen",
        value=1300,
        unit="€/kW",
        app_name="stemp",
        category=assumption_category,
        source=pv_source,
    ).save()
    Assumption(
        name="Betriebskosten",
        description=(
            "Betriebskosten für Photovoltaikanlagen. "
            "Angenommen werden 2.5% der Investitionskosten"
        ),
        value=32.5,
        unit="€/kW/a",
        app_name="stemp",
        category=assumption_category,
        source=pv_source,
    ).save()
    Assumption(
        name="Lebenszeit",
        description="Lebenszeit für Photovoltaikanlagen",
        value=25,
        unit="Jahre",
        app_name="stemp",
        category=assumption_category,
        source=pv_source,
    ).save()
    Assumption(
        name="CO2 Emissionsfaktor",
        description="CO2 Emissionen eine Photovoltaikanlage",
        value=0,
        unit="g/kWh",
        app_name="stemp",
        category=assumption_category,
        source=pv_source,
    ).save()
    logging.info(f"PV assumptions uploaded.")


def hp(category):
    hp_source = Source(
        meta_data=get_meta_from_json("heatpump", encoding="ISO-8859-1"),
        app_name="stemp",
        category=category,
    )
    hp_source.save()
    assumption_category = Category(
        name="Luft-Wärmepumpe", description="Parameter für die Luft-Wärmepumpe",
    )
    assumption_category.save()
    Assumption(
        name="Investitionskosten",
        description="Investitionskosten für Luft-Wärmepumpen",
        value=1200,
        unit="€/kW",
        app_name="stemp",
        category=assumption_category,
        source=hp_source,
    ).save()
    Assumption(
        name="Lebenszeit",
        description="Lebenszeit für Luft-Wärmepumpen",
        value=20,
        unit="Jahre",
        app_name="stemp",
        category=assumption_category,
        source=hp_source,
    ).save()
    Assumption(
        name="CO2 Emissionsfaktor",
        description="CO2 Emissionen einer Luft-Wärmepumpe",
        value=476,
        unit="g/kWh",
        app_name="stemp",
        category=assumption_category,
        source=hp_source,
    ).save()
    Assumption(
        name="Wirkungsgrad (Warmwasser-Boiler)",
        description="Annahme für den Wirkungsgrad eines elektrischen Warmwasser-Boilers",
        value=90,
        unit="%",
        app_name="stemp",
        category=assumption_category,
        source=hp_source,
    ).save()
    logging.info(f"HP assumptions uploaded.")


def warmwater():
    # Warmwasser
    c_hot_water = Category(
        name="Warmwasser", description="Annahmen rund um den Warmwasserverbrauch"
    )
    c_hot_water.save()
    hot_water_energy_source = Source(
        meta_data=get_meta_from_json("hot_water_energy"),
        app_name="stemp",
        category=c_hot_water,
    )
    hot_water_energy_source.save()
    hot_water_energy = Assumption(
        name="Warmwasserenergie",
        description=(
            "Benötigte Energie um einen Liter Wasser von 5° auf 55° zu "
            "erhitzen. Dieser Wert wird benutzt, um den durch Warmwasser "
            "benötigten Wärmebedarf auszurechnen."
        ),
        value=constants.ENERGY_PER_LITER,
        unit="kWh/l",
        app_name="stemp",
        category=c_hot_water,
        source=hot_water_energy_source,
    )
    hot_water_energy.save()
    logging.info(f"Warmwwater assumptions uploaded.")


def primary_factors():
    # Primärfaktoren
    c_pf = Category(name="Primärenergie", description="Primärenergiefaktoren")
    c_pf.save()
    pf = Source(
        meta_data=get_meta_from_json("primärenergiefaktoren"),
        app_name="stemp",
        category=c_pf,
    )
    pf.save()
    Assumption(
        name="Primärenergiefaktor: Erdas",
        description="Primärenergiefaktor für Erdgas",
        value=1.1,
        unit="",
        app_name="stemp",
        category=c_pf,
        source=pf,
    ).save()
    Assumption(
        name="Primärenergiefaktor: Heizöl",
        description="Primärenergiefaktor für Heizöl",
        value=1.1,
        unit="",
        app_name="stemp",
        category=c_pf,
        source=pf,
    ).save()
    Assumption(
        name="Primärenergiefaktor: Biogas",
        description="Primärenergiefaktor für Biogas",
        value=0.5,
        unit="",
        app_name="stemp",
        category=c_pf,
        source=pf,
    ).save()
    Assumption(
        name="Primärenergiefaktor: Holz",
        description="Primärenergiefaktor für Holz",
        value=0.2,
        unit="",
        app_name="stemp",
        category=c_pf,
        source=pf,
    ).save()
    Assumption(
        name="Primärenergiefaktor: allgemeiner Strommix",
        description="Primärenergiefaktor für allgemeinen Strommix",
        value=2.4,
        unit="",
        app_name="stemp",
        category=c_pf,
        source=pf,
    ).save()
    Assumption(
        name="Primärenergiefaktor: Verdrängungsstrommix",
        description="Primärenergiefaktor für Verdrängungsstrommix",
        value=2.8,
        unit="",
        app_name="stemp",
        category=c_pf,
        source=pf,
    ).save()
    logging.info(f"Primary factor assumptions uploaded.")
