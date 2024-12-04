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
    individuals_table = param.ClassSelector(class_=IndividualsTable) # for debugging
    sample_sets_table = param.ClassSelector(class_=SampleSetsTable) # for debugging
    geomap = param.ClassSelector(class_=GeoMap)
    combined_table = pn.widgets.DataFrame()

    # imported table settings
    columns = param.List(default=[], doc="Columns for the table")
    editors = param.Dict(default={}, doc="Column editors")
    formatters = param.Dict(default={}, doc="Column formatters")
    page_size = param.Selector(
        objects=[10, 20, 50, 100, 200, 500],
        default=20,
        doc="Number of rows per page to display",
    )
    filters = param.Dict()

    # imported sidebar settings  
    sample_select = pn.widgets.MultiChoice()
    selected = param.List()
    mod_update_button = pn.widgets.Button(name="Update")


    def __init__(self, **params):
        super().__init__(**params)
        self.combined_table = self.datastore.combine_tables

        self.individuals_table = self.datastore.individuals_table
        self.sample_sets_table = self.datastore.sample_sets_table
        self.geomap = GeoMap(datastore=self.datastore)
        self.sample_select = self.individuals_table.sample_select
        self.selected = list(self.individuals_table.data.rx.value.selected)

        self.editors = {k: None for k in self.combined_table.columns}
        self.editors["sample_set_id"] = {
            "type": "number",
            "valueLookup": True,
        }
        self.editors["selected"] = {
            "type": "list",
            "values": [False, True],
            "valuesLookup": True,
        }
        self.formatters = self.individuals_table.formatters
        self.filters = self.individuals_table.filters
        self.page_size = self.individuals_table.page_size
        self.mod_update_button = self.individuals_table.mod_update_button

    # Triggers same thing twice, needed to stay up to date
    @pn.depends("selected",
                "sample_select.value",
                "page_size",
                "mod_update_button",
                "individuals_table.page_size",
                "individuals_table.sample_select.value", 
                "individuals_table.mod_update_button.value")
    def __panel__(self):
        self.selected = list(self.individuals_table.data.rx.value.selected)
        self.page_size = self.individuals_table.page_size
        self.mod_update_button = self.individuals_table.mod_update_button

        self.combined_table = self.datastore.combine_tables
        pn.bind(self.datastore.combine_tables,
                self.combined_table,
                )
        
        table = pn.widgets.Tabulator(
            self.combined_table,
            pagination="remote",
            layout="fit_columns",
            selectable=True,
            page_size=self.page_size,
            formatters=self.formatters,
            editors=self.editors,
            margin=10,
            text_align={col: "right" for col in self.combined_table.columns},
            header_filters=self.filters,
        )
        
        # Hidden row added because panel only updates changes to widgets
        # depending on individuals_table if individuals_table is rendered
        hidden_row = pn.Row(self.individuals_table, visible=False) 
        return pn.Column( 
            hidden_row,
            self.geomap,
            pn.pane.Markdown(
                "**Map** - Displays the geographical locations where samples "
                "were collected and visually represents their group sample "
                "affiliations through colors.",
                sizing_mode="stretch_width",
            ),
            table

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
