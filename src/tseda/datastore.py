import random

import daiquiri
import pandas as pd
import panel as pn
import param
from panel.viewable import Viewer
from tsbrowse import model

from tseda import config
from tseda.model import Individual, SampleSet

from .gnn import windowed_genealogical_nearest_neighbours

logger = daiquiri.getLogger("tseda")


def make_individuals_table(tsm):
    result = []
    for ts_ind in tsm.ts.individuals():
        ind = Individual(individual=ts_ind)
        result.append(ind)
    return IndividualsTable(table=pd.DataFrame(result))


def make_sample_sets_table(tsm):
    result = []
    for ts_pop in tsm.ts.populations():
        ss = SampleSet(
            sample_set_id=ts_pop.id, population=ts_pop, predefined=True
        )
        result.append(ss)
    return SampleSetsTable(table=pd.DataFrame(result))


def preprocess(tsm):
    """Take a tsbrowse.TSModel and make individuals and sample sets tables."""
    logger.info(
        "Preprocessing data: making individuals and sample sets tables"
    )

    sample_sets_table = make_sample_sets_table(tsm)
    individuals_table = make_individuals_table(tsm)
    return individuals_table, sample_sets_table


class SampleSetsTable(Viewer):
    default_columns = ["name", "color", "predefined"]
    editors = {k: None for k in default_columns}
    editors["color"] = {
        "type": "list",
        "values": config.COLORS,
        "valueLookup": True,
    }

    editors = {
        "name": {"type": "input", "validator": "unique", "search": True},
        "color": {
            "type": "list",
            "values": [
                {
                    "value": color,
                    "label": (
                        f'<div style="background-color:{color}; '
                        f'width: 100%; height: 20px;"></div>'
                    ),
                }
                for color in config.COLORS
            ],
        },
        "predefined": {"type": "tickCross"},
        "valueLookup": True,
    }

    formatters = {
        "color": {"type": "color"},
        "predefined": {"type": "tickCross"},
    }

    create_sample_set_textinput = param.String(
        doc="Enter name of new sample set. Press Enter (⏎) to create",
        default=None,
        label="Create new sample set",
    )

    create_sample_set_warning = pn.pane.Alert(
        "If the new sample set is not shown immediately, click Refresh above",
        alert_type="warning",
        visible=False,
    )

    sample_set_warning = pn.pane.Alert(
        "This sample set name already exists, pick a unique name.",
        alert_type="warning",
        visible=False,
    )

    table = param.DataFrame()

    def __init__(self, **params):
        super().__init__(**params)
        self.table.set_index(["sample_set_id"], inplace=True)
        self.data = self.param.table.rx()

    @property
    def tooltip(self):
        return pn.widgets.TooltipIcon(
            value=(
                "The name and color of each sample set are editable. In the "
                "color column, select a color from the dropdown list. In the "
                "individuals table, you can assign individuals to sample sets."
            ),
        )

    @pn.depends("create_sample_set_textinput")
    def __panel__(self):
        if self.create_sample_set_textinput is not None:
            self.create_sample_set_warning.visible = True
            previous_names = [
                self.table.name[i] for i in range(len(self.table))
            ]
            if self.create_sample_set_textinput in previous_names:
                self.sample_set_warning.visible = True
            else:
                previous_colors = [
                    self.table.color[i] for i in range(len(self.table))
                ]
                unused_colors = [
                    color
                    for color in config.COLORS
                    if color not in previous_colors
                ]
                if len(unused_colors) != 0:
                    colors = unused_colors
                else:
                    colors = config.COLORS
                self.sample_set_warning.visible = False
                i = max(self.param.table.rx.value.index) + 1
                self.param.table.rx.value.loc[i] = [
                    self.create_sample_set_textinput,
                    colors[random.randint(0, len(colors) - 1)],
                    False,
                ]
                self.create_sample_set_textinput = None
        table = pn.widgets.Tabulator(
            self.data,
            layout="fit_data_table",
            selectable=True,
            page_size=10,
            pagination="remote",
            margin=10,
            formatters=self.formatters,
            editors=self.editors,
            configuration={
                "rowHeight": 40,
            },
            height=500,
        )
        return pn.Column(
            self.tooltip,
            table,
        )

    def get_ids(self):
        if isinstance(self.table, pd.DataFrame):
            return self.table.index.values.tolist()
        else:
            raise TypeError("self.table is not a valid pandas DataFrame.")

    def sidebar_table(self):
        table = pn.widgets.Tabulator(
            self.data,
            layout="fit_data_table",
            selectable=True,
            page_size=10,
            pagination="remote",
            margin=10,
            formatters=self.formatters,
            editors=self.editors,
            hidden_columns=["id"],
        )
        return pn.Card(
            pn.Column(self.tooltip, table),
            title="Sample sets table quick view",
            collapsed=True,
            header_background=config.SIDEBAR_BACKGROUND,
            active_header_background=config.SIDEBAR_BACKGROUND,
            styles=config.VCARD_STYLE,
        )

    def sidebar(self):
        return pn.Column(
            pn.Card(
                self.param.create_sample_set_textinput,
                self.create_sample_set_warning,
                title="Sample sets table options",
                collapsed=False,
                header_background=config.SIDEBAR_BACKGROUND,
                active_header_background=config.SIDEBAR_BACKGROUND,
                styles=config.VCARD_STYLE,
            ),
            self.sample_set_warning,
        )

    @property
    def color(self):
        """Return the color of all sample sets as a dictionary"""
        d = {}
        for index, row in self.data.rx.value.iterrows():
            d[index] = row.color
        return d

    @property
    def color_by_name(self):
        """Return the color of all sample sets as a dictionary with
        sample set names as keys"""
        d = {}
        for _, row in self.data.rx.value.iterrows():
            d[row["name"]] = row.color
        return d

    @property
    def names(self):
        """Return the names of all sample sets as a dictionary"""
        d = {}
        for index, row in self.data.rx.value.iterrows():
            d[index] = row["name"]
        return d

    @property
    def names2id(self):
        """Return the sample sets as dictionary with names as keys,
        ids as values"""
        d = {}
        for index, row in self.data.rx.value.iterrows():
            d[row["name"]] = index
        return d

    def loc(self, i):
        """Return sample set by index"""
        return self.data.rx.value.loc[i]


