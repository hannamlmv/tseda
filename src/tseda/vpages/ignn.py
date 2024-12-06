"""Genealogical Nearest Neighbors (GNN) analysis.

Draw GNN plots for individuals and haplotypes. The GNN plot shows the
GNN proportions in each sample set for each individual or haplotype.
The GNN proportions are calculated using the genealogical nearest
neighbors method.

Individuals are grouped and colored by sample set. The groupings and
colors can be modified in the sample set editor. Hovering over the bars
in the plot shows the GNN proportions of each sample set for a given
sample.

TODO:

- linked brushing between the map and the GNN plot
"""

import holoviews as hv
import hvplot.pandas  # noqa
import pandas as pd
import panel as pn
import param
from bokeh.models import (
    ColumnDataSource,
    FactorRange,
    HoverTool,
)
from bokeh.plotting import figure

from tseda import config

from .core import View, make_windows
from .map import GeoMap

hv.extension("bokeh")
pn.extension(sizing_mode="stretch_both")


class GNNHaplotype(View):
    """Make GNN haplotype plot."""

    individual_id = param.Integer(
        default=None,
        doc="Individual ID (0-indexed)",
    )

    window_size = param.Integer(
        default=10000, bounds=(1, None), doc="Size of window"
    )

    warning_pane = pn.pane.Alert(
        """Please select at least 1 sample to visualize these graphs. 
        Sample selection is done on the Individuals page.""",
        alert_type="warning",
        visible=False,
    )

    individual_id_warning = pn.pane.Alert(
        "",
        alert_type="warning",
        visible=False,
    )

    def plot(self, haplotype=0):
        if self.individual_id is None:
            return pn.pane.Markdown("Enter a sample ID")
        if self.window_size is not None:
            windows = make_windows(
                self.window_size, self.datastore.tsm.ts.sequence_length
            )
        else:
            windows = None
        data = self.datastore.haplotype_gnn(
            self.individual_id, windows=windows
        )
        df = data.loc[data.index.get_level_values("haplotype") == haplotype]
        df = df.droplevel(["haplotype", "end"])
        if list(df.columns) == []:
            self.warning_pane.visible = True
            return pn.pane.Markdown("")
        else:
            self.warning_pane.visible = False
        populations = [str(x) for x in df.columns]
        colormap = [
            self.datastore.sample_sets_table.color_by_name[x]
            for x in df.columns
        ]
        df.reset_index(inplace=True)
        # TODO: hvplot ignores tools/default_tools parameter
        p = df.hvplot.area(
            x="start",
            y=populations,
            color=colormap,
            legend="right",
            sizing_mode="stretch_width",
            fill_alpha=0.5,
            min_height=300,
            responsive=True,
            tools=[
                "pan",
                "xpan",
                "xwheel_zoom",
                "box_select",
                "save",
                "reset",
            ],
        )
        p.opts(
            default_tools=[
                "pan",
                "xpan",
                "xwheel_zoom",
                "box_select",
                "save",
                "reset",
            ],
            active_tools=[
                "pan",
                "xpan",
                "xwheel_zoom",
                "box_select",
                "save",
                "reset",
            ],
            tools=["xpan", "xwheel_zoom", "box_select", "save", "reset"],
            ylabel="Proportion",
        )
        return p

    def plot_haplotype0(self):
        return self.plot(0)

    def plot_haplotype1(self):
        return self.plot(1)

    def check_inputs(self, inds):
        max_id = inds.index.max()
        info_column = pn.Column(
            pn.pane.HTML(
                "<h2 style='margin: 0;'>GNN Haplotype plot</h2>",
                sizing_mode="stretch_width",
            ),
            pn.pane.Markdown(
                "**Enter a valid sample id to see the GNN haplotype plot.**"
            ),
        )
        if self.individual_id is None:
            self.individual_id_warning.visible = False  # No warning for None
            return None, info_column

        try:
            if (
                not isinstance(self.individual_id, (int, float))
                or self.individual_id < 0
            ):
                self.individual_id_warning.object = (
                    "The individual ID does not exist. "
                    f"Valid IDs are in the range 0-{max_id}."
                )
                self.individual_id_warning.visible = True
                return (None, info_column)
            else:
                self.individual_id_warning.visible = False
                nodes = inds.loc[self.individual_id].nodes
                info_column = pn.Column(pn.pane.Markdown(""))
                return (nodes, info_column)
        except KeyError:
            self.individual_id_warning.object = (
                "The individual ID does not exist. "
                f"Valid IDs are in the range 0-{max_id}."
            )
            self.individual_id_warning.visible = True
            return (None, info_column)

    @pn.depends("individual_id", "window_size")
    def __panel__(self, **params):
        inds = self.datastore.individuals_table.data.rx.value
        nodes = self.check_inputs(inds)
        if nodes[0] is not None:
            return pn.Column(
                pn.pane.HTML(
                    "<h2 style='margin: 0;'>GNN Haplotype plot "
                    f"- Individual id {self.individual_id}</h2>",
                    sizing_mode="stretch_width",
                ),
                self.warning_pane,
                pn.pane.Markdown(f"### Haplotype 0 (sample id {nodes[0][0]})"),
                self.plot_haplotype0,
                pn.pane.Markdown(f"### Haplotype 1 (sample id {nodes[0][1]})"),
                self.plot_haplotype0,
            )
        else:
            return nodes[1]

    def sidebar(self):
        return pn.Card(
            self.param.individual_id,
            self.param.window_size,
            self.individual_id_warning,
            collapsed=False,
            title="GNN haplotype options",
            header_background=config.SIDEBAR_BACKGROUND,
            active_header_background=config.SIDEBAR_BACKGROUND,
            styles=config.VCARD_STYLE,
        )


