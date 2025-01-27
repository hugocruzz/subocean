import xarray as xr
import plotly.subplots as sp
import plotly.graph_objects as go
import numpy as np
from pathlib import Path

def visualize_combined_profiles(netcdf_path):
    # Load data
    try:
        ds = xr.open_dataset(netcdf_path)
    except Exception as e:
        print(f"Error loading netCDF file: {e}")
        return

    # Get total number of profiles
    n_profiles = len(ds.profile)
    n_windows = int(np.ceil(n_profiles / 10))
    
    # Get all variables except datetime and profile
    variables = [var for var in ds.data_vars if var != 'datetime']
    
    for window in range(n_windows):
        start_idx = window * 10
        end_idx = min((window + 1) * 10, n_profiles)
        n_plots = end_idx - start_idx
        
        # Calculate grid layout
        n_rows = int(np.ceil(np.sqrt(n_plots)))
        n_cols = int(np.ceil(n_plots / n_rows))
        
        fig = sp.make_subplots(
            rows=n_rows, 
            cols=n_cols,
            subplot_titles=[f'Profile {i}' for i in range(start_idx, end_idx)],
            shared_xaxes=True,
            shared_yaxes=True
        )
        
        # Add traces for first variable
        var = variables[0]
        for i, prof_idx in enumerate(range(start_idx, end_idx)):
            row = i // n_cols + 1
            col = i % n_cols + 1
            
            prof_data = ds.isel(profile=prof_idx)
            
            # Convert DataArray to numpy array
            x_data = prof_data[var].values
            y_data = prof_data['Depth_meter'].values
            
            fig.add_trace(
                go.Scatter(
                    x=x_data,
                    y=y_data,
                    name=f'Profile {prof_idx}',
                    showlegend=False
                ),
                row=row, col=col
            )
        
        # Update layout with proper sizing
        fig.update_layout(
            height=800,  # Fixed height
            width=1200,  # Fixed width
            title=f'Profiles {start_idx}-{end_idx-1}',
            showlegend=False,
            template='plotly_white',
            margin=dict(t=100, b=50, l=50, r=50)
        )

        # Update subplot spacing
        fig.update_layout(
            grid=dict(
                rows=n_rows,
                columns=n_cols,
                pattern='independent',
                roworder='top to bottom'
            )
        )

        '''# Add horizontal spacing between subplots
        fig.update_layout(
            horizontal_spacing=0.1,
            vertical_spacing=0.1
        )'''

        # Add dropdown menu with numpy array conversion
        buttons = []
        for var in variables:
            x_data = [ds.isel(profile=i)[var].values for i in range(start_idx, end_idx)]
            buttons.append({
                'method': 'update',
                'label': var,
                'args': [{'x': x_data}]
            })
            
        fig.update_layout(
            updatemenus=[{
                'buttons': buttons,
                'direction': 'down',
                'showactive': True,
                'x': 0.1,
                'y': 1.15
            }]
        )
        
        # Update all y-axes to be reversed
        for i in range(1, n_rows * n_cols + 1):
            fig.update_yaxes(autorange="reversed", row=i//n_cols+1, col=i%n_cols+1)
        
        fig.show()

if __name__ == "__main__":
    l1_dir = Path("data/Level1")
    netcdf_path = l1_dir / "combined_profiles.nc"
    visualize_combined_profiles(netcdf_path)