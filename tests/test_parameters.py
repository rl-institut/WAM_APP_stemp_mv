
import os
from django.test import Client
from django.core.wsgi import get_wsgi_application

# Change path:
kopy_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
os.chdir(kopy_path)

os.environ['DJANGO_DATABASE'] = 'default'
os.environ['DJANGO_SETTINGS_MODULE'] = 'kopy.settings'
application = get_wsgi_application()


client = Client()


def test_select_view():
    select = client.post(
        '/energysystem/select/',
        {'scenario': 'scenarios/heat_scenario'}
    )
    assert select.status_code == 302


def test_parameter_view():
    parameter = client.get('/energysystem/parameter/')
    assert parameter.status_code == 200

    parameter = client.post('/energysystem/parameter/', {'switch': 1})
    assert parameter.status_code == 302
