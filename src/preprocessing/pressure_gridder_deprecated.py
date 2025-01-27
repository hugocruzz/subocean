import pandas as pd
import xarray as xr
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, List

class PressureGridder:
    """Standardize profiles on pressure grid"""
    
    def __init__(self, df: pd.DataFrame, profile_name: str = None):
        self.df = df.copy()
        self.grid_log = []
        self.pressure_column = 'Hydrostatic pressure (bar)'
        self.profile_name = profile_name

    def get_numeric_columns(self) -> List[str]:
        """Get list of numeric columns suitable for interpolation"""
        return self.df.select_dtypes(include=[np.number]).columns.tolist()
        
    def add_cast_direction(self) -> None:
        """Add cast direction column (True for downcast, False for upcast)"""
        pressure_grad = self.df[self.pressure_column].diff()
        self.df['is_downcast'] = pressure_grad > 0

    def separate_casts(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Separate upcast and downcast using boolean mask"""
        # Add cast direction if not present
        if 'is_downcast' not in self.df.columns:
            self.add_cast_direction()
            
        # Separate based on boolean mask
        downcast = self.df[self.df['is_downcast']].copy()
        upcast = self.df[~self.df['is_downcast']].copy()
        
        return downcast, upcast
    
    def create_pressure_grid(self, interval: float = 0.1) -> np.ndarray:
        """Create regular pressure grid in bars"""
        pressure_min = self.df[self.pressure_column].min()
        pressure_max = self.df[self.pressure_column].max()
        return np.arange(pressure_min, pressure_max + interval, interval)
    
    def interpolate_to_grid(self, 
                    pressure_interval: float = 0.1,
                    exclude_cols: Optional[list] = None) -> xr.Dataset:
        """Interpolate data onto regular pressure grid"""
        numeric_cols = self.get_numeric_columns()
        if exclude_cols:
            numeric_cols = [col for col in numeric_cols if col not in exclude_cols]
                    
        # Ensure cast direction is added
        if 'is_downcast' not in self.df.columns:
            self.add_cast_direction()
        pressure_col = self.pressure_column
        pressure_grid = self.create_pressure_grid(pressure_interval)
        ds = xr.Dataset(coords={'pressure': pressure_grid})
        
        for col in numeric_cols:
            if (col != pressure_col and col != 'is_downcast'):
                try:
                    valid_data = self.df[[pressure_col, col, 'is_downcast']].dropna()
                    if len(valid_data) > 1:  # Need at least 2 points
                        clean_name = self.clean_variable_name(col)
                        
                        # Get overall pressure range
                        p_min = valid_data[pressure_col].min()
                        p_max = valid_data[pressure_col].max()
                        
                        # Create mask for valid pressure range
                        valid_range = (pressure_grid >= p_min) & (pressure_grid <= p_max)
                        
                        # Initialize arrays for valid range only
                        interp_values = np.full(len(pressure_grid[valid_range]), np.nan)
                        cast_direction = np.full(len(pressure_grid[valid_range]), np.nan)
                        
                        # Sort by pressure to ensure proper interpolation
                        sorted_data = valid_data.sort_values(pressure_col)
                        
                        # Interpolate within valid range
                        interp_values = np.interp(
                            pressure_grid[valid_range],
                            sorted_data[pressure_col],
                            sorted_data[col]
                        )
                        
                        # Interpolate cast direction (as float, convert to bool later)
                        cast_direction = np.interp(
                            pressure_grid[valid_range],
                            sorted_data[pressure_col],
                            sorted_data['is_downcast'].astype(float)
                        )
                        
                        # Create full arrays with NaN outside valid range
                        full_values = np.full_like(pressure_grid, np.nan)
                        full_direction = np.full_like(pressure_grid, np.nan)
                        
                        full_values[valid_range] = interp_values
                        full_direction[valid_range] = cast_direction
                        
                        # Add to dataset
                        ds[clean_name] = ('pressure', full_values)
                        ds[f"{clean_name}_is_downcast"] = ('pressure', full_direction > 0.5)
                        
                except Exception as e:
                    self.grid_log.append(f"Error interpolating {col}: {str(e)}")
        
        return ds

    def export_l3(self, ds: xr.Dataset, output_path: Path) -> Path:
        """Export L3 gridded data with profile name"""
        if self.profile_name:
            l3_path = output_path / f"L3_{self.profile_name}.nc"
        else:
            l3_path = output_path / "L3_gridded.nc"
        ds.to_netcdf(l3_path)
        self.grid_log.append(f"Exported L3 data to {l3_path}")
        return l3_path

    def clean_variable_name(self, name: str) -> str:
        """
        Clean variable names for NetCDF compatibility.
        - Remove brackets and parentheses
        - Replace spaces with underscores
        - Convert units and special characters
        - Ensure valid NetCDF naming
        """
        cleaned = (name
                  .replace('[', '')
                  .replace(']', '')
                  .replace('(', '')
                  .replace(')', '')
                  .replace(' ', '_')
                  .replace('%', 'percent')
                  .replace('/', '_per_')
                  .replace('-', '_')
                  .replace('.', '_')
                  .replace(',', '_'))
        
        # Remove any remaining special characters
        cleaned = ''.join(c for c in cleaned if c.isalnum() or c == '_')
        
        # Ensure starts with letter (NetCDF requirement)
        if cleaned and not cleaned[0].isalpha():
            cleaned = 'var_' + cleaned
            
        return cleaned
    
    def clean_name_for_netcdf(self, name: str) -> str:
        """Clean name for NetCDF compatibility"""
        # Replace invalid characters
        cleaned = (name.replace('-', '_')
                      .replace(' ', '_')
                      .replace(':', '_')
                      .replace('.', '_')
                      .replace('/', '_')
                      .replace('\\', '_'))
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
        clean_vars = {}
        for var in ds.data_vars:
            clean_name = self.clean_name_for_netcdf(var)
            clean_vars[var] = clean_name
        clean_ds = ds.rename(clean_vars)
        
        # Clean coordinate names
        clean_coords = {}
        for coord in ds.coords:
            clean_name = self.clean_name_for_netcdf(coord)
            clean_coords[coord] = clean_name
        clean_ds = clean_ds.rename(clean_coords)
        
        return clean_ds

    def export_l3(self, ds: xr.Dataset, output_path: Path) -> Path:
        """Export L3 gridded data"""
        # Clean profile name
        clean_profile = self.clean_name_for_netcdf(self.profile_name or 'gridded')
        l3_path = output_path / f"L3_{clean_profile}.nc"
        
        # Prepare dataset
        clean_ds = self.prepare_for_netcdf(ds)
        
        # Export
        clean_ds.to_netcdf(l3_path)
        self.grid_log.append(f"Exported L3 data to {l3_path}")
        return l3_path