class IndividualsTable(Viewer):
    """Class to hold and view individuals and perform calculations to
    change filters."""

    sample_sets_table = param.ClassSelector(class_=SampleSetsTable)

    columns = [
        "color",
        "population",
        "sample_set_id",
        "name_sample_set",
        "name_individual",
        "longitude",
        "latitude",
        "selected",
    ]

    editors = {k: None for k in columns}
    editors["sample_set_id"] = {
        "type": "number",
        "valueLookup": True,
    }
    editors["selected"] = {
        "type": "list",
        "values": [False, True],
        "valuesLookup": True,
    }

    formatters = {
        "selected": {"type": "tickCross"},
        "color": {"type": "color"},
    }

    table = param.DataFrame()

    page_size = param.Selector(
        objects=[10, 20, 50, 100, 200, 500],
        default=20,
        doc="Number of rows per page to display",
    )
    sample_select = pn.widgets.MultiChoice(
        name="Select sample sets",
        description="Select samples based on the sample set ID.",
        options=[],
    )
    population_from = pn.widgets.Select(
        name="Original population ID",
        value=None,
        sizing_mode="stretch_width",
        description=("Reassign individuals with this population ID."),
    )
    sample_set_to = pn.widgets.Select(
        name="New sample set ID",
        value=None,
        sizing_mode="stretch_width",
        description=("Reassign individuals to this sample set ID."),
    )
    mod_update_button = pn.widgets.Button(
        name="Reassign", button_type="success", margin=(10, 10)
    )
    refresh_button = pn.widgets.Button(
        name="Refresh", button_type="success", margin=(10, 0)
    )
    restore_button = pn.widgets.Button(
        name="Restore", button_type="danger", margin=(10, 10)
    )

    data_mod_warning = pn.pane.Alert(
        """Please enter a valid population ID and
        a non-negative new sample set ID""",
        alert_type="warning",
        visible=False,
    )

    filters = {
        "name_individual": {
            "type": "input",
            "func": "like",
            "placeholder": "Enter name",
        },
        "population": {
            "type": "input",
            "func": "like",
            "placeholder": "Enter ID",
        },
        "sample_set_id": {
            "type": "input",
            "func": "like",
            "placeholder": "Enter ID",
        },
        "selected": {
            "type": "tickCross",
            "tristate": True,
            "indeterminateValue": None,
        },
        "name_sample_set": {
            "type": "input",
            "func": "like",
            "placeholder": "Enter name",
        },
    }

    def __init__(self, **params):
        super().__init__(**params)
        self.table.set_index(["id"], inplace=True)
        self.data = self.param.table.rx()
        all_sample_set_ids = self.get_sample_set_ids()
        self.sample_select.options = all_sample_set_ids
        self.sample_select.value = all_sample_set_ids

    @property
    def tooltip(self):
        return pn.widgets.TooltipIcon(
            value=(
                "Individuals table with columns relevant for modifying plots. "
                "The `population_id` column is immutable and displays the  "
                "population id of the individual, as assigned during "
                "inference. The `sample_set_id` column is editable and can "
                "be assigned to a sample set id from the sample set table "
                "through a drop-down list by clicking on a cell. "
                "The `selected` column indicates whether an individual is  "
                "included in the analyses or not, and can be toggled to  "
                "exclude/include individuals of choice. Individuals lacking "
                "geolocation coordinates (`longitude`/`latitude`) are not  "
                "displayed in the GeoMap plots."
            ),
        )

    def sample_sets(self, only_selected=True):
        """Returns a dictionary with a sample
        set id to samples list mapping."""
        sample_sets = {}
        inds = self.data.rx.value
        for _, ind in inds.iterrows():
            if not ind.selected and only_selected:
                continue
            sample_set = ind.sample_set_id
            if sample_set not in sample_sets:
                sample_sets[sample_set] = []
            sample_sets[sample_set].extend(ind.nodes)
        return sample_sets

    def get_population_ids(self):
        """Return indices of populations."""
        return sorted(self.data.rx.value["population"].unique().tolist())

    def get_sample_set_ids(self):
        """Return indices of sample groups."""
        individuals_sets = sorted(self.data.rx.value["sample_set_id"].tolist())
        if self.sample_sets_table is not None:  # Nonetype when not yet defined
            individuals_sets = (
                individuals_sets + self.sample_sets_table.get_ids()
            )
        return sorted(list(set(individuals_sets)))

    @property
    def sample2ind(self):
        """Map sample (tskit node) ids to individual ids"""
        inds = self.data.rx.value
        d = {}
        for index, ind in inds.iterrows():
            for node in ind.nodes:
                d[node] = index
        return d

    def samples(self):
        """Return all samples"""
        for _, ind in self.data.rx.value.iterrows():
            for node in ind.nodes:
                yield node

    def loc(self, i):
        """Return individual by index"""
        return self.data.rx.value.loc[i]

    def check_data_modification(self):
        if (
            isinstance(self.mod_update_button.value, bool)
            and not self.mod_update_button.value
        ):
            return False
        if (
            self.sample_set_to.value is not None
            and self.population_from.value is not None
        ):
            population_ids = self.get_population_ids()
            if self.population_from.value not in population_ids:
                self.data_mod_warning.visible = True
                return False
            elif int(self.sample_set_to.value) < 0:
                self.data_mod_warning.visible = True
                return False
            else:
                self.data_mod_warning.visible = False
                return True
        else:
            self.data_mod_warning.visible = False
            return False

    def reset_modification(self):
        self.data.rx.value.sample_set_id = self.data.rx.value.population

    def combine_tables(self, individuals_table):
        """Combine individuals and sample sets table."""

        combined_df = pd.merge(
            individuals_table.rx.value,
            self.sample_sets_table.data.rx.value,
            left_on="sample_set_id",
            right_index=True,
            suffixes=("_individual", "_sample_set"),
        )

        combined_df["id"] = combined_df.index
        combined_df = combined_df[self.columns]

        formatters = self.formatters
        filters = self.filters
        page_size = self.page_size

        combined_table = pn.widgets.Tabulator(
            combined_df,
            pagination="remote",
            layout="fit_columns",
            selectable=True,
            page_size=page_size,
            formatters=formatters,
            editors=self.editors,
            sorters=[
                {"field": "id", "dir": "asc"},
                {"field": "selected", "dir": "des"},
            ],
            margin=10,
            text_align={col: "right" for col in self.columns},
            header_filters=filters,
        )
        return combined_table

    @pn.depends(
        "page_size",
        "sample_select.value",
        "mod_update_button.value",
        "refresh_button.value",
        "restore_button.value",
    )
    def __panel__(self):
        self.population_from.options = self.get_population_ids()
        all_sample_set_ids = self.get_sample_set_ids()
        self.sample_set_to.options = all_sample_set_ids
        self.sample_select.options = all_sample_set_ids

        if isinstance(self.sample_select.value, list):
            self.data.rx.value["selected"] = False
            for sample_set_id in self.sample_select.value:
                self.data.rx.value.loc[
                    self.data.rx.value.sample_set_id == sample_set_id,
                    "selected",
                ] = True
        if self.check_data_modification():
            self.table.loc[
                self.table["population"] == self.population_from.value,  # pyright: ignore[reportIndexIssue]
                "sample_set_id",
            ] = self.sample_set_to.value

        if (
            isinstance(self.restore_button.value, bool)
            and self.restore_button.value
        ):
            self.reset_modification()

        data = self.data

        table = self.combine_tables(data)

        return pn.Column(pn.Row(self.tooltip, align=("start", "end")), table)

    def options_sidebar(self):
        return pn.Card(
            self.param.page_size,
            self.sample_select,
            collapsed=False,
            title="Individuals table options",
            header_background=config.SIDEBAR_BACKGROUND,
            active_header_background=config.SIDEBAR_BACKGROUND,
            styles=config.VCARD_STYLE,
        )

    modification_header = pn.pane.HTML(
        "<h4 style='margin: 0;'>Batch reassign individuals</h4>"
    )

    def modification_sidebar(self):
        return pn.Column(
            pn.Card(
                self.modification_header,
                pn.Row(self.population_from, self.sample_set_to),
                pn.Row(
                    pn.Spacer(width=120),
                    self.restore_button,
                    self.mod_update_button,
                    align="end",
                ),
                collapsed=False,
                title="Data modification",
                header_background=config.SIDEBAR_BACKGROUND,
                active_header_background=config.SIDEBAR_BACKGROUND,
                styles=config.VCARD_STYLE,
            ),
            self.data_mod_warning,
        )


