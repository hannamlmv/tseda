"""Module to plot local trees

TODO:

- fix bounds of position / treeid parameters
"""

import ast

import holoviews as hv
import panel as pn
import param

from tseda import config

from .core import View

hv.extension("bokeh")


def eval_options(options):
    """Evaluate options parameter."""
    return ast.literal_eval(options)


class Tree(View):
    search_by = pn.widgets.ToggleGroup(
        name="Search By",
        options=["Position", "Tree Index"],
        behavior="radio",
        button_type="primary",
    )

    tree_index = param.Integer(default=0, doc="Get tree by zero-based index")
    position = param.Integer(
        default=None, doc="Get tree at genome position (bp)"
    )

    position_index_warning = pn.pane.Alert(
        "The input for position or tree index is out of bounds.",
        alert_type="warning",
        visible=False,
    )

    width = param.Integer(default=750, doc="Width of the tree plot")
    height = param.Integer(default=520, doc="Height of the tree plot")
    next = param.Action(
        lambda x: x.next_tree(), doc="Next tree", label="Next tree"
    )
    prev = param.Action(
        lambda x: x.prev_tree(), doc="Previous tree", label="Previous tree"
    )

    y_axis = pn.widgets.Checkbox(name="Y-axis", value=True)
    node_labels = param.String(
        default="{}",
        doc=(
            """Show custom labels for the nodes (specified by ID).
            Any nodes not present will not have a label."""
        ),
    )

    symbol_size = param.Number(default=8, bounds=(0, None), doc="Symbol size")

    advanced_warning = pn.pane.Alert(
        "The inputs for the advanced options are not valid.",
        alert_type="warning",
        visible=False,
    )

    def next_tree(self):
        self.position = None
        self.tree_index = min(
            self.datastore.tsm.ts.num_trees - 1, int(self.tree_index) + 1
        )
        # pyright: ignore[reportOperatorIssue]

    def prev_tree(self):
        self.position = None
        self.tree_index = max(0, int(self.tree_index) - 1)
        # pyright: ignore[reportOperatorIssue]

    @property
    def default_css(self):
        """Default css styles for tree nodes"""
        styles = []
        sample_sets = self.datastore.sample_sets_table.data.rx.value
        individuals = self.datastore.individuals_table.data.rx.value
        sample2ind = self.datastore.individuals_table.sample2ind
        for n in self.datastore.individuals_table.samples():
            ssid = individuals.loc[sample2ind[n]].sample_set_id
            ss = sample_sets.loc[ssid]
            s = f".node.n{n} > .sym " + "{" + f"fill: {ss.color} " + "}"
            styles.append(s)
        css_string = " ".join(styles)
        return css_string

    @param.depends("position", "tree_index", watch=True)
    def check_inputs(self):
        if self.position is not None and (
            int(self.position) < 0
            or int(self.position) > self.datastore.tsm.ts.sequence_length
        ):
            self.position_index_warning.visible = True
            raise ValueError
        if (
            self.tree_index is not None
            and int(self.tree_index) < 0
            or int(self.tree_index) > self.datastore.tsm.ts.num_trees
        ):
            self.position_index_warning.visible = True
            raise ValueError
        else:
            self.position_index_warning.visible = False

    @param.depends(
        "width",
        "height",
        "position",
        "symbol_size",
        "tree_index",
        "y_axis.value",
        "node_labels",
    )
    def __panel__(self):
        if self.position is not None:
            tree = self.datastore.tsm.ts.at(self.position)
            self.tree_index = tree.index
        else:
            tree = self.datastore.tsm.ts.at_index(self.tree_index)
        pos1 = int(tree.get_interval()[0])
        pos2 = int(tree.get_interval()[1]) - 1
        try:
            node_labels = eval_options(self.node_labels)
            plot = tree.draw_svg(
                size=(self.width, self.height),
                symbol_size=self.symbol_size,
                y_axis=self.y_axis.value,
                node_labels=node_labels,
                style=self.default_css,
            )
            self.advanced_warning.visible = False
        except ValueError or SyntaxError or TypeError:
            plot = tree.draw_svg(
                size=(self.width, self.height),
                y_axis=True,
                node_labels={},
                style=self.default_css,
            )
            self.advanced_warning.visible = True
        return pn.Column(
            pn.pane.Markdown(
                f"## Tree index {self.tree_index} (position {pos1} - {pos2})"
            ),
            pn.pane.HTML(plot),
            pn.Row(
                self.param.prev,
                self.param.next,
            ),
        )

    def update_sidebar(self):
        """Dynamically update the sidebar based on searchBy value."""
        if self.search_by.value == "Tree Index":
            self.position = None
            fields = [self.param.tree_index]
        else:
            fields = [self.param.position]

        sidebar_content = pn.Column(
            pn.Card(
                self.search_by,
                *fields,
                self.param.width,
                self.param.height,
                collapsed=False,
                title="Tree plotting options",
                header_background=config.SIDEBAR_BACKGROUND,
                active_header_background=config.SIDEBAR_BACKGROUND,
                styles=config.VCARD_STYLE,
            ),
            self.position_index_warning,
        )
        return sidebar_content

    @param.depends("search_by.value", watch=True)
    def sidebar(self):
        return self.update_sidebar()

    def advanced_options(self):
        sidebar_content = pn.Column(
            pn.Card(
                pn.pane.HTML(
                    "<b>See the <a href='https://tskit.dev/tskit/docs/stable/python-api.html#tskit.TreeSequence.draw_svg'>tskit documentation</a> for more information about these plotting options.<b>"
                ),
                pn.pane.HTML("Include"),
                self.y_axis,
                self.param.symbol_size,
                self.param.node_labels,
                collapsed=True,
                title="Advanced plotting options",
                header_background=config.SIDEBAR_BACKGROUND,
                active_header_background=config.SIDEBAR_BACKGROUND,
                styles=config.VCARD_STYLE,
            ),
            self.advanced_warning,
        )
        return sidebar_content


class TreesPage(View):
    key = "trees"
    title = "Trees"
    data = param.ClassSelector(class_=Tree)

    def __init__(self, **params):
        super().__init__(**params)
        self.data = Tree(datastore=self.datastore)
        self.sample_sets = self.datastore.sample_sets_table

    def __panel__(self):
        return pn.Column(
            self.data,
        )

    def sidebar(self):
        return pn.Column(
            self.data.sidebar,
            self.data.advanced_options,
            self.sample_sets.sidebar_table,
        )
