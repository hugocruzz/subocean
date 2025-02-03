import panel as pn
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path
from plotly.subplots import make_subplots
from src.preprocessing.cleaner import DataCleaner

class InteractiveProfilePlotter:
    def __init__(self, l2_dir: Path):
        self.l2_dir = l2_dir
        self.profiles = []
        self.variables = []
        self.colors = {'up': 'red', 'down': 'blue'}
        # Add storage for current values
        self.current_var = None
        self.current_min = None
        self.current_max = None
        self.current_rsd = None
        self.current_yaxis = None  # Add storage for y-axis selection
        self.load_data()
        
    def load_data(self):
        """Load all L2 profiles"""
        for file in self.l2_dir.glob('L2_*.csv'):
            df = pd.read_csv(file)
            df['profile'] = file.stem
            self.profiles.append(df)
            if not self.variables:
                self.variables = list(df.columns)

    def create_interactive_cleaning_plot(self):
        """Create interactive plot with cleaning controls"""
        # Create cleaner instance    # 4. Data Cleaning
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
        # Initialize Panel
        pn.extension()
        
        # Create widgets for cleaning parameters
        yaxis_select = pn.widgets.Select(
            name='Y-Axis Variable',
            options=self.variables,
            value='Depth (meter)'  # Set depth as default
        )
        
        var_select = pn.widgets.Select(
            name='X-Axis Variable', 
            options=self.variables,
            value=self.variables[4]
        )
        
        min_val = pn.widgets.FloatInput(
            name='Min Value', 
            value=DEFAULT_VALIDATION_RANGES.get(
                self.variables[4], (0, 100)
            )[0]
        )
        
        max_val = pn.widgets.FloatInput(
            name='Max Value',
            value=DEFAULT_VALIDATION_RANGES.get(
                self.variables[4], (0, 100)
            )[1]
        )
        
        rsd_threshold = pn.widgets.FloatInput(
            name='RSD Threshold',
            value=0.001,
            step=0.0001
        )

        # Add process button
        process_button = pn.widgets.Button(name='Process', button_type='primary')

        plot_pane = pn.pane.Plotly(sizing_mode='stretch_width', height=1600)  # Doubled height

        def update_plot_on_click(event):
            plot_pane.object = update_plot(
                var_select.value,
                yaxis_select.value,
                min_val.value,
                max_val.value,
                rsd_threshold.value
            )

        process_button.on_click(update_plot_on_click)

        def update_plot(var, yvar, min_v, max_v, rsd_thresh):
            self.current_var = var
            self.current_min = min_v
            self.current_max = max_v
            self.current_yaxis = yvar
            
            # Calculate grid dimensions
            n_profiles = len(self.profiles)
            n_cols = 3  # Changed to 3 columns
            n_rows = (n_profiles + n_cols - 1) // n_cols
            
            # Create figure with grid layout
            fig = make_subplots(
                rows=n_rows,
                cols=n_cols,
                shared_xaxes=True,
                shared_yaxes=True,
                subplot_titles=[df['profile'].iloc[0] for df in self.profiles] + [''] * (n_rows * n_cols - n_profiles),
                vertical_spacing=0.15,
                horizontal_spacing=0.1
            )
            
            # Set figure dimensions and layout
            fig.update_layout(
                height=800 * n_rows,  # Doubled height per row
                width=1200,
                showlegend=True,
                template="simple_white",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=50, b=50, l=50, r=50)
            )
            
            for i, profile_df in enumerate(self.profiles):
                row_idx = (i // n_cols) + 1
                col_idx = (i % n_cols) + 1
                
                cleaner = DataCleaner(profile_df, DEFAULT_VALIDATION_RANGES)
                ranges = {var: (min_v, max_v)}
                df_cleaned = cleaner.validate_measurements(ranges)
                df_cleaned = cleaner.calculate_rsd([var], threshold=rsd_thresh)
                
                # Determine if upcast or downcast
                is_downcast = 'down' in profile_df['profile'].iloc[0].lower()
                profile_color = '#1f77b4' if is_downcast else '#ff7f0e'  # Blue for downcast, Orange for upcast
                
                # Add raw data trace with lines
                fig.add_trace(
                    go.Scatter(
                        x=profile_df[var],
                        y=profile_df[yvar],
                        mode='lines+markers',
                        name=f'{profile_df["profile"].iloc[0]} (raw)',
                        marker=dict(size=4, color='#cccccc'),
                        line=dict(width=1, color='#cccccc')
                    ),
                    row=row_idx,
                    col=col_idx
                )
                
                # Add cleaned data trace with lines
                fig.add_trace(
                    go.Scatter(
                        x=df_cleaned[var],
                        y=df_cleaned[yvar],
                        mode='lines+markers',
                        name=f'{profile_df["profile"].iloc[0]} (cleaned)',
                        marker=dict(size=4, color=profile_color),
                        line=dict(width=1, color=profile_color)
                    ),
                    row=row_idx,
                    col=col_idx
                )
                
                # Update yaxis to be inverted for each subplot
                fig.update_yaxes(autorange="reversed", row=row_idx, col=col_idx)
            
            return fig

        # Initial plot
        plot_pane.object = update_plot(
            var_select.value,
            yaxis_select.value,
            min_val.value, 
            max_val.value,
            rsd_threshold.value
        )

        # Control panel widgets
        controls = pn.Column(
            pn.pane.Markdown("## Data Cleaning Controls"),
            var_select,
            yaxis_select,
            min_val,
            max_val,
            rsd_threshold,
            process_button,
            width=300,
            styles={'background': 'white'},  # Use styles dict instead of background
            margin=(10, 25, 10, 25)  # top, right, bottom, left
        )
        
        # Layout with controls on left, plot on right
        layout = pn.Row(
            controls,
            plot_pane,
            sizing_mode='stretch_width'
        )
        
        return layout

if __name__ == "__main__":
    base_dir = Path.cwd()
    expedition = "sanna"
    l2_dir = base_dir / "data" / "sanna" / "Level2"
    
    plotter = InteractiveProfilePlotter(l2_dir)
    dashboard = plotter.create_interactive_cleaning_plot()
    dashboard.show()