class VBar(View):
    """Make VBar plot of GNN output."""

    sorting = param.Selector(
        doc="Select what population to base the sort order on. Default is "
        "to sort by sample index",
        allow_None=True,
        default=None,
        label="Sort by",
    )

    sort_order = param.Selector(
        doc="Select the sorting order.",
        objects=["Ascending", "Descending"],
        default="Ascending",
    )

    warning_pane = pn.pane.Alert(
        """Please select at least 1 sample to visualize this graph. 
        Sample selection is done on the Individuals page.""",
        alert_type="warning",
    )

    # TODO: move to DataStore class?
    def gnn(self):
        inds = self.datastore.individuals_table.data.rx.value
        sample_sets = self.datastore.individuals_table.sample_sets()
        samples = [
            sample for sublist in sample_sets.values() for sample in sublist
        ]
        self.param.sorting.objects = [""] + list(
            self.datastore.sample_sets_table.names.values()
        )
        gnn = self.datastore.tsm.ts.genealogical_nearest_neighbours(
            samples, sample_sets=list(sample_sets.values())
        )
        df = pd.DataFrame(
            gnn,
            columns=[i for i in sample_sets],
        )
        samples2ind = [
            self.datastore.individuals_table.sample2ind[i] for i in samples
        ]
        df["id"] = samples2ind
        df["sample_id"] = df.index
        df["sample_set_id"] = [inds.loc[i].sample_set_id for i in samples2ind]
        df.set_index(["sample_set_id", "sample_id", "id"], inplace=True)
        return df

    @pn.depends("sorting", "sort_order")
    def __panel__(self):
        sample_sets = self.datastore.individuals_table.sample_sets()
        if len(list(sample_sets.keys())) < 1:
            return self.warning_pane
        df = self.gnn()
        sample_sets = self.datastore.sample_sets_table.data.rx.value
        inds = self.datastore.individuals_table.data.rx.value
        color = [sample_sets.color[i] for i in df.columns]
        groups = [sample_sets.name[i] for i in df.columns]
        levels = df.index.names
        factors = list(
            tuple([self.datastore.sample_sets_table.names[x[0]], str(x[1])])
            for x in df.index
        )
        df.columns = groups
        df.reset_index(inplace=True)
        df["x"] = factors
        samples2ind = self.datastore.individuals_table.sample2ind
        df["name"] = [inds.loc[samples2ind[x]].name for x in df.index]

        hover = HoverTool()
        hover.tooltips = list([("name", "@name")])
        hover.tooltips.extend(list(map(lambda x: (x, f"@{x}"), levels)))
        hover.tooltips.extend(
            list(
                map(
                    lambda x: (x, f"@{x}{{%0.1f}}"),
                    groups,
                )
            )
        )

        if self.sorting is not None and self.sorting != "":
            sort_by = (
                ["sample_set_id"] + [self.sorting] + ["sample_id", "id"]  # pyright: ignore[reportOperatorIssue]
            )
            ascending = [True, False, False, False]

            columns = df.columns.tolist()
            columns.remove(self.sorting)
            id_index = columns.index("id")
            columns.insert(id_index + 1, self.sorting)
            df = df[columns]
            sorting_index = groups.index(self.sorting)
            groups[sorting_index], groups[0] = groups[0], groups[sorting_index]
            color[sorting_index], color[0] = color[0], color[sorting_index]
        else:
            sort_by = ["sample_set_id", "sample_id", "id"]
            ascending = [True, False, False]
        if self.sort_order == "Ascending":
            df.sort_values(sort_by, axis=0, inplace=True)
        else:
            df.sort_values(
                sort_by,
                ascending=ascending,
                axis=0,
                inplace=True,
            )
        factors = df["x"].values
        source = ColumnDataSource(df)
        fig = figure(
            x_range=FactorRange(
                *factors, group_padding=0.1, subgroup_padding=0
            ),
            height=400,
            sizing_mode="stretch_width",
            tools="xpan,xwheel_zoom,box_select,save,reset",
            y_axis_label="Proportion",
        )
        fig.add_tools(hover)
        fig.vbar_stack(
            groups,
            source=source,
            x="x",
            color=color,
            legend_label=groups,
            width=1,
            line_color="black",
            line_alpha=0.7,
            line_width=0.5,
            fill_alpha=0.5,
        )

        fig.add_layout(fig.legend[0], "right")
        fig.legend[0].label_text_font_size = "12pt"

        fig.axis.major_tick_line_color = None
        fig.axis.minor_tick_line_color = None
        fig.xaxis.group_label_orientation = 1.0
        fig.xaxis.subgroup_label_orientation = 1.0
        fig.xaxis.group_text_font_size = "14pt"
        fig.xaxis.major_label_orientation = 1.0
        fig.xaxis.major_label_text_font_size = "0pt"
        fig.yaxis.major_label_text_font_size = "12pt"
        fig.yaxis.axis_label_text_font_size = "14pt"
        fig.axis.axis_line_color = None
        fig.grid.grid_line_color = None
        fig.outline_line_color = "black"
        fig.xaxis.separator_line_width = 2.0
        fig.xaxis.separator_line_color = "grey"
        fig.xaxis.separator_line_alpha = 0.5

        return pn.panel(fig)

    def sidebar(self):
        return pn.Card(
            self.param.sorting,
            self.param.sort_order,
            collapsed=False,
            title="GNN VBar options",
            header_background=config.SIDEBAR_BACKGROUND,
            active_header_background=config.SIDEBAR_BACKGROUND,
            styles=config.VCARD_STYLE,
        )


