import os

import geopandas as gpd
import pandas as pd
import pytest

from recovery.geo import check_match

DATA_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), "data")


@pytest.fixture
def other():
    return gpd.read_file(os.path.join(DATA_FOLDER, "admin0.gpkg"), layer="admin0_2018")


@pytest.fixture
def result(records, other):
    return check_match(
        records, other, "country", "ISO_A2", "correctCountry", "suggestedCountry"
    )


def test_flag(result, expected):
    pd.testing.assert_series_equal(result["correctCountry"], expected["correctCountry"])


def test_suggestions(result, expected):
    pd.testing.assert_series_equal(
        result["suggestedCountry"], expected["suggestedCountry"]
    )