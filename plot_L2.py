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

        plot_pane = pn.pane.Plotly(sizing_mode='stretch_width', height=800)

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
            
            fig = make_subplots(
                rows=len(self.profiles), cols=1,
                shared_xaxes=True,
                subplot_titles=[df['profile'].iloc[0] for df in self.profiles],
                vertical_spacing=0.1  # Decreased spacing
            )
    
            
            for i, profile_df in enumerate(self.profiles):

                
                cleaner = DataCleaner(profile_df,DEFAULT_VALIDATION_RANGES)
                
                # Apply validation range
                ranges = {var: (min_v, max_v)}
                df_cleaned = cleaner.validate_measurements(ranges)
                
                # Apply RSD cleaning
                df_cleaned = cleaner.calculate_rsd([var], threshold=rsd_thresh)
                
                # Plot original downcast data
                mask_down = profile_df['is_downcast']
                fig.add_trace(
                    go.Scatter(
                        x=profile_df[var][mask_down],
                        y=profile_df[yvar][mask_down],
                        name="Original down",
                        line=dict(color='lightgray'),
                        showlegend=True
                    ),
                    row=i+1, col=1
                )

                # Plot original upcast data
                mask_up = ~profile_df['is_downcast']
                fig.add_trace(
                    go.Scatter(
                        x=profile_df[var][mask_up],
                        y=profile_df[yvar][mask_up],
                        name="Original up",
                        line=dict(color='lightcoral'),
                        showlegend=True
                    ),
                    row=i+1, col=1
                )
                
                # Plot cleaned data - downcast
                mask_valid = ~df_cleaned[f"{var}_FLAG"].astype(bool)
                fig.add_trace(
                    go.Scatter(
                        x=df_cleaned[var][mask_valid & mask_down],
                        y=df_cleaned[yvar][mask_valid & mask_down],
                        name="Cleaned down",
                        line=dict(color=self.colors['down']),
                        showlegend=True
                    ),
                    row=i+1, col=1
                )

                # Plot cleaned data - upcast
                fig.add_trace(
                    go.Scatter(
                        x=df_cleaned[var][mask_valid & mask_up],
                        y=df_cleaned[yvar][mask_valid & mask_up],
                        name="Cleaned up",
                        line=dict(color=self.colors['up']),
                        showlegend=True
                    ),
                    row=i+1, col=1
                )

                # Update axes and legend position for this subplot
                fig.update_xaxes(title_text=var, row=i+1, col=1)
                fig.update_yaxes(title_text=yvar, autorange="reversed", row=i+1, col=1)
            # Update overall layout
            fig.update_layout(
                height=400*len(self.profiles),  # Increased height per subplot
                width=1000,
                showlegend=True,
                legend=dict(
                    xanchor="left",
                    x=1.05,
                    yanchor="top",
                    y=0.99
                )
            )
            
            return fig

        # Initial plot
        plot_pane.object = update_plot(
            var_select.value,
            yaxis_select.value,
            min_val.value, 
            max_val.value,
            rsd_threshold.value
        )

        # Layout with controls in a row
        controls = pn.Column(
            yaxis_select,
            var_select, 
            min_val, 
            max_val, 
            rsd_threshold,
            process_button,
            name='Controls'
        )
        
        return pn.Column(
            controls,
            plot_pane,
            sizing_mode='stretch_width'
        )

if __name__ == "__main__":
    base_dir = Path.cwd()
    l2_dir = base_dir / "data" / "Level2"
    
    plotter = InteractiveProfilePlotter(l2_dir)
    dashboard = plotter.create_interactive_cleaning_plot()
    dashboard.show()