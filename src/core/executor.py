import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from gpt_interface.data_state import DataState
class Executor:
    def run(self, code: str, df=None):
        try:
            # Setup namespace with both original and filtered dataframes
            namespace = {
                'plt': plt,
                'pd': pd,
                'np': np,
                'df': df,
                'filtered_df': df  # Initialize filtered_df with original data
            }
            
            exec(code, namespace)
            
            # Update filtered_df for next execution if it was modified
            if 'filtered_df' in namespace:
                self.filtered_df = namespace['filtered_df']
                
            return None
        except Exception as e:
            return str(e)
        
