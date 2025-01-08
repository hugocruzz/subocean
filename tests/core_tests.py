import pytest
from pathlib import Path
import pandas as pd
from datetime import datetime
import sys
import os

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), 'src')
sys.path.append(src_dir)

from core.data_model import SubOceanMetadata
from core.profile import Profile

@pytest.fixture
def sample_metadata_dict():
    return {
        "Concentration coefficient calibration 1": "0.123",
        "Concentration coefficient calibration 2": "27.141",
        "Title of the experiment": "SubOceanExperiment2024-11-27T12-58-44",
        "Start time": "2024-11-27 12:58:44",
        "End time": "2024-11-27 13:45:20",
        "Hydrostatic Pressure coefficient 1": "400",
        "Hydrostatic Pressure coefficient 2": "0",
        "Latitude": "0",
        "Type of gas": True
    }

@pytest.fixture
def sample_profile_data():
    return pd.DataFrame({
        'Date': ['2024/11/27'] * 6,
        'Time': [f'12:58:{i}' for i in range(45, 51)],
        '[CH4] dissolved with water vapour (ppm)': [8.50934, 11.1496, 8.91409, 
                                                   10.1192, 7.99359, 8.55013],
        'Error Standard': [0.0120, 0.0090, 0.0059, 0.0039, 0.0115, 0.0135]
    })

def test_metadata_loading(sample_metadata_dict):
    metadata = SubOceanMetadata.from_dict(sample_metadata_dict)
    assert metadata.concentration_cal1 == 0.123
    assert metadata.gas_type is True

def test_profile_loading(sample_profile_data, tmp_path):
    # Save sample data to temporary file
    data_path = tmp_path / "test_profile.txt"
    sample_profile_data.to_csv(data_path, sep='\t', index=False)
    
    # Create profile instance and load data
    profile = Profile(data_path)
    data, _ = profile.load()
    
    assert len(data) == len(sample_profile_data)
    assert '[CH4] dissolved with water vapour (ppm)' in data.columns

if __name__ == "__main__":
    # Run tests with pytest
    import pytest
    # -v for verbose output
    # -s to show print statements
    # --tb=short for shorter tracebacks
    pytest.main([__file__, '-v', '-s', '--tb=short'])