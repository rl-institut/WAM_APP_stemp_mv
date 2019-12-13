"""
Module to hold customized django fields
"""

from django.forms import Field
from stemp.widgets import HouseholdWidget, SubmitWidget


class HouseholdField(Field):
    """Field for households

    Is used in district list and summary. Shows current household and
    selected amounts.
    """
    widget = HouseholdWidget

    def __init__(self, hh, count=1, in_district=False):
        """
        Parameters:
            hh: Household
                Household to show in widget
            count: int
                Amount of households
            in_district: bool
                Does household belongs to district?
        """
        self.household = hh
        self.count = count
        self.in_district = in_district
        super(HouseholdField, self).__init__()

    def widget_attrs(self, widget):
        """
        Given a Widget instance (*not* a Widget class), returns a dictionary
        of any HTML attributes that should be added to the Widget, based on this
        Field.
        """
        return {
            'household': self.household,
            'count': self.count,
            'in_district': self.in_district,
            'deletable': True
        }


class SubmitField(Field):
    """Simple submit field to add submit input"""
    def __init__(self, widget=SubmitWidget, **kwargs):
        super(SubmitField, self).__init__(widget=widget, **kwargs)
