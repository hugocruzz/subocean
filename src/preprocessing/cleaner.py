import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import json
class DataCleaner:
    def __init__(self, df: pd.DataFrame, DEFAULT_VALIDATION_RANGES: Dict[str, Tuple[float, float]]):
        self.df = df.copy()
        self.cleaning_log = []
        self.config_path = Path(__file__).parent.parent / "config" / "column_mappings.json"
        self.DEFAULT_VALIDATION_RANGES = DEFAULT_VALIDATION_RANGES
    def standardize_columns(self):
        """Standardize column names based on mapping config"""
        with open(self.config_path) as f:
            mappings = json.load(f)["column_standardization"]
            
        self.df = self.df.rename(columns=mappings)
        return self.df
    
    def ensure_numeric_columns(self, columns: List[str]) -> pd.DataFrame:
        """Convert columns to numeric type and handle errors"""
        for col in columns:
            if col in self.df.columns:
                try:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                    self.cleaning_log.append(f"Converted {col} to numeric")
                except Exception as e:
                    self.cleaning_log.append(f"Error converting {col}: {str(e)}")
        return self.df
    
    def validate_measurements(self, 
                            validation_ranges: Optional[Dict[str, Tuple[float, float]]] = None
                            ) -> pd.DataFrame:
        """Flag measurements outside validation ranges"""
        conditions = validation_ranges or self.DEFAULT_VALIDATION_RANGES
        
        #self.standardize_columns()  # Add standardization step
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
        
    def calculate_rsd(self, gas_columns: List[str], 
                    error_column: str = 'Error Standard',
                    threshold: float = 0.001) -> pd.DataFrame:
        """Calculate RSD and flag gas measurements while preserving existing flags"""
        for column in gas_columns:
            if column in self.df.columns:
                # Calculate RSD
                rsd = (self.df[error_column]**2) / self.df[column]
                self.df[f"{column}_RSD"] = rsd
                
                # Get existing flag or initialize with zeros if it doesn't exist
                flag_column = f"{column}_FLAG"
                if flag_column not in self.df.columns:
                    self.df[flag_column] = 0
                    
                # Update flag - set to 1 if either existing flag is 1 OR rsd exceeds threshold
                self.df[flag_column] = ((self.df[flag_column] == 1) | (rsd > threshold)).astype(int)
                self.cleaning_log.append(f"Updated RSD and flags for {column}")
        return self.df

    def ensure_numeric_columns(self, columns: List[str]) -> pd.DataFrame:
        """Convert columns to numeric type and handle errors"""
        for col in columns:
            if col in self.df.columns:
                try:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                    self.cleaning_log.append(f"Converted {col} to numeric")
                except Exception as e:
                    self.cleaning_log.append(f"Error converting {col}: {str(e)}")
        return self.df

    def filter_flagged_row(self) -> pd.DataFrame:
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

    def filter_flagged_rows(self, columns_to_check: List[str]) -> pd.DataFrame:
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
        return df_filtered
    
    def process_all(self, gas_columns: List[str], output_path: Path) -> None:
        """Run complete cleaning pipeline"""
        # L1A: Basic validation and RSD flags
        self.validate_measurements()
        self.calculate_rsd(gas_columns)
        print("\n".join(self.cleaning_log))