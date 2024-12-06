from . import (
    ignn,
    individuals,
    overview,
    stats,
    structure,
    trees,
)

PAGES = [
    overview.OverviewPage,
    individuals.IndividualsPage,
    structure.StructurePage,
    ignn.IGNNPage,
    stats.StatsPage,
    trees.TreesPage,
]

PAGES_MAP = {page.key: page for page in PAGES}
PAGES_BY_TITLE = {page.title: page for page in PAGES}
