import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Tuple
from .data_model import SubOceanMetadata
import json

class Profile:
    """Handles SubOcean profile data and metadata"""
    def __init__(self, data_path: Path, log_path: Optional[Path] = None):
        self.data_path = Path(data_path)
        self.log_path = Path(log_path) if log_path else None
        self.data: Optional[pd.DataFrame] = None
        self.metadata: Optional[SubOceanMetadata] = None
        
    def load(self) -> Tuple[pd.DataFrame, Optional[SubOceanMetadata]]:
        """Load profile data and metadata"""
        self.data = pd.read_csv(self.data_path, sep='\t')
        
        # Create datetime column while preserving originals
        self.data['datetime'] = pd.to_datetime(
            self.data['Date'] + ' ' + self.data['Time']
        )
        
        if self.log_path and self.log_path.exists():
            with open(self.log_path, 'r') as f:
                metadata_dict = json.load(f)
                self.metadata = SubOceanMetadata.from_dict(metadata_dict)
        
        return self.data, self.metadata