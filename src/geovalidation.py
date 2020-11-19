import os
from typing import Union

import fiona
import geopandas as gpd
import numpy as np
import pandas as pd
from rasterstats import point_query

from _utils import _get_most_recent_year, _create_id_grid


def compare_admin_boundaries(
    gdf: gpd.GeoDataFrame,
    admin_path: str,
    date_col: str,
    admin_col: str,
    match_col: str,
    flag_name: str,
    suggested_name: str,
    default_validation_year: str = "last",
    add_source: bool = False,
    source_name: str = None,
    drop: bool = False,
) -> gpd.GeoDataFrame:
    """

    Parameters
    ----------
    gdf:
    admin_path:
    date_col:
    admin_col:
    match_col:
    flag_name:
    suggested_name:
    default_validation_year:
    add_source:
    source_name
    drop:

    Returns
    -------

    """
    layers = sorted(fiona.listlayers(admin_path))
    years = list(map(int, layers))

    validation_year_col = "__validation_year"

    gdf[validation_year_col] = None
    has_date = gdf[date_col].notna()
    gdf.loc[has_date, validation_year_col] = _get_most_recent_year(
        gdf.loc[has_date, date_col], years, round_unmatched=True
    )

    if default_validation_year == "first":
        gdf.loc[~has_date, validation_year_col] = min(years)
    elif default_validation_year == "last":
        gdf.loc[~has_date, validation_year_col] = max(years)
    else:
        raise ValueError("default_validation_year must be either 'first' or 'last'")

    gdf[flag_name] = None
    gdf[suggested_name] = None
    if add_source:
        gdf[source_name] = None

    for year in gdf[validation_year_col].unique():

        admin = gpd.read_file(admin_path, layer=str(year))
        admin = admin[[match_col, "geometry"]]

        has_current_year = gdf[validation_year_col] == year
        year_gdf = gdf.loc[has_current_year]

        year_gdf = gpd.sjoin(year_gdf, admin, how="left", op="intersects")

        is_valid = year_gdf[admin_col] == year_gdf[match_col]
        year_gdf[flag_name] = is_valid
        year_gdf.loc[~is_valid, suggested_name] = year_gdf.loc[~is_valid, match_col]

        if add_source:
            basename = os.path.splitext(os.path.basename(admin_path))[0]
            year_gdf[source_name] = f"{os.path.basename(basename)}_{year}"

        year_gdf = year_gdf.drop([match_col], axis=1)

        gdf.loc[has_current_year] = year_gdf

    gdf = gdf.drop([validation_year_col], axis=1)

    if drop:
        is_valid = gdf[admin_col] == gdf[match_col]
        gdf = gdf[is_valid]

    return gdf


def find_spatial_duplicates(
    gdf: gpd.GeoDataFrame,
    species_col: str,
    flag_name: str,
    resolution: float,
    bounds: Union[list, tuple] = None,
    crs: str = "epsg:4326",
    drop: bool = False,
    keep: str = "first"
):
    """

    Parameters
    ----------
    gdf
    species_col
    flag_name
    resolution
    bounds
    crs
    drop
    keep

    Returns
    -------

    """
    if not bounds:
        bounds = gdf.geometry.total_bounds

    grid = _create_id_grid(*bounds, resolution, crs)
    ids = point_query(gdf, grid.read(1), affine=grid.transform, interpolate="nearest")
    gdf["__grid_id"] = ids

    subset = [species_col, "__grid_id"]
    gdf[flag_name] = gdf.duplicated(subset, keep=False) & gdf["__grid_id"].notna()

    if drop:
        to_keep = ~gdf.duplicated(subset, keep=keep) | gdf["__grid_id"].isna()
        gdf = gdf[to_keep]

    return gdf


def read_input(
    fn: str,
    lon_col: str,
    lat_col: str,
    elev_col: str,
    drop_empty_coords=False,
    crs: str = "epsg:4326"
) -> gpd.GeoDataFrame:
    """

    Parameters
    ----------
    fn:                 Filename with extension. Can be a relative or
                        absolute path.
    lon_col:            Name of the longitude column.
    lat_col:            Name of the latitude column.
    elev_col:           Name of the elevation column.
    drop_empty_coords:  Whether to drop rows with no values in longitude
                        or latitude.
    crs:                Coordinate reference system with the
                        corresponding EPSG code. Must be in the form
                        epsg:code.

    Returns
    -------
    GeoDataFrame with the records.
    """
    dtypes = {lon_col: float, lat_col: float, elev_col: float}

    input_ext = os.path.splitext(fn)[1]
    if input_ext == ".csv":
        records = pd.read_csv(fn, dtype=dtypes)
    elif input_ext == ".xlsx":
        records = pd.read_excel(fn, dtype=dtypes)
    else:
        raise NotImplementedError("Input file extension is not supported.")

    if drop_empty_coords:
        records = records.dropna(how="any", subset=[lon_col, lat_col])

    geometry = gpd.points_from_xy(records[lon_col], records[lat_col])
    records = gpd.GeoDataFrame(records, geometry=geometry)
    records.crs = crs

    return records
