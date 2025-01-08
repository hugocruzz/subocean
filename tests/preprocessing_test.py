import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'src')
sys.path.append(src_dir)

from preprocessing.cleaner import DataCleaner
from preprocessing.rsd_processor import RSDProcessor
from preprocessing.error_handler import ErrorHandler

@pytest.fixture
def sample_profile_data():
    """Create realistic sample data including all required columns"""
    return pd.DataFrame({
        'datetime': pd.date_range('2024-11-27 12:58:45', periods=10, freq='S'),
        '[CH4] dissolved with water vapour (ppm)': [8.50934, 11.1496, 8.91409, 10.1192, 
                                                   7.99359, 8.55013, 9.12345, 8.76543, 
                                                   10.5432, 9.87654],
        '[H2O] measured (%)': [15.344, 9.730, 16.463, 13.792, 31.144, 17.327, 
                              14.567, 16.789, 15.432, 14.678],
        'Error Standard': [0.0120, 0.0090, 0.0059, 0.0039, 0.0115, 0.0135, 
                          0.0078, 0.0094, 0.0156, 0.0088],
        'Cavity Pressure (mbar)': [30.0469, 30.0469, 29.9375, 29.9531, 30.0469, 
                                  30.0156, 30.1234, 29.8765, 30.0123, 30.0456],
        'Cellule Temperature (Degree Celsius)': [39.699, 39.696, 39.674, 39.694, 
                                               39.704, 39.711, 39.689, 39.701, 
                                               39.695, 39.698],
        'Depth (meter)': [-1.40027, -1.46392, -1.27297, -1.27297, -1.03429,
                         -1.33662, -1.25000, -1.15000, -1.20000, -1.30000]
    })

# Test DataCleaner
def test_h2o_moving_average(sample_profile_data):
    cleaner = DataCleaner(sample_profile_data)
    result = cleaner.clean_h2o_measurements(window=3)
    
    assert '[H2O] measured (%)_ma' in result.columns
    assert not result['[H2O] measured (%)_ma'].equals(sample_profile_data['[H2O] measured (%)'])
    assert len(cleaner.cleaning_log) > 0

def test_measurement_validation(sample_profile_data):
    cleaner = DataCleaner(sample_profile_data)
    result = cleaner.validate_measurements()
    
    # Test that values are within expected ranges
    assert result['Cavity Pressure (mbar)'].between(29.5, 30.5).all()
    assert result['Cellule Temperature (Degree Celsius)'].between(39.5, 40.5).all()
    assert result['Depth (meter)'].between(-2, 11000).all()

# Test RSDProcessor
def test_rsd_calculation(sample_profile_data):
    processor = RSDProcessor(sample_profile_data)
    rsd = processor.calculate_rsd('CH4')
    
    # Manual calculation
    expected = (sample_profile_data['Error Standard']**2) / \
              sample_profile_data['[CH4] dissolved with water vapour (ppm)']
    
    assert np.allclose(rsd, expected)
    assert len(rsd) == len(sample_profile_data)

def test_rsd_threshold_filtering(sample_profile_data):
    processor = RSDProcessor(sample_profile_data)
    threshold = 0.00001
    filtered = processor.filter_by_threshold('CH4', threshold)
    
    assert len(filtered) <= len(sample_profile_data)
    assert all(processor.rsd_results['CH4'][filtered.index] <= threshold)

# Test ErrorHandler
def test_error_standard_processing(sample_profile_data):
    handler = ErrorHandler(sigma_threshold=3.0)
    result = handler.process_error_standard(sample_profile_data)
    
    assert 'Error Standard' in result.columns
    assert result['Error Standard'].isna().sum() >= 0

def test_quality_metrics(sample_profile_data):
    handler = ErrorHandler()
    metrics = handler.get_quality_metrics(sample_profile_data)
    
    assert 'error_std_mean' in metrics
    assert 'error_std_std' in metrics
    assert 'missing_data_pct' in metrics
    assert all(isinstance(v, float) for v in metrics.values())

if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])