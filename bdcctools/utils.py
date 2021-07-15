"""
General helper functions.
"""
import pandas as pd


def fuzzy_match(observed: pd.Series, expected: pd.Series) -> pd.Series:
    """


    Parameters
    ----------
    observed
    expected

    Returns
    -------

    """
    pass


def verify(
    df: pd.DataFrame,
    observed_col: str,
    expected: pd.Series,
    flag_name: str,
    add_suggested: bool = False,
    suggested_name: str = None,
    drop: bool = False
) -> pd.DataFrame:
    """
    Verifies that the values in a specific column from `df` match some
    expected values.

    Parameters
    ----------
    df:             pandas DataFrame.
    observed_col:   Name of the column in `df` with the values to verify.
    expected:       pandas Series with expected values. Has to match `df`
                    length.
    flag_name:      Name of the resulting column indicating whether the
                    observed values match the expected values.
    add_suggested:  Whether to add a column to the result with suggested
                    values for those rows where the observed values do not
                    match the expected values.
    suggested_name: Name of the column for the suggested values. Only has
                    effect when add_suggested=True is passed.
    drop:           Whether to drop the rows where the observed values
                    do not match the expected values.

    Returns
    -------
    Copy of `df` with extra columns.
    """
    df = df.copy()

    df[flag_name] = df[observed_col] == expected
    if add_suggested:
        df.loc[~df[flag_name], suggested_name] = expected.loc[~df[flag_name]]

    if drop:
        df = df[~df[flag_name]]

    return df
