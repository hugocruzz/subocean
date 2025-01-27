import pandas as pd

class CastProcessor:
    """Handle cast direction detection and separation"""
    
    def __init__(self, pressure_column: str = 'Hydrostatic pressure (bar)'):
        self.pressure_column = pressure_column

    def add_cast_direction(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add basic cast direction based on pressure gradient"""
        df = df.copy()
        pressure_grad = df[self.pressure_column].diff()
        df['is_downcast'] = pressure_grad > 0
        return df
        
    def clean_cast_direction(self, pressure_threshold) -> pd.DataFrame:
        """Clean and separate casts based on maximum pressure"""
        # Find maximum pressure point
        max_pressure_idx = self.df[self.pressure_column].idxmax()
        
        # Split into theoretical down and up casts
        downcast = self.df.iloc[:max_pressure_idx + 1].copy()
        upcast = self.df.iloc[max_pressure_idx:].copy()
        
        # Clean pressure transitions
        def clean_pressure_gradient(df: pd.DataFrame, ascending: bool) -> pd.DataFrame:
                pressure_grad = df[self.pressure_column].diff()
                if ascending:
                    return df[pressure_grad >= -pressure_threshold]
                return df[pressure_grad <= pressure_threshold]
        
        # Clean each cast
        downcast_clean = clean_pressure_gradient(downcast, ascending=True)
        upcast_clean = clean_pressure_gradient(upcast, ascending=False)
        
        # Add cast direction
        downcast_clean['is_downcast'] = True
        upcast_clean['is_downcast'] = False
        
        return pd.concat([downcast_clean, upcast_clean])