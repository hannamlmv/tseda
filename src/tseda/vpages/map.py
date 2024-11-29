"""Module for creating a map of the world with sample locations

Generate a hvplot map of the world with sample locations based on a
GeoPandas representation of the individuals data. The map is
interactive and can be drawn using different XYZ tiles.

TODO:

- Add linked brushing between the map and other panel objects /
  widgets
- Fix issue where map is rendered small and repeated tiles

"""

import geopandas
import hvplot.pandas  # noqa
import pandas as pd
import panel as pn
import param
import xyzservices.providers as xyz

from tseda import config

from .core import View

tiles_options = {
    "WorldImagery": xyz.Esri.WorldImagery,
    "WorldTopoMap": xyz.Esri.WorldTopoMap,
    "WorldStreetMap": xyz.Esri.WorldStreetMap,
    "WorldTerrain": xyz.Esri.WorldTerrain,
    "WorldShadedRelief": xyz.Esri.WorldShadedRelief,
    "WorldPhysical": xyz.Esri.WorldPhysical,
    "WorldGrayCanvas": xyz.Esri.WorldGrayCanvas,
}


class GeoMap(View):
    tiles_selector = param.Selector(
        default="WorldPhysical",
        objects=list(tiles_options.keys()),
        doc="Select XYZ tiles for map",
    )
    tiles = tiles_options[tiles_selector.default]

    def __panel__(self):
        self.tiles = tiles_options[self.tiles_selector]
        df = self.datastore.individuals_table.data.rx.value
        df = df.loc[df.selected]
        color = self.datastore.color
        gdf = geopandas.GeoDataFrame(
            df.drop(["longitude", "latitude"], axis=1),
            geometry=geopandas.points_from_xy(df.longitude, df.latitude),
        )
        color = color.loc[~gdf.geometry.is_empty.values]
        gdf = gdf[~gdf.geometry.is_empty]

        kw = {
            "geo": True,
            "tiles": self.tiles,
            "tiles_opts": {"alpha": 0.5},
            "responsive": True,
            "max_height": 200,
            "min_height": 199,
            "xlim": (-180, 180),
            "ylim": (-60, 70),
            "tools": ["wheel_zoom", "box_select", "tap", "pan", "reset"],
        }

        if gdf.empty:
            gdf = geopandas.GeoDataFrame(
                pd.DataFrame(index=[0]),
                geometry=geopandas.points_from_xy([0.0], [0.0]),
            )
            return gdf.hvplot(
                **kw,
                hover_cols=None,
                size=100,
                color=None,
                fill_alpha=0.0,
                line_color=None,
            )
        return gdf.hvplot(
            **kw,
            hover_cols=["name", "population", "sample_set_id"],
            size=100,
            color=color,
            fill_alpha=0.5,
            line_color="black",
        )

    def sidebar(self):
        return pn.Card(
            self.param.tiles_selector,
            collapsed=False,
            title="Map options",
            header_background=config.SIDEBAR_BACKGROUND,
            active_header_background=config.SIDEBAR_BACKGROUND,
            styles=config.VCARD_STYLE,
        )
