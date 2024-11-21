"""Individuals editor page.

Panel showing a simple individuals editor page. The page consists of
two main components: a map showing the distribution of individuals
and a table showing the individuals.

The individuals table allows the user to toggle individuals for
inclusion/exclusion, and reassign individuals to new sample set
combinations.
"""

import panel as pn
import param

from tseda.datastore import IndividualsTable

from .core import View
from .map import GeoMap


class IndividualsPage(View):
    key = "individuals"
    title = "Individuals"
    data = param.ClassSelector(class_=IndividualsTable)
    geomap = param.ClassSelector(class_=GeoMap)
    selection = pn.widgets.MultiChoice()

    def __init__(self, **params):
        super().__init__(**params)
        self.data = self.datastore.individuals_table
        self.selection = self.datastore.individuals_table.sample_select
        self.geomap = GeoMap(datastore=self.datastore)

    @pn.depends("selection.value")
    def __panel__(self):
        return pn.Column(self.geomap, self.data)

    def sidebar(self):
        return pn.Column(
            self.geomap.sidebar,
            self.data.options_sidebar,
            self.data.modification_sidebar,
        )
