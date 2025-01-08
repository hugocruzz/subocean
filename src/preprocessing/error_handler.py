import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging
class ErrorHandler:
    def __init__(self, method: str = 'iqr', zscore_threshold: float = 3.0, iqr_threshold: float = 1.5):
        """
        Initialize error handler with method-specific thresholds
        
        Parameters
        ----------
        method : str
            'zscore' (sigma rule) or 'iqr' (Tukey's method)
        zscore_threshold : float
            Number of standard deviations for z-score method
        iqr_threshold : float
            Multiplier for IQR in Tukey's method
        """
        self.method = method
        self.thresholds = {
            'zscore': zscore_threshold,
            'iqr': iqr_threshold
        }
        self.logger = logging.getLogger(__name__)
        
    def process_error_standard(self, df: pd.DataFrame, column: str = 'Error Standard') -> pd.DataFrame:
        """Process Error Standard values using chosen outlier detection method"""
        df = df.copy()
        data = df[column]
        
        if self.method == 'zscore':
            mean = data.mean()
            std = data.std()
            mask = (data - mean).abs() <= self.thresholds['zscore'] * std
            
        elif self.method == 'iqr':
            q1 = data.quantile(0.25)
            q3 = data.quantile(0.75)
            iqr = q3 - q1
            mask = (data >= q1 - self.thresholds['iqr'] * iqr) & (data <= q3 + self.thresholds['iqr'] * iqr)
        
        df.loc[~mask, column] = np.nan
        self.logger.info(f"Removed {(~mask).sum()} {column} outliers using {self.method} method")
        
        return df
    def get_quality_metrics(self, df: pd.DataFrame, column: str = 'Error Standard') -> Dict[str, Optional[float]]:
        """Calculate quality metrics for the specified column in the DataFrame"""
        data = df[column].dropna()
        metrics = {
            'mean': data.mean(),
            'std': data.std(),
            'min': data.min(),
            'max': data.max(),
            '25%': data.quantile(0.25),
            '50%': data.median(),
            '75%': data.quantile(0.75),
            'count': data.count()
        }
        self.logger.info(f"Calculated quality metrics for {column}")
        return metrics