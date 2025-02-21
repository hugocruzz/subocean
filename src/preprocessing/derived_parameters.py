import pandas as pd
import numpy as np
from typing import List, Dict, Optional

class DerivedParameters:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.calculation_log = []
        self.pressure_column = 'Hydrostatic pressure (bar)'

    def add_cast_direction(self) -> pd.DataFrame:
        """Add basic cast direction based on pressure gradient"""
        if 'is_downcast' not in self.df.columns:
            pressure_grad = self.df[self.pressure_column].diff()
            self.df['is_downcast'] = pressure_grad > 0
            self.calculation_log.append("Added cast direction")
        return self.df

    def clean_cast_direction(self, pressure_threshold: float = 0.01) -> pd.DataFrame:
        """Clean and separate casts based on maximum pressure"""
        max_pressure_idx = self.df[self.pressure_column].idxmax()
        
        # Split into down/up casts
        downcast = self.df.iloc[:max_pressure_idx + 1].copy()
        upcast = self.df.iloc[max_pressure_idx:].copy()
        
        # Clean transitions
        pressure_grad_down = downcast[self.pressure_column].diff()
        pressure_grad_up = upcast[self.pressure_column].diff()
        
        downcast = downcast[pressure_grad_down >= -pressure_threshold]
        upcast = upcast[pressure_grad_up <= pressure_threshold]
        
        # Label casts
        downcast['is_downcast'] = True
        upcast['is_downcast'] = False
        
        self.df = pd.concat([downcast, upcast])
        self.calculation_log.append("Cleaned cast direction")
        return self.df
    
    def apply_time_delay_correction(self, 
                                  columns: List[str], 
                                  time_delay: float = 20.0) -> pd.DataFrame:
        """
        Apply time delay correction to gas measurements.
        
        Args:
            columns: List of gas measurement columns to correct
            time_delay: Time delay in seconds based on carrier gas flow
            
        Returns:
            DataFrame with corrected gas measurements
        """
        if 'datetime' not in self.df.columns:
            self.calculation_log.append("Skipped time delay - missing datetime column")
            return self.df

        # Calculate sampling frequency using datetime column
        time_diff = self.df['datetime'].diff().median()
        sampling_freq = 1 / time_diff.total_seconds()
    
        shift_periods = int(time_delay * sampling_freq)
        
        # Apply shift to each gas column
        for column in columns:
            if column in self.df.columns:
                # Shift measurements forward by delay period
                self.df[column] = self.df[column].shift(-shift_periods).fillna(method='ffill')
                
                self.calculation_log.append(
                    f"Applied {time_delay:.1f}s delay correction to {column}")
            else:
                self.calculation_log.append(f"Skipped {column} - column not found")
                
        return self.df
    
    def apply_moving_average(self, column: str, window: int = 5) -> pd.DataFrame:
        """Apply moving average to specific column"""
        self.df[f"{column}_no_moving_average"] = self.df[column]
        self.df[f"{column}"] = self.df[column].rolling(
            window=window, center=True).mean()
        self.calculation_log.append(f"Applied {window}-point moving average to {column}")
        return self.df
        

    def has_required_columns(self, columns: List[str]) -> bool:
        """Check if all required columns exist"""
        return all(col in self.df.columns for col in columns)

    def calculate_flows(self) -> pd.DataFrame:
        """Calculate flow parameters with safety checks"""
        required_cols = ['Total Flow (sccm)', 'Flow Carrier Gas (sccm)', '[H2O] measured (%)']
        
        if self.has_required_columns(required_cols):
            self.df['Dry gas Flow [sccm]'] = (
                self.df['Total Flow (sccm)'] - 
                self.df['Flow Carrier Gas (sccm)'] - 
                self.df['Total Flow (sccm)'] * self.df['[H2O] measured (%)'] / 100
            )
            
            self.df['Water_vapour flow [sccm]'] = (
                self.df['Total Flow (sccm)'] * 
                self.df['[H2O] measured (%)'] / 100
            )
            self.calculation_log.append("Calculated flow parameters")
        else:
            self.calculation_log.append("Skipped flow calculations - missing columns")
        
        return self.df
    
    def calculate_gas_corrections(self) -> pd.DataFrame:
        """Apply temperature corrections with safety checks"""
        # CH4 correction
        ch4_cols = ['[CH4] dissolved with water vapour (ppm)', 'Cellule Temperature (Degree Celsius)']
        if self.has_required_columns(ch4_cols):
            self.df["[CH4] dissolved with water vapour (ppm) corrected Tcell"] = (
                self.df["[CH4] dissolved with water vapour (ppm)"] /
                (0.925*(self.df['Cellule Temperature (Degree Celsius)']-40)/100+1)
            )
            self.df["[CH4] dissolved with water vapour (nmol/L) corrected Tcell"] = (
                self.df["[CH4] dissolved with water vapour (ppm)"] /
                (0.925*(self.df['Cellule Temperature (Degree Celsius)']-40)/100+1)
            )
            self.calculation_log.append("Applied CH4 temperature correction")
        else:
            self.calculation_log.append("Skipped CH4 correction - missing columns")
            
        # H2O correction
        h2o_cols = ['[H2O] measured (%)', 'Cellule Temperature (Degree Celsius)']
        if self.has_required_columns(h2o_cols):
            self.df['[H2O] measured corrected Tcell'] = (
                 self.df['[H2O] measured (%)']/100 /
                (2.469*(self.df['Cellule Temperature (Degree Celsius)']-40)/100+1)
            )
            self.calculation_log.append("Applied H2O temperature correction")
            
        else:
            self.calculation_log.append("Skipped H2O correction - missing columns")
        #Add correction on total gas flow 
        self.df["Total Flow (sccm) corrected Tcell"] = self.df['Dry gas Flow [sccm]'] + self.df['[H2O] measured corrected Tcell']+self.df['Flow Carrier Gas (sccm)']
        return self.df

    def calculate_all(self) -> pd.DataFrame:
        """Run all calculations in correct order"""
        
        # First add cast direction
        self.clean_cast_direction(pressure_threshold=0.03)
        
        # Rest of processing
        self.apply_moving_average('[H2O] measured (%)', 10)
        self.calculate_flows()
        #Comment gas_correction because need to check with emeline if already corrected. 
        #self.calculate_gas_corrections()
        return self.df

