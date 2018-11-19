
from django.views.generic import TemplateView

from stemp import queries


class ManageView(TemplateView):
    template_name = 'stemp/manage.html'

    def get_context_data(self, info=''):
        return {'info': info}

    def post(self, request):
        if 'reload_scenarios' in request.POST:
            queries.delete_scenarios()
            queries.insert_scenarios()
            info = 'Scenarios reloaded!'
        elif 'recreate_oep_tables' in request.POST:
            queries.delete_oep_tables()
            queries.create_oep_tables()
            info = 'Tables recreated!'
        elif 'insert_dhw_timeseries' in request.POST:
            queries.insert_dhw_timeseries()
            info = 'DHW Timeseries inserted.'
        elif 'insert_heat_demand' in request.POST:
            queries.insert_heat_demand()
            info = 'Heat demand inserted.'
        elif 'insert_pv_and_temp' in request.POST:
            queries.insert_pv_and_temp()
            info = 'PV and Temperature inserted.'
        else:
            info = 'Did not found matching command...'
        context = self.get_context_data(info)
        return self.render_to_response(context)
