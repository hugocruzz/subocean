from core.executor import Executor
from core.profile import Profile
from gpt_interface.prompt_handler import PromptHandler
import xarray as xr
import pandas as pd
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from typing import List, Tuple
from datetime import datetime
import numpy as np
def find_profile_pairs(l0_dir: Path) -> List[Tuple[Path, Path]]:
    """Find matching .txt and .log files"""
    txt_files = list(l0_dir.glob("*.txt"))
    profile_pairs = []
    
    for txt_file in txt_files:
        log_file = txt_file.with_suffix('.log')
        if log_file.exists():
            profile_pairs.append((txt_file, log_file))
    
    return profile_pairs
def clean_column_name(name: str) -> str:
    """Clean column name for NetCDF compatibility"""
    # Replace brackets, spaces and special chars
    clean = name.replace('[', '').replace(']', '')
    clean = clean.replace(' ', '_')
    clean = clean.replace('(', '').replace(')', '')
    clean = clean.replace('%', 'percent')
    clean = clean.replace('/', 'per')  # Replace forward slashes
    return clean

def process_to_xarray(profile_pairs: List[Tuple[Path, Path]], l1_dir: Path) -> Path:
    """Process multiple profiles into single xarray Dataset"""
    profiles_data = []
    column_mappings = {}  # Track original column names
    
    for txt_path, log_path in profile_pairs:
        profile = Profile(txt_path, log_path)
        df, metadata = profile.load()
        
        # Store original column names and clean
        column_mappings.update({clean_column_name(col): col for col in df.columns})
        df.columns = [clean_column_name(col) for col in df.columns]
        # Debug column types
        print("DataFrame types before conversion:")
        print(df.dtypes)
        
        # Ensure numeric columns are float64
        numeric_columns = df.select_dtypes(include=['float64', 'float32', 'int64', 'int32']).columns
        for col in numeric_columns:
            df[col] = df[col].astype('float64')
        
        # Drop string date columns, keep only datetime
        columns_to_drop = ['Date', 'Time']
        df = df.drop([col for col in columns_to_drop if col in df.columns], axis=1)
        
        # Convert to xarray with datetime index
        ds = xr.Dataset.from_dataframe(df.set_index('datetime'))
        
        if metadata:
            try:
                clean_metadata = {
                    k: str(v) if isinstance(v, (datetime, bool)) else v 
                    for k, v in metadata.to_dict().items()
                }
                ds.attrs.update(clean_metadata)
            except TypeError as e:
                print(f"Warning: Some metadata attributes were not compatible: {e}")
                
        profiles_data.append(ds)
    
    # Debug data types before concat
    print("\nDataset types before concat:")
    for ds in profiles_data:
        print(ds.dtypes)
    combined_ds = xr.concat(profiles_data, dim='profile')
    # Add column mappings as attribute
    combined_ds.attrs['column_mappings'] = str(column_mappings)
    output_path = l1_dir / "combined_profiles.nc"
    
    # Set encoding for numeric variables only
    encoding = {
        var: {'dtype': 'float64'} 
        for var in combined_ds.data_vars
        if np.issubdtype(combined_ds[var].dtype, np.number)
    }
    
    # Set datetime encoding
    encoding['datetime'] = {
        'dtype': 'int64',
        'units': 'seconds since 1970-01-01',
        'calendar': 'proleptic_gregorian'
    }
    
    combined_ds.to_netcdf(output_path, encoding=encoding)
    return output_path
def visualize_combined_profiles(nc_path: Path):
    """Visualize data from NetCDF file"""
    ds = xr.open_dataset(nc_path)
    prompt_handler = PromptHandler(ds)
    
    command = "Create a plot showing CH4 concentration vs depth for all profiles"
    code = prompt_handler.generate_plot_code(command)
    executor = Executor()
    executor.run(code, ds=ds)

if __name__ == "__main__":
    base_dir = Path.cwd()
    data_dir = base_dir / "data"
    l0_dir = data_dir / "Level0"
    l1_dir = data_dir / "Level1"
    l1_dir.mkdir(exist_ok=True)
    
    # Find and process all profiles
    profile_pairs = find_profile_pairs(l0_dir)
    nc_path = process_to_xarray(profile_pairs, l1_dir)
    
    # Visualize combined data
    visualize_combined_profiles(nc_path)