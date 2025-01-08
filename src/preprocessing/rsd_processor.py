import pandas as pd
import numpy as np
from typing import Optional, Dict

class RSDProcessor:
    """Process Relative Standard Deviation for gas measurements"""
    
    def __init__(self, df: pd.DataFrame, error_column: str = 'Error Standard'):
        self.df = df
        self.error_column = error_column
        self.rsd_results: Dict[str, pd.Series] = {}
        
    def calculate_rsd(self, column: str) -> pd.Series:
        """
        Calculate RSD for specified column
        
        Parameters
        ----------
        column : str
            Full column name (e.g. '[CH4] dissolved with water vapour (ppm)')
        """
        if column not in self.df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
        if self.error_column not in self.df.columns:
            raise ValueError(f"Error column '{self.error_column}' not found in DataFrame")
            
        rsd = (self.df[self.error_column]**2) / self.df[column]
        self.rsd_results[column] = rsd
        return rsd
    
    def rsd_filter_by_threshold(self, column: str, threshold: float) -> pd.DataFrame:
        """
        Replace values in column with NaN where RSD exceeds threshold
        
        Parameters
        ----------
        column : str
            Full column name to filter
        threshold : float
            RSD threshold value
        
        Returns
        -------
        pd.DataFrame
            DataFrame with values above threshold replaced by NaN
        """
        if column not in self.rsd_results:
            self.calculate_rsd(column)
        
        df_filtered = self.df.copy()
        mask = self.rsd_results[column] > threshold
        df_filtered.loc[mask, column] = np.nan
        
        return df_filtered