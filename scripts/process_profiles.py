from pathlib import Path
import xarray as xr
import pandas as pd
from typing import Dict, List
import sys
import re
# Add src to path
src_dir = Path.cwd().parent / 'src'
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.profile import Profile
from preprocessing.cleaner import DataCleaner
from preprocessing.derived_parameters import DerivedParameters
from preprocessing.depth_gridder import DepthGridder_xr

def process_profile(data_path: Path, log_path: Path, output_dirs: Dict[str, Path]) -> Dict[str, Path]:
    """Process SubOcean profile through pipeline"""
    # 1. Load Data
    profile = Profile(data_path, log_path)
    df, metadata = profile.load()
    gas_columns = [
                '[CH4] dissolved with water vapour (ppm)',
                '[N2O] dissolved with water vapour (ppm)',
                '[NH3] measured (ppm)',
                '[H2O] measured (%)'
            ]
    # 4. Data Cleaning
    DEFAULT_VALIDATION_RANGES = {
                'Cavity Pressure (mbar)': (29.5, 30.5),
                'Cellule Temperature (Degree Celsius)': (39.5, 40.5),
                'Depth (meter)': (-2, 11000),
                'Flow Carrier Gas (sccm)': (0, 10),
                'Total Flow (sccm)': (0, 100),
                'Ringdown time (microSec)': (10, 30), #Should be 13 +- 1 for CH4 and 26 +- 1 for N2O
                '[CH4] dissolved with water vapour (ppm)': (0, 100),
                'Error Standard': (0, 0.1)  
            }
    
    cleaner = DataCleaner(df,DEFAULT_VALIDATION_RANGES)
    # Apply validation ranges
    df = cleaner.validate_measurements()
    # Calculate RSD and update flags
    df = cleaner.calculate_rsd(gas_columns)
    # Export L1A (raw data with flags)
    df.to_csv(output_dirs["L1"]/f"L1A_{data_path.stem}.csv", index=False)
    
    # Create L1B by applying column-specific flags
    # Apply row-wise filtering based on gas measurements
    cleaner.filter_flagged_row()
    #Strong filter that removes all rows with flagged gas measurements
    cleaner.filter_flagged_rows(columns_to_check=['Error Standard'])
    cleaner.df.to_csv(output_dirs["L1"]/ f"L1B_{data_path.stem}.csv", index=False)

    # 3. Derived Parameters
    derived = DerivedParameters(cleaner.df, gas_columns)
    df = derived.calculate_all()
    df.to_csv(output_dirs["L2"] / f"L2_{data_path.stem}.csv", index=False)
    
    # Clean profile name for NetCDF
    clean_profile_name = clean_string_for_netcdf(data_path.stem)
    
    # Separate and save casts
    l3a_paths = {}
    for cast_type in ['downcast', 'upcast']:
        # Split cast
        mask = df['is_downcast'] if cast_type == 'downcast' else ~df['is_downcast']
        cast_df = df[mask].copy()
        
        if not cast_df.empty:
            # Clean variable names
            cast_df.columns = [clean_string_for_netcdf(col) for col in cast_df.columns]
            
            # Grid the cast along depth
            gridder = DepthGridder_xr(cast_df, profile_name=clean_profile_name)
            ds = gridder.interpolate_to_grid(depth_interval=0.05)  # Grid every 5cm
            
            # Save L3A file
            output_path = output_dirs["L3A"] / f"L3A_{clean_profile_name}_{cast_type}.nc"
            ds.to_netcdf(output_path)
            l3a_paths[cast_type] = output_path
    
    return {
        "L1A": output_dirs["L1"] / f"L1A_{data_path.stem}.csv",
        "L1B": output_dirs["L1"] / f"L1B_{data_path.stem}.csv",
        "L2": output_dirs["L2"] / f"L2_{data_path.stem}.csv",
        "L3A": l3a_paths
    }

def combine_l3_profiles(l3a_dir: Path, cast_type: str = 'downcast') -> xr.Dataset:
    """Combine L3A profiles into L3B dataset"""
    l3a_files = list(l3a_dir.glob(f"L3A_*_{cast_type}.nc"))
    if not l3a_files:
        raise FileNotFoundError(f"No L3A {cast_type} files found in {l3a_dir}")
    
    datasets = []
    for file in l3a_files:
        ds = xr.open_dataset(file)
        my_lst =  file.stem.split("_")[:-1]
        profile_id = '_'.join(map(str, my_lst))
        # Create profile dimension instead of scalar coordinate
        ds = ds.expand_dims({'profile': [profile_id]})
        datasets.append(ds)
    
    return xr.concat(datasets, dim='profile')
def clean_name_for_netcdf(name: str) -> str:
    import re
    """Clean filename to be NetCDF compatible"""
    # Replace invalid characters with underscore
    clean = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    # Ensure doesn't start with number
    if clean[0].isdigit():
        clean = 'p_' + clean
    return clean

def clean_string_for_netcdf(s: str) -> str:
    """Clean string to be NetCDF compatible"""
    # Remove special characters except underscore
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', s)
    # Ensure doesn't start with number
    if clean[0].isdigit():
        clean = 'p' + clean
    return clean

if __name__ == "__main__":
    # Setup paths
    base_dir = Path.cwd()
    data_dir = base_dir / "data"
    l0_dir = data_dir / "Level0"
    
    # Create output directories with L3A and L3B
    output_dirs = {
        'L1': data_dir / "Level1",
        'L2': data_dir / "Level2",
        'L3A': data_dir / "Level3/L3A",
        'L3B': data_dir / "Level3/L3B"
    }
    for dir_path in output_dirs.values():
        dir_path.mkdir(exist_ok=True, parents=True)
    
    # Process all profiles to L3A
    for data_path in l0_dir.glob("*.txt"):
        log_path = data_path.with_suffix('.log')
        if log_path.exists():
            process_profile(data_path, log_path, output_dirs)
    
    # Create L3B combined profiles
    for cast_type in ['downcast', 'upcast']:
        combined_ds = combine_l3_profiles(output_dirs['L3A'], cast_type)
        output_path = output_dirs['L3B'] / f"L3B_combined_{cast_type}.nc"
        combined_ds.to_netcdf(output_path)
    print(f"Combined downcast dataset exported to {output_path}")
    print(f"Combined upcast dataset exported to {output_path}")
