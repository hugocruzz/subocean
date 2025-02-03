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
from profile_plot import create_measurement_plot, create_diagnostic_plot, group_related_parameters

# Unified validation configuration
VALIDATION_CONFIG = {
    'standard_ranges': {
        'Cavity Pressure (mbar)': (29.5, 30.5),
        'Cellule Temperature (Degree Celsius)': (39.5, 40.5),
        'Depth (meter)': (-2, 11000),
        'Flow Carrier Gas (sccm)': (0, 10),
        'Total Flow (sccm)': (0, 100),
        'Ringdown time (microSec)': (10, 30), #Should be 13 +- 1 for CH4 and 26 +- 1 for N2O
        'Error Standard': (0, 0.1),
        '[C2H6] dissolved (ppm)': (0, 100),
        'Delta 13 CH4 (per-mille)': (-15000, 15000),
    },
    'gas_rules': {
        '[CH4] dissolved with water vapour (ppm)': {
            'range': (0, 100),
            'rsd_threshold': 1
        },
        '[CH4] dissolved with water vapour (nmol/L)': {
            'range': (0, 100),
            'rsd_threshold': 0.01
        },
        '[N2O] dissolved with water vapour (ppm)': {
            'range': (0, 100),
            'rsd_threshold': 0.01
        },
        '[N2O] dissolved with water vapour (nmol/L)': {
            'range': (0, 100),
            'rsd_threshold': 0.01
        },
    }
}

def save_metadata_csv(metadata: dict, output_path: Path) -> None:
    """Save metadata as CSV file"""
    # Convert metadata dict to DataFrame
    meta_df = pd.DataFrame([metadata])
    meta_path = output_path.with_name(f"{output_path.stem}_metadata.csv")
    meta_df.to_csv(meta_path, index=False)

def parse_metadata(metadata_obj) -> dict:
    """Convert metadata object (JSON or SubOceanMetadata) to dictionary"""
    if isinstance(metadata_obj, dict):
        return metadata_obj
    elif hasattr(metadata_obj, '__dict__'):
        return vars(metadata_obj)
    else:
        return {k: str(v) for k, v in metadata_obj.__getattribute__.items()}

def add_netcdf_attributes(dataset: xr.Dataset, metadata_obj, expedition_name: str) -> xr.Dataset:
    """Add metadata as global attributes to NetCDF dataset"""
    # Get metadata as dictionary
    metadata_dict = parse_metadata(metadata_obj)
    
    # Add expedition name
    metadata_dict['expedition_name'] = expedition_name
    
    # Clean metadata values for NetCDF compatibility
    clean_metadata = {
        clean_name_for_netcdf(k): clean_string_for_netcdf(str(v))
        for k, v in metadata_dict.items()
    }
    
    # Set attributes
    dataset.attrs.update(clean_metadata)
    return dataset

def clean_column_names(df):
    """Clean DataFrame column names for NetCDF compatibility"""
    # Replace brackets, spaces and special chars with underscore
    clean_cols = {}
    for col in df.columns:
        clean = re.sub(r'[\[\]\(\)\s\\/]+', '_', col)
        clean = re.sub(r'[^a-zA-Z0-9_]+', '', clean)
        # Ensure doesn't start with number
        if clean[0].isdigit():
            clean = 'var_' + clean
        clean_cols[col] = clean
    return df.rename(columns=clean_cols)

def process_profile(data_path: Path, log_path: Path, output_dirs: Dict[str, Path], expedition_name: str) -> Dict[str, Path]:
    """Process SubOcean profile through pipeline"""
    # 1. Load Data
    profile = Profile(data_path, log_path)
    df, metadata = profile.load()
    # 4. Data Cleaning
    cleaner = DataCleaner(df)
    # Calculate RSD and update flags
    df = cleaner.calculate_rsd(VALIDATION_CONFIG['gas_rules'].keys())
    # Apply validation ranges
    df = cleaner.validate_data(VALIDATION_CONFIG)
    # Export L1A (raw data with flags)
    l1a_path = output_dirs["L1"]/f"L1A_{data_path.stem}.csv"
    df.to_csv(l1a_path, index=False)
    save_metadata_csv(metadata, l1a_path)
    
    # Create L1B by applying column-specific flags
    # Apply row-wise filtering based on gas measurements
    cleaner.filter_flagged_row()
    #Strong filter that removes all rows with flagged gas measurements
    cleaner.filter_flagged_rows(columns_to_check=['Error Standard'])
    l1b_path = output_dirs["L1"]/ f"L1B_{data_path.stem}.csv"
    cleaner.df.to_csv(l1b_path, index=False)
    save_metadata_csv(metadata, l1b_path)

    
    derived = DerivedParameters(cleaner.df)
    df = derived.calculate_all()
    
    # Export L2A as CSV with metadata and expedition name
    l2a_path = output_dirs["L2A"] / f"L2A_{expedition_name}_{data_path.stem}.csv"
    df.to_csv(l2a_path, index=False)
    save_metadata_csv(metadata, l2a_path)
    
    # Export L2B as NetCDF with cleaned column names
    l2b_path = output_dirs["L2B"] / f"L2B_{expedition_name}_{data_path.stem}.nc"
    
    # Clean DataFrame column names before converting to xarray
    df_clean = clean_column_names(df)
    ds = df_clean.set_index('datetime').to_xarray()
    
    # Add metadata as attributes
    ds = add_netcdf_attributes(ds, metadata, expedition_name)
    ds.to_netcdf(l2b_path)
    
    # Create plots directory
    plots_dir = output_dirs["figures"] / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate and save plots
    try:
        # Get parameter groups and diagnostics
        param_groups, diag_params = group_related_parameters(df)
        
        # Create timestamp for plot titles
        timestamp = pd.to_datetime(df['datetime'].iloc[0]).strftime("%Y-%m-%d %H:%M")
        
        # Generate and save measurement plot
        fig_meas = create_measurement_plot(df, param_groups, timestamp)
        meas_path = plots_dir / f"{data_path.stem}_measurements.html"
        fig_meas.write_html(str(meas_path))
        
        # Generate and save diagnostic plot
        fig_diag = create_diagnostic_plot(df, diag_params, timestamp)
        diag_path = plots_dir / f"{data_path.stem}_diagnostics.html"
        fig_diag.write_html(str(diag_path))
        
    except Exception as e:
        print(f"Error creating plots for {data_path.stem}: {str(e)}")
    
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
            output_path = output_dirs["L3A"] / f"L3A_{expedition_name}_{clean_profile_name}_{cast_type}.nc"
            ds.to_netcdf(output_path)
            l3a_paths[cast_type] = output_path
    
    return {
        "L1A": l1a_path,
        "L1B": l1b_path,
        "L2A": l2a_path,
        "L2B": l2b_path,
        "L2_plots": {
            "measurements": meas_path,
            "diagnostics": diag_path
        },
        "L3A": l3a_paths
    }

