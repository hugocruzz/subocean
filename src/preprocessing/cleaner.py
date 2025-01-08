import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple

class DataCleaner:
    # Default validation ranges
    DEFAULT_VALIDATION_RANGES = {
        'Cavity Pressure (mbar)': (29.5, 30.5),
        'Cellule Temperature (Degree Celsius)': (39.5, 40.5),
        'Depth (meter)': (-2, 11000)
    }
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.cleaning_log = []
        
    def apply_moving_average(self, column: str, window: int = 5) -> pd.DataFrame:
        """Apply moving average to specific column"""
        self.df[f"{column}_ma"] = self.df[column].rolling(
            window=window, center=True).mean()
        self.cleaning_log.append(f"Applied {window}-point moving average to {column}")
        return self.df
    
    def clean_h2o_measurements(self, window: int = 5) -> pd.DataFrame:
        """Clean H2O measurements with moving average"""
        return self.apply_moving_average('[H2O] measured (%)', window)
    
    def validate_measurements(self, 
                            validation_ranges: Optional[Dict[str, Tuple[float, float]]] = None
                            ) -> pd.DataFrame:
        """
        Validate key measurements using provided or default ranges
        
        Parameters
        ----------
        validation_ranges : Dict[str, Tuple[float, float]], optional
            Dictionary of column names and their (min, max) validation ranges.
            If None, uses DEFAULT_VALIDATION_RANGES.
        """
        conditions = validation_ranges or self.DEFAULT_VALIDATION_RANGES
        
        for column, (min_val, max_val) in conditions.items():
            if column in self.df.columns:  # Only validate if column exists
                mask = (self.df[column] >= min_val) & (self.df[column] <= max_val)
                self.df.loc[~mask, column] = np.nan
                self.cleaning_log.append(
                    f"Filtered {column} between {min_val} and {max_val}")
        
        return self.df