import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import json

class DataCleaner:
    def __init__(self, df, validation_ranges=None):
        self.df = df
        self.DEFAULT_VALIDATION_RANGES = validation_ranges
        self.cleaning_log = []

    def ensure_numeric_columns(self, columns):
        """Convert columns to numeric type and handle errors"""
        for col in columns:
            if col in self.df.columns:
                try:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                    self.cleaning_log.append(f"Converted {col} to numeric")
                except Exception as e:
                    self.cleaning_log.append(f"Error converting {col}: {str(e)}")
        return self.df

    def apply_validation_rules(self, validation_rules):
        """
        Apply combined filtering based on absolute ranges and RSD thresholds.
        
        Args:
            validation_rules (dict): Dictionary containing range and RSD thresholds for each gas
        Returns:
            pd.DataFrame: DataFrame with added flag columns
        """
        for gas, rules in validation_rules.items():
            if gas in self.df.columns:
                # Create masks for both conditions
                valid_range = (self.df[gas] >= rules['range'][0]) & (self.df[gas] <= rules['range'][1])
                valid_rsd = abs(self.df[f"{gas}_RSD"]) <= rules['rsd_threshold']
                
                # Combine masks and create flag column (1 = invalid, 0 = valid)
                self.df[f"{gas}_FLAG"] = (~(valid_range & valid_rsd)).astype(int)
        
        return self.df

    def validate_measurements(self, validation_ranges=None):
        """Flag measurements outside validation ranges"""
        conditions = validation_ranges or self.DEFAULT_VALIDATION_RANGES
        
        # Convert all columns to numeric first
        numeric_columns = list(conditions.keys())
        self.ensure_numeric_columns(numeric_columns)
        
        for column, (min_val, max_val) in conditions.items():
            if column in self.df.columns:
                mask = (self.df[column] >= min_val) & (self.df[column] <= max_val)
                self.df[f"{column}_FLAG"] = (~mask | self.df[column].isna()).astype(int)
                self.cleaning_log.append(
                    f"Flagged {column} outside [{min_val}, {max_val}]"
                )
        return self.df

    def calculate_rsd(self, gas_columns):
        """Calculate RSD and flag gas measurements while preserving existing flags"""
        for column in gas_columns:
            if column in self.df.columns:
                # Calculate RSD
                rsd = (self.df['Error Standard']**2) / self.df[column]
                self.df[f"{column}_RSD"] = rsd
                self.cleaning_log.append(f"Updated RSD for {column}")
        return self.df

    def filter_flagged_row(self):
        """Create filtered DataFrame by setting flagged values to NaN"""
        df_filtered = self.df.copy()
        
        # Get all flag columns
        flag_columns = [col for col in self.df.columns if col.endswith('_FLAG')]
        
        # Apply flags
        for flag_col in flag_columns:
            base_col = flag_col.replace('_FLAG', '')
            if base_col in df_filtered.columns:
                df_filtered.loc[df_filtered[flag_col] == 1, base_col] = np.nan
        self.df = df_filtered
        return self.df 

    def filter_flagged_rows(self, columns_to_check):
        """Create filtered DataFrame by setting rows to NaN based on specified column flags
        
        Args:
            columns_to_check: List of base column names to check flags
            
        Returns:
            DataFrame with NaN values where specified flags are raised
        """
        df_filtered = self.df.copy()
        
        # Get relevant flag columns
        flag_columns = [f"{col}_FLAG" for col in columns_to_check 
                    if f"{col}_FLAG" in self.df.columns]
        
        # Create mask where any specified flag is 1
        mask = df_filtered[flag_columns].eq(1).any(axis=1)
        
        # Set all columns to NaN where mask is True
        df_filtered.loc[mask, :] = np.nan
        self.df = df_filtered
        return self.df

    def process_all(self, gas_columns: List[str], output_path: Path) -> None:
        """Run complete cleaning pipeline"""
        # L1A: Basic validation and RSD flags
        self.validate_measurements()
        self.calculate_rsd(gas_columns)
        print("\n".join(self.cleaning_log))

    def validate_data(self, validation_config: Dict) -> pd.DataFrame:
        """
        Unified validation system for all measurements
        
        Args:
            validation_config: {
                'standard_ranges': {
                    'column': (min, max)
                },
                'gas_rules': {
                    'gas_name': {
                        'range': (min, max),
                        'rsd_threshold': float
                    }
                }
            }
        """
        """Flag measurements outside validation ranges"""
        conditions = validation_config['standard_ranges'] or self.DEFAULT_VALIDATION_RANGES
        
        # Convert all columns to numeric first
        numeric_columns = list(conditions.keys())
        self.ensure_numeric_columns(numeric_columns)
        # First validate standard measurements
        for column, (min_val, max_val) in validation_config['standard_ranges'].items():
            if column in self.df.columns:
                mask = (self.df[column] >= min_val) & (self.df[column] <= max_val)
                self.df[f"{column}_FLAG"] = (~mask | self.df[column].isna()).astype(int)
                
        # Then handle gas measurements with RSD
        for gas, rules in validation_config['gas_rules'].items():
            if gas in self.df.columns:
                valid_range = (self.df[gas] >= rules['range'][0]) & (self.df[gas] <= rules['range'][1])
                valid_rsd = abs(self.df[f"{gas}_RSD"]) <= rules['rsd_threshold']
                self.df[f"{gas}_FLAG"] = (~(valid_range & valid_rsd)).astype(int)
                
        return self.df