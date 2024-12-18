import numpy as np
import pandas as pd

# from fink_utils.photometry.conversion import dc_mag, is_source_behind
from fink_utils.photometry.utils import apparent_flux
# from fink_utils.spark.utils import concat_col
# from pyspark.sql.functions import pandas_udf
# from pyspark.sql.types import ArrayType, DoubleType, BooleanType, StringType, MapType

# RELEASE = 22
# CTAO_PATH = 'CTAO_blazars_ztfdr{}.parquet'.format(RELEASE)

def standardized_flux_(pdf: pd.DataFrame, CTAO_blazar: pd.DataFrame) -> tuple:
    """Returns the standardized flux (flux over median of each band) and its uncertainties for a batch of alerts

    Parameters
    ----------
    pdf: pd.core.frame.DataFrame
        Pandas DataFrame of the alert history containing: 
        candid, ojbectId, cdistnr, cmagpsf, csigmapsf, cmagnr, csigmagnr, cisdiffpos, cfid, cjd
    CTAO_blazar: pd.core.frame.DataFrame
        Pandas DataFrame of the monitored sources containing: 
        3FGL Name, ZTF Name, Arrays of Medians, Computed Threshold, Observed Threshold, Redshift, Final Threshold

    Returns
    -------
    Tuple of pandas.Series
        Standardized flux and its uncertainties
    """

    std_flux = np.full(len(pdf), np.nan)
    sigma_std_flux = np.full(len(pdf), np.nan)

    name = pdf['objectId'].values[0]
    CTAO_data = CTAO_blazar.loc[CTAO_blazar['ZTF Name'] == name]
    if not CTAO_data.empty:

        flux_dc, sigma_flux_dc = 1000 * np.transpose(
            [
                apparent_flux(*args) for args in zip(
                    pdf['cmagpsf'].astype(float).values,
                    pdf['csigmapsf'].astype(float).values,
                    pdf['cmagnr'].astype(float).values,
                    pdf['csigmagnr'].astype(float).values,
                    pdf['cisdiffpos'].values
                )
            ]
        )
        
        for filter in pdf['cfid'].unique():
            maskFilt = pdf['cfid'] == filter
            median = precomputed_data['Array of Medians'].values[0][filter - 1]
            std_flux[maskFilt] = flux_dc[maskFilt] / median
            sigma_std_flux[maskFilt] = sigma_flux_dc[maskFilt] / median
    
    return pd.Series(std_flux), pd.Series(sigma_std_flux)