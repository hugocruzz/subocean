import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, List, Dict, Tuple
from pathlib import Path

class PlotManager:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.fig = None
        self.ax = None
    
    def create_profile_plot(self, 
                          y_column: str = 'Depth (meter)',
                          x_columns: List[str] = None,
                          title: str = None,
                          figsize: Tuple[int, int] = (10, 8)) -> None:
        """Create depth profile plot"""
        self.fig, self.ax = plt.subplots(figsize=figsize)
        
        for col in x_columns:
            self.ax.plot(self.df[col], self.df[y_column], 
                        label=col, marker='.')
        
        self.ax.set_ylabel('Depth (m)')
        self.ax.invert_yaxis()  # Depth increases downward
        self.ax.grid(True)
        if title:
            self.ax.set_title(title)
        self.ax.legend()
    
    def create_time_series(self, 
                          columns: List[str],
                          title: str = None,
                          figsize: Tuple[int, int] = (12, 6)) -> None:
        """Create time series plot"""
        self.fig, self.ax = plt.subplots(figsize=figsize)
        
        for col in columns:
            self.ax.plot(self.df['datetime'], self.df[col], 
                        label=col, marker='.')
        
        self.ax.set_xlabel('Time')
        self.ax.grid(True)
        if title:
            self.ax.set_title(title)
        self.ax.legend()
    
    def save_plot(self, filepath: Path) -> None:
        """Save current plot to file"""
        if self.fig:
            self.fig.savefig(filepath)