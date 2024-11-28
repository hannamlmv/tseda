import panel as pn

from .core import View


class OverviewPage(View):
    key = "overview"
    title = "Overview"

    def __panel__(self):
        return pn.Column(pn.pane.HTML(self.datastore.tsm.ts))

    def sidebar(self):
        return pn.Column(
            pn.pane.HTML(
                "<h2 style='margin: 0;'>Overview</h2>",
                sizing_mode="stretch_width",
            ),
            pn.pane.Markdown(
                (
                    "Welcome to **tseda**! This is a tool that "
                    "you can use to analyze your data bla bla "
                    "come up with something good..."
                ),
                sizing_mode="stretch_width",
            ),
        )
