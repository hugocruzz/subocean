import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Set interactive backend for standalone script
plt.ion()  # Enable interactive mode

# Add src to path
src_dir = Path.cwd().parent / 'src'
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.profile import Profile
from preprocessing.cleaner import DataCleaner
from preprocessing.rsd_processor import RSDProcessor
from preprocessing.error_handler import ErrorHandler
from gpt_interface.prompt_handler import PromptHandler
from core.executor import Executor

def process_profile(data_path: Path, log_path: Path, output_dir: Path) -> Path:
    """Process SubOcean profile through pipeline"""
    print(f"Processing {data_path.name}")
    
    # 1. Load Data
    profile = Profile(data_path, log_path)
    df, metadata = profile.load()
    print(f"Loaded {len(df)} measurements")
    
    # 2. Clean Data
    cleaner = DataCleaner(df)
    df = cleaner.validate_measurements() #Based on threshold values specified in DataCleaner class, mask outliers
    df = cleaner.clean_h2o_measurements(window=5) #Replace H2o values with moving average values with window=5
    
    # 3. Calculate RSD
    processor = RSDProcessor(df, error_column="Error Standard")
    df = processor.rsd_filter_by_threshold('[CH4] dissolved with water vapour (ppm)', threshold=0.001)#Calculate the rsd of this column 
    
    # 4. Handle Errors
    handler = ErrorHandler(method="zscore")
    df = handler.process_error_standard(df) #Remove outliers based on error standard 
    metrics = handler.get_quality_metrics(df, column="Error Standard") #Normal metrics 
    print("\nQuality Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value:.6f}")
    
    # 5. Export Level 1 Data
    output_path = output_dir / f"L1_{data_path.name}"
    df.to_csv(output_path, index=False)
    print(f"\nSaved Level 1 data to {output_path}")
    
    return output_path

def visualize_profile(data_path: Path):
    """Visualize processed profile using GPT"""
    # Load Level 1 data
    df = pd.read_csv(data_path)
    
    executor = Executor()
    # Setup visualization
    prompt_handler = PromptHandler(df)
    command = "Create a plot with CH4 concentration with depth"
    
    # Generate and execute plot
    code = prompt_handler.generate_plot_code(command)
    print("\nExecuting visualization...")
    print(code)

    # Execute with DataFrame
    error = executor.run(code, df=df)

    if error:
        print(f"Error during execution: {error}")
    else:
        print("Successfully executed")
    plt.show()

if __name__ == "__main__":
    # Setup paths
    base_dir = Path.cwd()
    data_dir = base_dir / "data"
    l0_dir = data_dir / "Level0"
    l1_dir = data_dir / "Level1"
    l1_dir.mkdir(exist_ok=True)
    
    # Process file
    data_path = l0_dir / "SubOceanExperiment2024-11-27T12-58-44.txt"
    log_path = l0_dir / "SubOceanExperiment2024-11-27T12-58-44.log"
    
    l1_path = process_profile(data_path, log_path, l1_dir)
    visualize_profile(l1_path)