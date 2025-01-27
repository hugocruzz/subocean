import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Tuple


class DepthGridder_xr:
    """Grid data to regular depth intervals using xarray"""
    
    def __init__(self, df: pd.DataFrame, profile_name: str = None):
        self.df = df
        self.depth_column = 'Depth__meter_'
        self.profile_name = profile_name if profile_name else 'profile'
        
    def interpolate_to_grid(self, depth_interval: float = 0.05) -> xr.Dataset:
        """Interpolate data to regular depth grid"""
        # Ensure depth column exists
        if self.depth_column not in self.df.columns:
            raise ValueError(f"Depth column '{self.depth_column}' not found")
            
        # Get numeric columns excluding depth
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        numeric_cols = numeric_cols.drop(self.depth_column)
        
        # Average numeric data at same depths
        df_numeric = self.df[numeric_cols]
        df_averaged = df_numeric.groupby(self.df[self.depth_column]).mean()
        
        # Create regular depth grid
        depth_min = np.floor(self.df[self.depth_column].min())
        depth_max = np.ceil(self.df[self.depth_column].max())
        depth_grid = np.arange(depth_min, depth_max + depth_interval, depth_interval)
        
        # Create and interpolate dataset
        ds = xr.Dataset.from_dataframe(df_averaged)
        ds_interp = ds.interp({self.depth_column: depth_grid}, method='linear')
        
        # Add metadata
        ds_interp.attrs['profile_name'] = self.profile_name
        ds_interp.attrs['depth_interval'] = depth_interval
        
        return ds_interp