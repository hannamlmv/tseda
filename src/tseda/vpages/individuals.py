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

from tseda.datastore import IndividualsTable, SampleSetsTable

from .core import View
from .map import GeoMap


class IndividualsPage(View):
    key = "individuals"
    title = "Individuals"
    sample_sets_table = param.ClassSelector(class_=SampleSetsTable)
    individuals_table = param.ClassSelector(class_=IndividualsTable)

    geomap = param.ClassSelector(class_=GeoMap)

    def __init__(self, **params):
        super().__init__(**params)
        self.geomap = GeoMap(datastore=self.datastore)
        self.sample_sets_table = self.datastore.sample_sets_table
        self.individuals_table = self.datastore.individuals_table
        self.individuals_table.sample_sets_table = self.sample_sets_table

    def __panel__(self):
        return pn.Column(
            self.geomap,
            pn.pane.Markdown(
                "**Map** - Displays the geographical locations where samples "
                "were collected and visually represents their group sample "
                "affiliations through colors.",
                sizing_mode="stretch_width",
            ),
            self.individuals_table,
        )

    def sidebar(self):
        return pn.Column(
            pn.pane.HTML(
                "<h2 style='margin: 0;'>Individuals</h2>",
                sizing_mode="stretch_width",
            ),
            pn.pane.Markdown(
                (
                    "This section allows you to manage and explore "
                    "individual samples in your dataset.<br><br>"
                    "Use the controls below to customize the "
                    "plots and adjust parameters."
                ),
                sizing_mode="stretch_width",
            ),
            self.geomap.sidebar,
            self.individuals_table.options_sidebar,
            self.individuals_table.modification_sidebar,
            self.sample_sets_table.sidebar_table,
        )
