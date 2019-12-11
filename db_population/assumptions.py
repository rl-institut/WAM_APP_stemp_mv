from meta.models import Category, Source, Assumption
from stemp import constants
from stemp.db_population.population_utils import get_meta_from_json


def insert_assumptions():
    pv()
    warmwater()
    primary_factors()


def pv():
    pv_category = Category(
        name="Photovoltaik",
        description="Parameter für Photovoltaikanlagen",
    )
    pv_category.save()
    pv_source = Source(
        meta_data=get_meta_from_json("pv", encoding="ISO-8859-1"),
        app_name="stemp",
        category=pv_category,
    )
    pv_source.save()
    Assumption(
        name="Investitionskosten: PV",
        description="Investitionskosten für Photovoltaikanlagen",
        value=1300,
        unit="€/kW",
        app_name="stemp",
        category=pv_category,
        source=pv_source,
    )
    Assumption(
        name="Betriebskosten: PV",
        description="Betriebskosten für Photovoltaikanlagen",
        value=32.5,
        unit="€/kW/a",
        app_name="stemp",
        category=pv_category,
        source=pv_source,
    )
    Assumption(
        name="Lebenszeit: PV",
        description="Lebenszeit für Photovoltaikanlagen",
        value=25,
        unit="Jahre",
        app_name="stemp",
        category=pv_category,
        source=pv_source,
    )


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