class IGNNPage(View):
    key = "iGNN"
    title = "iGNN"
    geomap = param.ClassSelector(class_=GeoMap)
    vbar = param.ClassSelector(class_=VBar)
    gnnhaplotype = param.ClassSelector(class_=GNNHaplotype)

    def __init__(self, **params):
        super().__init__(**params)
        self.geomap = GeoMap(datastore=self.datastore)
        self.vbar = VBar(datastore=self.datastore)
        self.gnnhaplotype = GNNHaplotype(datastore=self.datastore)
        self.sample_sets = self.datastore.sample_sets_table

    def __panel__(self):
        return pn.Column(
            pn.pane.HTML(
                "<h2 style='margin: 0;'>Geomap</h2>",
                sizing_mode="stretch_width",
            ),
            pn.Row(
                self.geomap,
            ),
            pn.pane.Markdown(
                "**Map** - Displays the geographical locations where samples "
                "were collected and visually represents their group sample "
                "affiliations through colors.",
                sizing_mode="stretch_width",
            ),
            pn.pane.HTML(
                "<h2 style='margin: 0;'>vBar plot</h2>",
                sizing_mode="stretch_width",
            ),
            self.vbar,
            pn.pane.Markdown(
                "**vBar** - Lorem ipsum",
                sizing_mode="stretch_width",
            ),
            self.gnnhaplotype,
        )

    def sidebar(self):
        return pn.Column(
            pn.pane.HTML(
                "<h2 style='margin: 0;'>iGNN</h2>", sizing_mode="stretch_width"
            ),
            pn.pane.Markdown(
                (
                    "This section provides interactive visualizations for "
                    "**Genealogical Nearest Neighbors "
                    "(GNN)** analysis.<br><br>"
                    "Use the controls below to customize the plots and "
                    "adjust parameters."
                ),
                sizing_mode="stretch_width",
            ),
            self.geomap.sidebar,
            self.vbar.sidebar,
            self.gnnhaplotype.sidebar,
            self.sample_sets.sidebar_table,
        )
