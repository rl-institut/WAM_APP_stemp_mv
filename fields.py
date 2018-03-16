
from django.forms import Field
from stemp.widgets import HouseholdWidget


class HouseholdField(Field):
    widget = HouseholdWidget

    def __init__(self, hh_name, count=1):
        self.hh_name = hh_name
        self.count = count
        super(HouseholdField, self).__init__()

    def widget_attrs(self, widget):
        """
        Given a Widget instance (*not* a Widget class), returns a dictionary of
        any HTML attributes that should be added to the Widget, based on this
        Field.
        """
        return {
            'hh_name': self.hh_name,
            'count': self.count
        }