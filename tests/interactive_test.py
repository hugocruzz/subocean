import pytest
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.testing.decorators import cleanup
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'src')
sys.path.append(src_dir)

from visualization.interactive import InteractivePlot

@pytest.fixture
def sample_data():
    return pd.DataFrame({
        'datetime': pd.date_range('2024-11-27 12:58:45', periods=10, freq='S'),
        'Depth (meter)': [-1.40027, -1.46392, -1.27297, -1.27297, -1.03429,
                         -1.33662, -1.25000, -1.15000, -1.20000, -1.30000],
        '[CH4] dissolved with water vapour (ppm)': [8.50934, 11.1496, 8.91409, 
                                                   10.1192, 7.99359, 8.55013,
                                                   9.12345, 8.76543, 10.5432, 9.87654]
    })

@cleanup
def test_interactive_plot_creation(sample_data):
    plotter = InteractivePlot(sample_data)
    fig = plotter.create_interactive_profile(
        x_columns=['[CH4] dissolved with water vapour (ppm)']
    )
    assert fig is not None
    assert plotter.ax is not None
    assert plotter.reset_button is not None
    assert plotter.depth_slider is not None
    plt.close(fig)

def test_axis_inversion(sample_data):
    plotter = InteractivePlot(sample_data)
    plotter.create_interactive_profile(
        x_columns=['[CH4] dissolved with water vapour (ppm)']
    )
    
    # Test y-axis inversion
    plotter.invert_axis('y')
    assert plotter.axis_states['y'] is True
    
    # Test reset
    plotter.reset_view()
    assert not plotter.ax.yaxis_inverted()
    
if __name__ == "__main__":
    # Run tests with pytest
    import pytest
    # -v for verbose output
    # -s to show print statements
    # --tb=short for shorter tracebacks
    pytest.main([__file__, '-v', '-s', '--tb=short'])
