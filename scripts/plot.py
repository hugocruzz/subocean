import plotly.graph_objects as go
import xarray as xr
from pathlib import Path
from typing import List, Optional, Tuple
from plotly.subplots import make_subplots

class ProfilePlotter:
    def __init__(self, downcast_path: Path, upcast_path: Path):
        """Initialize with paths to both downcast and upcast NetCDF files"""
        self.ds_down = xr.open_dataset(downcast_path)
        self.ds_up = xr.open_dataset(upcast_path)
        
        # Get and verify dimensions
        self.dims = list(self.ds_down.dims)
        if list(self.ds_up.dims) != self.dims:
            raise ValueError("Downcast and upcast datasets must have same dimensions")
        if len(self.dims) != 2:
            raise ValueError("Datasets must have exactly 2 dimensions")
            
        # Assign dimensions
        self.y_axis = self.dims[0]  # First dimension as y-axis
        self.profile_dim = self.dims[1]  # Second dimension for profiles
        
        # Setup remaining attributes
        self.profiles = list(self.ds_down[self.profile_dim].values)
        self.variables = self._get_base_variables()
        self.colors = {'down': 'blue', 'up': 'red'}
    
    def _get_base_variables(self) -> List[str]:
        """Get unique variable names from both datasets"""
        down_vars = set(var for var in self.ds_down.data_vars)
        up_vars = set(var for var in self.ds_up.data_vars)
        return sorted(down_vars.intersection(up_vars))
    
    def create_subplot_grid(self, n_profiles: int) -> Tuple[int, int]:
        """Calculate optimal subplot grid"""
        if n_profiles <= 3:
            return 1, n_profiles
        elif n_profiles <= 6:
            return 2, 3
        else:
            return 3, 4
    

    def create_interactive_plot(self, max_profiles: int = 10) -> go.Figure:
        n_profiles = min(len(self.profiles), max_profiles)
        rows, cols = self.create_subplot_grid(n_profiles)
        
        fig = make_subplots(
            rows=rows, cols=cols,
            shared_yaxes=True,
            subplot_titles=[f"Profile {p}" for p in self.profiles[:n_profiles]]
        )
        
        first_var = "_CH4__dissolved_with_water_vapour__ppm_"
        
        for i, profile in enumerate(self.profiles[:n_profiles]):
            row = (i // cols) + 1
            col = (i % cols) + 1
            
            # Plot downcast data
            down_data = self.ds_down.sel({self.profile_dim: profile})
            fig.add_trace(
                go.Scatter(
                    x=down_data[first_var],
                    y=down_data[self.y_axis],
                    name=f"{profile} (down)",
                    line=dict(color=self.colors['down'])
                ),
                row=row, col=col
            )
            
            # Plot upcast data
            up_data = self.ds_up.sel({self.profile_dim: profile})
            fig.add_trace(
                go.Scatter(
                    x=up_data[first_var],
                    y=up_data[self.y_axis],
                    name=f"{profile} (up)",
                    line=dict(color=self.colors['up'])
                ),
                row=row, col=col
            )
                        
            fig.update_yaxes(
                title_text="Depth (meter)" if col == 1 else "",
                autorange="reversed",
                row=row, col=col
            )
        
        return fig

if __name__ == "__main__":
    base_dir = Path.cwd()
    l3_down_path = r"data\Level3\L3B\L3B_combined_downcast.nc"
    l3_up_path = r"data\Level3\L3B\L3B_combined_upcast.nc"
    
    plotter = ProfilePlotter(l3_down_path, l3_up_path)
    fig = plotter.create_interactive_plot()
    fig.show()