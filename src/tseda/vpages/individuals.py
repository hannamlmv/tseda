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
import pandas as pd

from tseda.datastore import IndividualsTable, SampleSetsTable

from .core import View
from .map import GeoMap


class IndividualsPage(View):
    key = "individuals"
    title = "Individuals"
    individuals_table = param.ClassSelector(class_=IndividualsTable)
    sample_sets_table = param.ClassSelector(class_=SampleSetsTable)
    combined_table = param.ClassSelector(class_=IndividualsTable)

    geomap = param.ClassSelector(class_=GeoMap)

    mod_update_button = pn.widgets.Button(name="Update")


    def combine_tables(self):
        """Combine individuals and sample sets table."""
        combined = pd.merge(
            self.individuals_table.data.rx.value,
            self.sample_sets_table.data.rx.value,
            left_on="sample_set_id",
            right_index=True,
            suffixes=("_indiv", "_sample"),
        )
        combined.reset_index(inplace=True)
        combined["id"] = combined.index
        combined.rename(
            columns={"index": "id"}, inplace=True
        )  
        return combined

    def __init__(self, **params):
        super().__init__(**params)
        self.individuals_table = self.datastore.individuals_table
        self.sample_sets_table = self.datastore.sample_sets_table
        combined_data = self.combine_tables()
        combined_columns = [
            "color",
            "sample_set_id",
            "name_sample",
            "population",
            "name_indiv",
            "selected",
            "longitude",
            "latitude",
        ]
        self.combined_table = IndividualsTable(
            table=combined_data, columns=combined_columns
        )
        # print(self.combined_table.data.rx.value)

        self.geomap = GeoMap(datastore=self.datastore)

    @pn.depends("mod_update_button.value")
    def __panel__(self):
        return pn.Column(self.geomap, self.combined_table)

    def sidebar(self):
        return pn.Column(
            self.geomap.sidebar,
            self.combined_table.options_sidebar,
            self.combined_table.modification_sidebar,
        )