class DataStore(Viewer):
    tsm = param.ClassSelector(class_=model.TSModel)
    sample_sets_table = param.ClassSelector(class_=SampleSetsTable)
    individuals_table = param.ClassSelector(class_=IndividualsTable)

    views = param.List(constant=True)

    @property
    def color(self):
        """Return colors of selected individuals"""
        color = pd.merge(
            self.individuals_table.data.rx.value,
            self.sample_sets_table.data.rx.value,
            left_on="sample_set_id",
            right_index=True,
        )
        return color.loc[color.selected].color

    def haplotype_gnn(self, focal_ind, windows=None):
        sample_sets = self.individuals_table.sample_sets()
        ind = self.individuals_table.loc(focal_ind)
        hap = windowed_genealogical_nearest_neighbours(
            self.tsm.ts, ind.nodes, sample_sets, windows=windows
        )
        dflist = []
        sample_set_names = [
            self.sample_sets_table.loc(i)["name"] for i in sample_sets
        ]
        if windows is None:
            for i in range(hap.shape[0]):
                x = pd.DataFrame(hap[i, :])
                x = x.T
                x.columns = sample_set_names
                x["haplotype"] = i
                x["start"] = 0
                x["end"] = self.tsm.ts.sequence_length
                dflist.append(x)
        else:
            for i in range(hap.shape[1]):
                x = pd.DataFrame(hap[:, i, :])
                x.columns = sample_set_names
                x["haplotype"] = i
                x["start"] = windows[0:-1]
                x["end"] = windows[1:]
                dflist.append(x)
        df = pd.concat(dflist)
        df.set_index(["haplotype", "start", "end"], inplace=True)
        return df

    # Not needed? Never used?
    def __panel__(self):
        return pn.Row(
            self.individuals_table,
            self.sample_sets_table,
        )