def combine_l3_profiles(l3a_dir: Path, cast_type: str = 'downcast') -> xr.Dataset:
    """Combine L3A profiles into L3B dataset, searching in all subdirectories"""
    # Use rglob to search recursively
    l3a_files = list(l3a_dir.rglob(f"L3A_*_{cast_type}.nc"))
    if not l3a_files:
        raise FileNotFoundError(f"No L3A {cast_type} files found in {l3a_dir}")
    
    # Group files by gas type (subdirectory)
    gas_groups = {}
    for file in l3a_files:
        # Get gas type from parent directory name
        gas_type = file.parent.name
        if gas_type not in gas_groups:
            gas_groups[gas_type] = []
        gas_groups[gas_type].append(file)
    
    # Process each gas type separately
    combined_datasets = {}
    for gas_type, files in gas_groups.items():
        datasets = []
        for file in files:
            ds = xr.open_dataset(file)
            my_lst = file.stem.split("_")[:-1]
            profile_id = '_'.join(map(str, my_lst))
            # Add gas type to profile metadata
            ds.attrs['gas_type'] = gas_type
            # Create profile dimension
            ds = ds.expand_dims({'profile': [profile_id]})
            datasets.append(ds)
        
        if datasets:
            combined_datasets[gas_type] = xr.concat(datasets, dim='profile')
    
    return combined_datasets

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

def main(expedition_name: str):
    # Base directories
    base_dir = Path.cwd()
    data_dir = base_dir / "data" / expedition_name
    figures_dir = base_dir / "figures" / expedition_name
    l0_dir = data_dir / "Level0"
    
    # Update output directories
    output_dirs = {
        'L1': data_dir / "Level1",
        'L2A': data_dir / "Level2/L2A",  # Changed from L2
        'L2B': data_dir / "Level2/L2B",  # Added L2B
        'L3A': data_dir / "Level3/L3A",
        'L3B': data_dir / "Level3/L3B",
        'figures': figures_dir
    }
    
    # Create base output directories
    for dir_path in output_dirs.values():
        dir_path.mkdir(exist_ok=True, parents=True)
    
    # Mirror directory structure for both data and figures
    subdirs = [p for p in l0_dir.glob('*') if p.is_dir()]
    for subdir in subdirs:
        subdir_name = subdir.relative_to(l0_dir)
        # Create data subdirs
        for level_dir in [d for k,d in output_dirs.items() if k != 'figures']:
            (level_dir / subdir_name).mkdir(exist_ok=True, parents=True)
        # Create figures subdir
        (figures_dir / subdir_name).mkdir(exist_ok=True, parents=True)
    
    # Process profiles
    for data_path in l0_dir.rglob("*.txt"):
        log_path = data_path.with_suffix('.log')
        if log_path.exists():
            rel_path = data_path.relative_to(l0_dir)
            level_paths = {
                level: base_dir / rel_path.parent
                for level, base_dir in output_dirs.items()
            }
            process_profile(data_path, log_path, level_paths, expedition_name)
    '''    
    # Create L3B combined profiles
    for cast_type in ['downcast', 'upcast']:
        # Get combined datasets (dictionary by gas type)
        combined_datasets = combine_l3_profiles(output_dirs['L3A'], cast_type)
        
        # Save each gas type dataset separately
        for gas_type, dataset in combined_datasets.items():
            # Create gas type subdirectory in L3B
            l3b_subdir = output_dirs['L3B'] / gas_type
            l3b_subdir.mkdir(exist_ok=True, parents=True)
            
            # Add metadata as attributes
            dataset = add_netcdf_attributes(dataset, metadata, expedition_name)
            
            # Create output path with gas type
            output_path = l3b_subdir / f"L3B_{expedition_name}_{gas_type}_{cast_type}.nc"
            
            # Save dataset
            dataset.to_netcdf(output_path)
            print(f"Saved L3B dataset for {gas_type} to {output_path}")'''
if __name__ == "__main__":
    main(expedition_name="lexplore")