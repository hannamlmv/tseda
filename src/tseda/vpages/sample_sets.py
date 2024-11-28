"""Sample sets editor page.

Panel showing a simple sample set editor page. The page consists of
an editable table showing the sample sets.

The sample sets table allows the user to edit the name and color of
each sample set. In addition, new sample sets can be added that allows
the user to reassign individuals to different sample sets in the
individuals table.

TODO:

- change from/to params to param.NumericTuple?
"""

import panel as pn
import param

from tseda.datastore import SampleSetsTable

from .core import View


class SampleSetsPage(View):
    key = "sample_sets"
    title = "Sample Sets"
    data = param.ClassSelector(class_=SampleSetsTable)

    def __init__(self, **params):
        super().__init__(**params)
        self.data = self.datastore.sample_sets_table

    def __panel__(self):
        return pn.Column(self.data)

    def sidebar(self):
        return pn.Column(
            pn.pane.HTML(
                "<h2 style='margin: 0;'>Sample Sets</h2>",
                sizing_mode="stretch_width",
            ),
            pn.pane.Markdown(
                (
                    "This section allows you to manage and "
                    "customize Sample Sets.<br><br>"
                    "Use the controls below to add new samples."
                ),
                sizing_mode="stretch_width",
            ),
            self.data.sidebar,
        )
