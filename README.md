# SubOcean Data Visualization Tool

Interactive visualization system for SubOcean CH4/N2O profiles using GPT-4 for natural language plot generation.

## Features

- Natural language plot commands
- Interactive data visualization
- Real-time data filtering
- Automated data quality checks
- State-aware plot modifications
- Support for multiple data views

## Installation

```bash
# Create environment
conda create -n subocean python=3.9
conda activate subocean

# Install dependencies
pip install -r requirements.txt

# Set up OpenAI API
cp .env.example .env
# Add your OpenAI API key to .env
```
## Project structure 

subocean/
├── src/
│   ├── core/              # Core data processing
│   ├── preprocessing/     # Data cleaning
│   ├── visualization/     # Plot generation
│   └── gpt_interface/    # GPT integration
├── data/
│   └── Level0/           # Raw instrument data
├── tests/                # Unit tests
└── examples/             # Jupyter notebooks


## Usage

### Basic plot generation 
```python

from core.profile import Profile
from gpt_interface.prompt_handler import PromptHandler

# Load data
profile = Profile("data/Level0/SubOceanExperiment.txt")
df, metadata = profile.load()

# Initialize handlers
prompt_handler = PromptHandler(df)

# Generate plot with natural language
command = "Create a depth profile of CH4 concentration"
code = prompt_handler.generate_plot_code(command)
```

## Next Steps
### Pre-processing:
- Implement delay 
- Load multiple profiles
- Add log coordinates to data and make it possible to plot log coordinates (by creating a netcdf/xarray ?)
- Load bathymetry ?

### GPT
- Column recognition for better robustness (CTD profiles etc)
- Implement parallel CTD opening with automated search for close CTD
- Implement real-time data filtering
- Enhance GPT-4 integration for more complex commands