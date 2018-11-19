
from wam.admin import wam_admin_site
from stemp import models

# Register load db:
wam_admin_site.register(models.District)
wam_admin_site.register(models.Household)
wam_admin_site.register(models.DistrictHouseholds)
wam_admin_site.register(models.HeatProfile)

# Register simulations
wam_admin_site.register(models.Scenario)
wam_admin_site.register(models.Parameter)
wam_admin_site.register(models.Simulation)
