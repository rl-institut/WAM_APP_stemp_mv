
from django.forms import Field
from stemp.models import Household
from stemp.widgets import HouseholdWidget, SubmitWidget


class HouseholdField(Field):
    widget = HouseholdWidget

    def __init__(self, hh, count=1, in_district=False):
        self.household = hh
        self.count = count
        self.in_district = in_district
        super(HouseholdField, self).__init__()

    def widget_attrs(self, widget):
        """
        Given a Widget instance (*not* a Widget class), returns a dictionary of
        any HTML attributes that should be added to the Widget, based on this
        Field.
        """
        return {
            'household': self.household,
            'count': self.count,
            'in_district': self.in_district,
            'deletable': True
        }


class SubmitField(Field):
    def __init__(self, widget=SubmitWidget, **kwargs):
        super(SubmitField, self).__init__(widget=widget, **kwargs)
