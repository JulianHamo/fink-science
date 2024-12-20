from line_profiler import profile

import pandas as pd

from pyspark.sql.functions import pandas_udf
from pyspark.sql.types import ArrayType, DoubleType, StringType, MapType

from fink_science.standardized_flux.utils import standardized_flux_

from fink_science.tester import spark_unit_tests
from fink_science import __file__
import os

RELEASE = 22
CTAO_PATH = 'CTAO_blazars_ztf_dr{}.parquet'.format(RELEASE)


@pandas_udf(MapType(StringType(), ArrayType(DoubleType())))
@profile
def standardized_flux(candid: pd.Series,
                      objectId: pd.Series,
                      cdistnr: pd.Series,
                      cmagpsf: pd.Series,
                      csigmapsf: pd.Series,
                      cmagnr: pd.Series,
                      csigmagnr: pd.Series,
                      cisdiffpos: pd.Series,
                      cfid: pd.Series,
                      cjd: pd.Series) -> pd.Series:
    """Calls the standardized_flux_ function
       for the distributed Spark Pandas UDF environment

    Parameters
    ----------
    candid: pd.series
        ID of the alerts
    objectId: pd.Series
        ZTF ID of the sources
    cdistnr: pd.Series
        distance between the alert position
        and the closest source of each alert
    cmagpsf: pd.Series
        magnitude from the history of each alert
    csigmapsf: pd.Series
        magnitude error from the history of each alert
    cmagnr: pd.Series
        magnitude of the closest source from the history of each alert
    csigmagnr: pd.Series
        error on the magnitude of the closest source
        from the history of each alert
    cisdiffpos: pd.Series
        Variation sign from the history of each alert
        (+1 is positive variation, -1 else)
    cfid: pd.Series
        filter used during the exposure in the history of each alert
    cjd: pd.Series
        julian date of the historical measurements of each alert

    Return
    ------
    out: pd.Series
        Standardized flux and uncertainties in the history of each alert

    Example
    -------
    >>> import os
    >>> from fink_utils.spark.utils import concat_col
    >>> import pyspark.sql.functions as F

    >>> filename = 'CTAO_blazar_datatest_v20-12-24.parquet'
    >>> parDF_ex = spark_ex.read.parquet(ztf_alert_sample + filename)

    # Required alert columns
    >>> what = [
    ...     'distnr',
    ...     'magpsf',
    ...     'sigmapsf',
    ...     'magnr',
    ...     'sigmagnr',
    ...     'isdiffpos',
    ...     'fid',
    ...     'jd'
    >>> ]

    # Concatenation
    >>> prefix = 'c'
    >>> for key in what:
    ...     parDF_ex = concat_col(parDF_ex, colname=key, prefix=prefix)

    # Run the module
    >>> args = [
    ...     'candid',
    ...     'objectId',
    ...     'cdistnr',
    ...     'cmagpsf',
    ...     'csigmapsf',
    ...     'cmagnr',
    ...     'csigmagnr',
    ...     'cisdiffpos',
    ...     'cfid',
    ...     'cjd'
    >>> ]
    >>> parDF_ex = parDF_ex.withColumn(
    ...     'container',
    ...     standardized_flux(*args)
    >>> )
    >>> parDF_ex = parDF_ex.withColumn(
    ...     'cstd_flux',
    ...     parDF_ex['container'].getItem('flux')
    >>> )
    >>> parDF_ex = parDF_ex.withColumn(
    ...     'csigma_std_flux',
    ...     parDF_ex['container'].getItem('sigma')
    >>> )

    # Drop temporary columns
    >>> what_prefix = [prefix + key for key in what]
    >>> parDF_ex = parDF_ex.drop('container')
    >>> parDF_ex = parDF_ex.drop(*what_prefix)

    # Test
    >>> count = parDF_ex.filter(F.array_max(parDF_ex['cstd_flux']) < 1).count()
    307
    >>> count = parDF_ex.filter(F.array_max(parDF_ex['cstd_flux']) > 1).count()
    661
    """

    CTAO_blazar = pd.read_parquet(CTAO_PATH)

    pdf = pd.DataFrame(
        {
            "candid": candid,
            "objectId": objectId,
            "cdistnr": cdistnr,
            "cmagpsf": cmagpsf,
            "csigmapsf": csigmapsf,
            "cmagnr": cmagnr,
            "csigmagnr": csigmagnr,
            "cisdiffpos": cisdiffpos,
            "cfid": cfid,
            "cjd": cjd
        }
    )
    out = []
    for candid_ in pdf["candid"]:
        tmp = pdf[pdf["candid"] == candid_]
        sub = pd.DataFrame(
            {
                "candid": tmp["candid"].to_numpy()[0],
                "objectId": tmp["objectId"].to_numpy()[0],
                "cdistnr": tmp["cdistnr"].to_numpy()[0],
                "cmagpsf": tmp["cmagpsf"].to_numpy()[0],
                "csigmapsf": tmp["csigmapsf"].to_numpy()[0],
                "cmagnr": tmp["cmagnr"].to_numpy()[0],
                "csigmagnr": tmp["csigmagnr"].to_numpy()[0],
                "cisdiffpos": tmp["cisdiffpos"].to_numpy()[0],
                "cfid": tmp["cfid"].to_numpy()[0],
                "cjd": tmp["cjd"].to_numpy()[0],
            }
        )
        std_flux = standardized_flux_(sub, CTAO_blazar)
        out.append({'flux': std_flux[0], 'sigma': std_flux[1]})

    return pd.Series(out)


if __name__ == "__main__":
    """Execute the test suite"""

    globs = globals()
    path = os.path.dirname(__file__)
    ztf_alert_sample = "file://{}/data/alerts/datatest".format(path)
    globs["ztf_alert_sample"] = ztf_alert_sample

    # Run the test suite
    spark_unit_tests(globs)
