# SubOcean Data Visualization Tool

Interactive visualization system for SubOcean CH4/N2O profiles using GPT-4 for natural language plot generation.

## Features

- Natural language plot commands
- Interactive data visualization
- Real-time data filtering
- Automated data quality checks
- State-aware plot modifications
- Support for multiple data views

## Data Processing Pipeline

### Processing Levels

#### Level 0 (Raw Data)
- Raw data from instrument
- Original column names and units

#### Level 1 (Quality Controlled)
##### L1A: Initial Processing
- Column name standardization
- Basic quality control flags
- Unit conversions
- Invalid measurement filtering

##### L1B: Computed Parameters
- Relative Standard Deviation (RSD) for gas measurements
- Time delay corrections
- Moving averages

#### Level 2 (Derived Parameters)
- Dissolved gas concentrations (nmol/L)
  - CH4 dissolved with water vapor
  - N2O dissolved with water vapor
  - NH3 dissolved
- Salinity corrections
- Temperature corrections
- Pressure corrections

#### Level 3 (Gridded Products)
- Pressure-binned data (0.05 bar intervals)
- Separate upcast/downcast profiles
- Interpolated values
- Profile statistics

### Computed Variables

| Variable | Description | Unit | Formula |
|----------|-------------|------|---------|
| RSD_[gas] | Relative standard deviation | % | (Error_Standard²/[gas]_measured) |
| [gas]_dissolved | Dissolved concentration | nmol/L | [gas]_measured * f(P,T,S) |
| Depth | Calculated depth | meters | P/ρg |

### Quality Control Steps
1. Remove invalid measurements (Error_Standard > threshold)
2. Filter extreme values (> 3σ from mean)
3. Apply moving average smoothing
4. Flag suspicious data points

## Column Descriptions

1. **Date**: The date of the measurement (UTC).
2. **Time**: The time of the measurement (UTC).
3. **Date calibrated**: The date when the measurement system was calibrated (UTC).
4. **Time calibrated**: The time when the measurement system was calibrated (UTC).
5. **[CH4] dissolved with water vapour (ppm)**: Methane concentration dissolved with water vapor, measured in parts per million (ppm). With water vapor means the offline CTD collected dissolved Oxygen as mg/L 
or percentage water saturation. The percentage of saturation measured by the CTD is multiplied by 0.21 (21% being the default dissolved oxygen.)
6. **[CH4] dissolved with water vapour (nmol/L)**: Methane concentration dissolved with water vapor, measured in nanomoles per liter (nmol/L).
7. **[CH4] dissolved with constant dry gas flow (ppm)**: Methane concentration dissolved with constant dry gas flow, measured in ppm.
8. **[CH4] dissolved with constant dry gas flow (nmol/L)**: Methane concentration dissolved with constant dry gas flow, measured in nmol/L.
9. **[N2O] dissolved with water vapour (ppm)**: Nitrous oxide concentration dissolved with water vapor, measured in ppm.
10. **[N2O] dissolved with water vapour (nmol/L)**: Nitrous oxide concentration dissolved with water vapor, measured in nmol/L.
11. **[N2O] dissolved with constant dry gas flow (ppm)**: Nitrous oxide concentration dissolved with constant dry gas flow, measured in ppm.
12. **[N2O] dissolved with constant dry gas flow (nmol/L)**: Nitrous oxide concentration dissolved with constant dry gas flow, measured in nmol/L.
13. **[NH3] dissolved (ppm)**: Ammonia concentration dissolved, measured in ppm.
14. **Depth (meter)**: Depth of measurement in meters, calculated from hydrostatic pressure considering latitude.
15. **Hydrostatic Pressure Calibrated (bar)**: Hydrostatic pressure, calibrated and measured in bars.
16. **Carrier gas pressure calibrated (bar)**: Carrier gas pressure, calibrated and measured in bars.
17. **[CH4] measured (ppm)**: Methane concentration measured directly, in ppm. 
18. **[N2O] measured (ppm)**: Nitrous oxide concentration measured directly, in ppm.
19. **[NH3] measured (ppm)**: Ammonia concentration measured directly, in ppm.
20. **[H2O] measured (%)**: Water vapor concentration, measured in percentage (%).
21. **Flow Carrier Gas (sccm)**: Carrier gas flow, measured in standard cubic centimeters per minute (sccm).
22. **Total Flow (sccm)**: Total gas flow, measured in sccm, including water vapor and dissolved gases.
23. **Cavity Pressure (mbar)**: Pressure within the cavity, set at 30 mbar.
24. **Cellule Temperature (Degree Celsius)**: Temperature within the cavity, set at 40°C.
25. **Hydrostatic pressure (bar)**: Hydrostatic pressure measured during the run, in bars.
26. **LShift**: Variable related to spectral fit quality. Use in combination with Error Standard for cleaning datasets.
27. **Error Standard**: Indicator of spectral fit quality. Lower values indicate better fits.
28. **Ringdown Time (microSec)**: Laser spectrometer performance indicator. ~13 µs for SubOcean-CH4, ~26 µs for SubOcean-N2O.
29. **Box Temperature (Degree Celsius)**: Internal temperature of the pressure tube. Stabilizes over time after immersion. should be around 40°C, might take 1h to stabilize.
30. **Carrier gas pressure (dbar)**: Pressure of carrier gas in the tank, measured in decibars (dbar). This value is to be checked on the field to know if everything is going well.
31. **PWM Cellule Temperature**: Not clearly defined. Temperature of the cellule as part of the PWM system.
32. **PWM Cellule Pressure**: Not clearly defined. Pressure within the cellule as part of the PWM system.
33. **Laser Temperature (Degree Celsius)**: Laser temperature, typically constant.
34. **Laser Flux**: Laser flux, typically constant.
35. **Norm Signal**: Not clearly defined.
36. **Value Max**: Not clearly defined.
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
- Add log coordinates to data and make it possible to plot log coordinates (by creating a netcdf/xarray ?)
- Load bathymetry ?


### GPT
- Column recognition for better robustness (CTD profiles etc)
- Implement parallel CTD opening with automated search for close CTD
- Implement real-time data filtering
- Enhance GPT-4 integration for more complex commands

Ideas : You are a scientist that has 2 instruments a ctd profiler and another profiler that we will call subocean. 
You want to be able to plot and be able to compare those two profiles. 
For that you have a folder with the subocean profiles, and another folder with ctd profiles. 
You want to create a script that will take as input a question like : "Give me 

TODO:
 Plot chaque profiles: 
    - Check chaque profiles si up and down pareil 
    - Couleurs differentes up et down 
    •	Allow to compare the resulting SubOcean concentration profiles using constant values for T, S and O2, with those obtained from the CTD data, in order to evaluate their effect.
Questions for Jerome/A2PS:
   - equation of the time delay

## Notes:
m_eff=(1.9774+(0.0385-0.00316*Salinity(psu))*(WaterTemperature(°C)-2.67))*(1+0.2286*(O2diss(%)-0.2)/(0-0.2))

## Fieldwork
- Turn on the spectrometer 1h before the first measurement (during transportation) to reach 40°C for the box temperature
- IF deployed vertically, the signal might appear noisy on the first meters. Need to be tested in the lab.
- Check the fit to know if need to recover signal 