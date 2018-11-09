from django.contrib import admin
from stemp import models

# Register load db:
admin.site.register(models.District)
admin.site.register(models.Household)
admin.site.register(models.DistrictHouseholds)
admin.site.register(models.HeatProfile)

# Register simulations
admin.site.register(models.Scenario)
admin.site.register(models.Parameter)
admin.site.register(models.Simulation)
