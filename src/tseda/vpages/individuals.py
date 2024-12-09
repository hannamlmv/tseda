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
    key = "individuals and sets"
    title = "Individuals & sets"
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
            pn.Row(
                pn.Column(
                    pn.pane.HTML(
                        "<h2 style='margin: 0;'>Geomap</h2>",
                        sizing_mode="stretch_width",
                    ),
                    pn.Row(self.geomap, min_width=400),
                ),
                pn.Spacer(sizing_mode="stretch_width", max_width=50),
                pn.Column(
                    self.sample_sets_table,
                    sizing_mode="stretch_width",
                    max_width=400,
                ),
            ),
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
                "<h2 style='margin: 0;'>Individuals & sets</h2>",
                sizing_mode="stretch_width",
            ),
            pn.pane.Markdown(
                (
                    "This section allows you to manage and explore"
                    "individual samples in your dataset "
                    "and customize Sample Sets.<br><br>"
                    "Use the controls below to customize the plots,"
                    "adjust parameters, and add new samples."
                ),
                sizing_mode="stretch_width",
            ),
            self.geomap.sidebar,
            self.sample_sets_table.sidebar,
            self.individuals_table.options_sidebar,
            self.individuals_table.modification_sidebar,
        )
