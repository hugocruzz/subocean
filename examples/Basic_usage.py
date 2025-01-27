import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import xarray as xr
from typing import Optional, Dict, List, Tuple
# Set interactive backend for standalone script
plt.ion()  # Enable interactive mode

# Add src to path
src_dir = Path.cwd().parent / 'src'
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.profile import Profile
from preprocessing.cleaner import DataCleaner
from preprocessing.derived_parameters import DerivedParameters
from preprocessing.error_handler import ErrorHandler
from preprocessing.pressure_gridder import DepthGridder
from gpt_interface.prompt_handler import PromptHandler
from core.executor import Executor

def process_profile(data_path: Path, log_path: Path, output_dir: Path) -> Dict[str, Path]:
    """Process SubOcean profile through pipeline"""
    print(f"Processing {data_path.name}")
    
    # 1. Load Data
    profile = Profile(data_path, log_path)
    df, metadata = profile.load()
    print(f"Loaded {len(df)} measurements")
    
    # 2. L1A: Data Validation and Flags
    cleaner = DataCleaner(df)
    gas_columns = [
        '[CH4] dissolved with water vapour (ppm)',
        '[N2O] dissolved with water vapour (ppm)',
        '[NH3] measured (ppm)',
        '[H2O] measured (%)'
    ]
    
    # Calculate RSD and validate measurements
    df = cleaner.validate_measurements()
    df = cleaner.calculate_rsd(gas_columns)
    cleaner.export_l1a(output_dir)
    
    # 3. L1B: Filtered Data
    df_l1b = cleaner.export_l1b(output_dir)
    
    # 4. L2: Derived Parameters
    derived = DerivedParameters(df_l1b)
    
    # Apply time delay correction
    carrier_gas_flow = df["Flow Carrier Gas (sccm)"].mean() / 60  # mL/s
    time_delay = 0.5 / carrier_gas_flow  # seconds
    df = derived.apply_time_delay_correction(gas_columns, time_delay)
    
    # Calculate other parameters
    df = derived.apply_moving_average('[H2O] measured (%)', window=5)
    df = derived.calculate_flows()
    df = derived.calculate_gas_corrections()
    
    # Export L2 data
    l2_path = output_dir / f"L2_{data_path.stem}.csv"
    df.to_csv(l2_path, index=False)
    print(f"Exported L2 data to {l2_path}")
    
    # 5. L3: Gridded Data
    gridder = DepthGridder(df)
    ds = gridder.interpolate_to_grid(depth_interval=0.5)
    l3_path = gridder.export_l3(ds, output_dir)
    
    return {
        "L1A": output_dir / "L1A_data.csv",
        "L1B": output_dir / "L1B_data.csv",
        "L2": l2_path,
        "L3": l3_path
    }

def visualize_profile(data_path: Path):
    """Visualize processed profile using GPT"""
    # Load Level 1 data
    df = pd.read_csv(data_path)
    
    executor = Executor()
    # Setup visualization
    prompt_handler = PromptHandler(df)
    command = "Create a plot with CH4 concentration with depth on the y-axis going from surface to bottom"
    
    # Generate and execute plot
    code = prompt_handler.generate_plot_code(command)
    print("\nExecuting visualization...")
    print(code)

    # Execute with DataFrame
    error = executor.run(code, df=df)

    if error:
        print(f"Error during execution: {error}")
    else:
        print("Successfully executed")
    plt.show()

import tkinter as tk
from tkinter import filedialog
import plotly.graph_objects as go
from pathlib import Path

def select_and_plot(gpt_tool=False):
    # Create root window and hide it
    root = tk.Tk()
    root.withdraw()

    # Open file dialog
    file_path = filedialog.askopenfilename(
        title="Select Profile",
        filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")],
        initialdir=str(l0_dir)
    )
    
    if file_path:
        # Convert to Path object
        data_path = Path(file_path)
        log_path = data_path.with_suffix('.log')
        
        # Process profile
        l1_paths = process_profile(data_path, log_path, l1_dir)
        
        # Read the processed profile
        df = pd.read_csv(l1_paths["L2"])
        if gpt_tool:
            visualize_profile(l1_paths["L2"])
        else: 
            # Create figure
            fig = go.Figure()
            
            # Add traces for each variable
            for col in df.columns:
                if col != 'Depth (meter)':
                    fig.add_trace(
                        go.Scatter(
                            x=df[col],
                            y=df['datetime'],
                            name=col,
                            visible='legendonly'
                        )
                    )
            
            # Update layout
            fig.update_layout(
                yaxis=dict(
                    title='datetime',
                    autorange='reversed'
                ),
                xaxis=dict(title='Values'),
                height=1000,
                width=2000,
                showlegend=True
            )
            
            # Show plot
            fig.show()

if __name__ == "__main__":
    # Setup paths
    base_dir = Path.cwd()
    data_dir = base_dir / "data"
    l0_dir = data_dir / "Level0"
    
    # Create output directories
    output_dirs = {
        'L1': data_dir / "Level1",
        'L2': data_dir / "Level2",
        'L3': data_dir / "Level3"
    }
    for dir_path in output_dirs.values():
        dir_path.mkdir(exist_ok=True)
    
    # Select and process file
    root = tk.Tk()
    root.withdraw()
    
    '''file_path = filedialog.askopenfilename(
        title="Select Profile to Process",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        initialdir=str(l0_dir)
    )'''
    file_path = r'data\Level0\SubOceanExperiment2024-11-27T12-58-44.txt'
    
    if file_path:
        data_path = Path(file_path)
        log_path = data_path.with_suffix('.log')
        
        # Process data through pipeline
        output_files = process_profile(
            data_path=data_path,
            log_path=log_path,
            output_dir=output_dirs['L1']
        )
        
        # Visualization options
        vis_options = {
            '1': 'Plot L1 Data (raw + flags)',
            '2': 'Plot L2 Data (processed)',
            '3': 'Plot L3 Data (gridded)',
            'q': 'Quit'
        }
        
        while True:
            print("\nVisualization Options:")
            for key, value in vis_options.items():
                print(f"{key}: {value}")
                
            choice = input("\nSelect visualization option: ")
            
            if choice == 'q':
                break
            elif choice == '1':
                visualize_profile(output_files['L1B'])
            elif choice == '2':
                visualize_profile(output_files['L2'])
            elif choice == '3':
                # Load and plot L3 netCDF
                ds = xr.open_dataset(output_files['L3'])
                
                fig = go.Figure()
                
                # Plot downcast and upcast
                for var in ds.data_vars:
                    if 'down' in var:
                        fig.add_trace(
                            go.Scatter(
                                x=ds[var],
                                y=ds.depth,
                                name=f"{var}",
                                visible='legendonly'
                            )
                        )
                
                fig.update_layout(
                    yaxis=dict(
                        title='Depth (m)',
                        autorange='reversed'
                    ),
                    height=1000,
                    width=1500,
                    showlegend=True
                )
                
                fig.show()