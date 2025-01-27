import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Tuple

class PressureGridder_xr:
    def __init__(self, df: pd.DataFrame, 
                 profile_name: str = None,
                 pressure_min: float = 0, 
                 pressure_max: float = 500):
        self.pressure_column = 'Depth__meter_'
        self.profile_name = profile_name
        self.pressure_min = pressure_min
        self.pressure_max = pressure_max
        self.grid_log = []
        
        # Require cast direction
        if 'is_downcast' not in df.columns:
            raise ValueError("DataFrame must have cast direction")
            
        # Split and grid
        ds_down = self._grid_cast(df[df['is_downcast']])
        ds_up = self._grid_cast(df[~df['is_downcast']])
        self.ds = xr.concat([ds_down, ds_up], dim='is_downcast')
    
    def _grid_cast(self, df: pd.DataFrame) -> xr.Dataset:
        """Grid a single cast direction"""
        return (df.select_dtypes(include=[np.number])
                  .sort_values(self.pressure_column)
                  .groupby(self.pressure_column)
                  .mean()
                  .reset_index()
                  .set_index(self.pressure_column)
                  .to_xarray())
    
    def create_pressure_grid(self, interval: float = 0.1) -> np.ndarray:
        """Create regular pressure grid with specified range"""
        return np.arange(self.pressure_min, self.pressure_max + interval, interval)
        
    def interpolate_to_grid(self, 
                          pressure_interval: float = 0.1,
                          method: str = 'linear') -> xr.Dataset:
        """Interpolate all variables at once using xarray"""
        pressure_grid = self.create_pressure_grid(pressure_interval)
        
        # Interpolate to new grid
        ds_grid = self.ds.interp(**{self.pressure_column: pressure_grid},
                                method=method,
                                kwargs={'fill_value': np.nan})
        
        if self.profile_name:
            ds_grid.attrs['profile_name'] = self.profile_name
            
        return ds_grid
    
    
    def clean_name_for_netcdf(self, name: str) -> str:
        """Clean name for NetCDF compatibility"""
        if not isinstance(name, str):
            return 'unnamed'
            
        # Replace common problematic characters
        replacements = {
            '[': '',
            ']': '',
            '(': '',
            ')': '',
            ' ': '_',
            '-': '_',
            ':': '_',
            '.': '_',
            '/': '_',
            '\\': '_',
            '%': 'percent',
            '+': 'plus',
            '°': '',
            'µ': 'u',
            '²': '2',
            '³': '3'
        }
        
        cleaned = name
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
        
        # Remove any remaining non-alphanumeric characters
        cleaned = ''.join(c for c in cleaned if c.isalnum() or c == '_')
        
        # Ensure starts with letter
        if cleaned and not cleaned[0].isalpha():
            cleaned = 'var_' + cleaned
            
        return cleaned

    def prepare_for_netcdf(self, ds: xr.Dataset) -> xr.Dataset:
        """Prepare dataset for NetCDF export"""
        clean_ds = ds.copy()
        
        # Clean variable names
        rename_vars = {}
        for var in ds.data_vars:
            clean_name = self.clean_name_for_netcdf(var)
            rename_vars[var] = clean_name
        clean_ds = clean_ds.rename(rename_vars)
        
        # Clean coordinate names
        rename_coords = {}
        for coord in ds.coords:
            clean_name = self.clean_name_for_netcdf(coord)
            rename_coords[coord] = clean_name
        clean_ds = clean_ds.rename(rename_coords)
        
        return clean_ds

    def export_l3(self, ds_grid: xr.Dataset, output_path: Path) -> Tuple[Path, Path]:
        """Export separate L3 files for up and down casts"""
        clean_profile = self.clean_name_for_netcdf(self.profile_name or 'gridded')
        
        # Clean and prepare datasets
        ds_grid_down = self.prepare_for_netcdf(ds_grid.sel(is_downcast=True))
        ds_grid_up = self.prepare_for_netcdf(ds_grid.sel(is_downcast=False))
        
        # Export downcast
        l3_down_path = output_path / f"L3_{clean_profile}_downcast.nc"
        ds_grid_down.to_netcdf(l3_down_path)
        
        # Export upcast
        l3_up_path = output_path / f"L3_{clean_profile}_upcast.nc"
        ds_grid_up.to_netcdf(l3_up_path)
        
        return l3_down_path, l3_up_path

class DepthGridder_xr:
    """Grid data to regular depth intervals using xarray"""
    
    def __init__(self, df: pd.DataFrame, profile_name: str = None):
        self.df = df
        self.depth_column = 'Depth__meter_'
        self.profile_name = profile_name if profile_name else 'profile'
        
    def interpolate_to_grid(self, depth_interval: float = 0.05) -> xr.Dataset:
        """
        Interpolate data to regular depth grid
        
        Parameters
        ----------
        depth_interval : float
            Interval for depth grid in meters (default: 0.05)
            
        Returns
        -------
        xr.Dataset
            Gridded dataset
        """
        # Create xarray dataset
        ds = xr.Dataset.from_dataframe(self.df)
        
        # Create regular depth grid
        depth_min = np.floor(self.df[self.depth_column].min())
        depth_max = np.ceil(self.df[self.depth_column].max())
        depth_grid = np.arange(depth_min, depth_max + depth_interval, depth_interval)
        
        # Interpolate to regular depth grid
        ds_interp = ds.interp({self.depth_column: depth_grid}, method='linear')
        
        # Add profile metadata
        ds_interp.attrs['profile_name'] = self.profile_name
        ds_interp.attrs['depth_interval'] = depth_interval
        
        return ds_interp