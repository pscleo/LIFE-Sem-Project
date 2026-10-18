# Station-Keeping Analysis for the Large Interferometer For Exoplanets (LIFE) mission

Analysis suite for simulating and evaluating satellite constellation designs at the Sun-Earth L2 point, with focus on station-keeping maneuver requirements and orbital stability.

Built as part of a semester thesis "Orbit simulation of a satellite
constellation in an L2 halo orbit" by Maximilian Leeb

## Project Overview

This codebase simulates octahedron-shaped satellite constellations at L2 with multiple station-keeping (SK) intervals, analyzing:
- **Delta-V requirements** for maintaining constellation geometry
- **Orbital deviations** from intended formation offsets
- **Trade-offs** between SK frequency and fuel consumption
- **Performance characteristics** across 0.5-hour to 28-day SK intervals

## Quick Start

### Prerequisites

- **STK 13+** with Python API installed (check STK programming help for installation)
- **Python 3.8+** with packages: pandas, numpy, matplotlib, pathlib
- **JPL Horizons ephemeris data** (if needed, automatic download or manual file)

### Setup Python Environment

A `requirements.txt` file is provided to easily recreate the Python virtual environment with all necessary dependencies.

**For new installations:**
```powershell
# Create and activate virtual environment
python -m venv SA-venv
.\SA-venv\Scripts\Activate.ps1

# Install all packages
pip install -r requirements.txt
```

**Important: STK Python API Special Case**

The `requirements.txt` includes a local path to the STK Python API (`agi.stk13`). When installing on a new machine, you may encounter:
```
ERROR: Could not find a local package with the name agi.stk13
```

**If this happens, follow these steps:**

1. **Check your STK installation path:**
   - Default: `C:/Program Files/AGI/STK_ODTK 13/bin/AgPythonAPI/`
   - Verify the `agi_stk13-*.whl` file exists in this directory

2. **If STK is installed in a different location:**
   - Open `requirements.txt` 
   - Replace the file path in the first line with your actual STK installation path:
     ```
     agi.stk13 @ file:///C:/Your/Custom/Path/AGI/STK_ODTK 13/bin/AgPythonAPI/agi_stk13-13.0.0-py3-none-any.whl
     ```

3. **If installation still fails:**
   - Edit `requirements.txt` to comment out the STK line, install the rest, then install STK separately (refer to https://help.agi.com/stkdevkit/index.htm#python/pythonGettingStarted.htm)

### The Three-Step Workflow

```
Step 1: Prepare ephemeris data
   └─→ horizon_csv-to-STK_e.py (convert Horizons CSV to STK format)

Step 2: Run constellation simulations (THIS IS THE MAIN SCRIPT)
   └─→ octahedron-constellation.py (60+ satellites, 10 SK intervals)

Step 3: Analyze and visualize results
   └─→ analysis-SK-duration.py (Delta-V, deviations, correlations)
```

---

## Step 1: Prepare Ephemeris Data

### `horizon_csv-to-STK_e.py`

**Purpose:** Convert JPL Horizons CSV output to STK Ephemeris (.e) format

**When you need this:**
- First-time setup or refreshing JWST ephemeris data
- Using a different celestial object (not included by default)

**How to use:**

1. Download data from [JPL Horizons](https://ssd.jpl.nasa.gov/horizons/app.html)
   - Ephemeris Type: **Vector Table**
   - Coordinate Center: **Geocentric** (code 500)
   - Output Format: **CSV**
   - Quantities: **State vectors** (x, y, z, vx, vy, vz)
   - Time step: 1 hour recommended

2. Run the converter:
```bash
python horizon_csv-to-STK_e.py input_horizons.csv output_horizons.e
```

3. Place output file in `horizon-to-STK/data/`

**Example output:**
The script generates STK-compatible ephemeris files with interpolation parameters for smooth orbital propagation.

---

## Step 2: Run Constellation Simulations (MAIN SCRIPT)

### `octahedron-constellation.py`

**Purpose:** Comprehensive production simulation of octahedron satellite constellations at L2

**This is the core script that:**
- ✓ Creates 61 satellites (1 Base + 10 constellations × 6 satellites)
- ✓ Runs 10 different station-keeping intervals (SK0.5h through SK28d)
- ✓ Optimizes differential correction sequences for orbit maintenance
- ✓ Exports maneuver summaries and position tracking data
- ✓ Generates CSV files for downstream analysis

**Constellation structure:**
Each octahedron has 6 satellites positioned at ±1000m on coordinate axes:
```
Satellite X+: (+1000m, 0m, 0m)
Satellite X-: (-1000m, 0m, 0m)
Satellite Y+: (0m, +1000m, 0m)
Satellite Y-: (0m, -1000m, 0m)
Satellite Z+: (0m, 0m, +1000m)
Satellite Z-: (0m, 0m, -1000m)
```

**Station-keeping intervals:**
- **SK0.5h**: 30 minutes (frequent, high fuel)
- **SK1h**: 1 hour
- **SK3h**: 3 hours
- **SK6h**: 6 hours
- **SK12h**: 12 hours
- **SK1d**: 1 day
- **SK3d**: 3 days
- **SK7d**: 7 days (default reference)
- **SK14d**: 14 days
- **SK28d**: 28 days (infrequent, low fuel)

**How to run:**

1. Ensure JWST ephemeris file exists in `horizon-to-STK/data/`
2. Open in Jupyter or Python REPL
3. Run cell-by-cell or execute full script
4. Full execution: **2-4 hours** (depends on system performance)

**Configuration:**
Edit `CONSTELLATION_CONFIGS` list (lines 186-337) to:
- Add/remove SK intervals
- Change satellite counts or offsets
- Adjust separation delays

**Output generated:**
```
data-export/
├── maneuver-summaries/
│   └── Octahedron_SK*.csv    (Delta-V data per maneuver)
├── positions/
│   └── Octahedron_SK*.csv    (Orbital positions, 10-min intervals)
└── temp/
    └── position/             (intermediate export files)
```

**Helper modules used:**
- `helpers/add_satellites.py` - Satellite creation and optimization
- `helpers/scenario_setup.py` - STK scenario initialization
- `helpers/analysis.py` - Report generation and data parsing

---

## Step 3: Analyze & Visualize Results

### `analysis-SK-duration.py`

**Purpose:** Comprehensive data analysis and visualization of constellation performance

**Key analyses:**

1. **Delta-V Analysis**
   - Total Delta-V per constellation vs SK interval
   - Validates header data against calculated sums
   - Logarithmic plotting for multi-scale data

2. **Position Deviation Analysis**
   - Maximum deviations from intended formation offsets
   - Per-axis (X, Y, Z) and magnitude deviations
   - Identifies outliers and anomalies

3. **Time-series Tracking**
   - Orbital deviations over simulation duration
   - Oscillation patterns and trends
   - Correlation with maneuver timing

4. **Correlation Studies**
   - Relationship between Delta-V and position deviations
   - Optimal SK interval identification
   - Trade-off analysis

**How to use:**

```python
# Run complete analysis
analyze_octahedron_constellations()

# Calculate deviations
satellite_data = calculate_max_deviations()

# Plot Delta-V (with exclusions for problematic data)
plot_delta_v_vs_sk_duration(exclude_names=['SK3d', 'SK1h_Y*'], y_log=True)

# Plot position deviations
plot_max_deviations(satellite_data, x_log=True, y_log=True)

# Time-series analysis
plot_deviations_over_time("Xp1000m", sk_interval="SK7d", x_axis_days=True)

# Correlation scatter
plot_delta_v_vs_max_deviation(satellite_data, x_log=True, y_log=True)
```

**Output generated:**
```
results/
├── delta_v_vs_sk_duration*.png        (Delta-V trends)
├── position_deviations_vs_sk*.png     (2×2 axis grid)
├── magnitude_deviation_vs_sk*.png     (Summary view)
├── deviations_vs_*.png                (Time-series)
└── delta_v_vs_max_deviation*.png      (Correlation)
```

**Known data issues (automatically excluded):**
- `SK3d_*`: Display noise (excessive vibrations)
- `SK1d_Xm, SK1d_Zm`: Oscillation anomaly ~day 170
- `SK1h_Y*, SK1h_Z*`: Optimization failure (diverging deviations)
- `SK0p5h_*`: Some incomplete simulations

---

## Attitude Control Sample

The `attitude-control/` folder contains a sample for attitude control analysis provided by CADFEM. This is reference material for studying rotational dynamics and control strategies for the satellite constellation. Using this control model increases the simulation complexity and time by several orders of magnitude.

---

## Additional Tools

### Helper Modules (`helpers/`)

#### `add_satellites.py`
Creates and configures satellites in STK with Astrogator sequences
- Satellite ephemeris loading
- Differential correction setup
- Position-hold station-keeping sequences
- Propagator configuration

#### `scenario_setup.py`
Initializes STK scenario environment
- L2 coordinate system creation
- Time management and epoch conversions
- Cartesian component setup
- Visualization configuration

#### `analysis.py`
Exports and processes STK simulation data
- Maneuver summary report generation
- Position data CSV conversion
- Outlier detection and cleaning
- Metadata preservation

### Utility Scripts (`automation/`)

#### `rotation-dv-estimate.py`
Theoretical Delta-V calculations for circular orbits in microgravity
- Validates simulation results against physics
- Helps identify unexpected behavior

#### `rename_octahedron_files.py`
One-time utility for file reorganization
- Converts old naming scheme to current standard
- Safe to run (non-destructive)

#### `collection-of-utility-commands.py`
Reference snippets for STK operations
- Copy-paste code examples
- Color definitions, visualization commands
- Useful for interactive development

---

## STK-Connect Folder: Manual Analysis Tools

**Note:** The `STK-connect/` folder contains **manual analysis scripts** for visualization and exploration. These scripts:

- ✓ **Do NOT** actively control STK or run simulations
- ✓ **Do** load and visualize pre-generated data
- ✗ **Are not** part of the main production workflow
- ✗ **Should not** be used for generating new simulation data

**Contents:**
- `plot_2-sat-constellation_refactored.py` - 2-satellite comparison visualizations
- `plot_maneuver_comparison_refactored.py` - Maneuver analysis plots
- `helpers/` - Coordinate transforms, data processing utilities
- `archive/` - Legacy implementations (reference only)

**When to use STK-connect:**
- Interactive exploration of results
- Custom visualization development
- Understanding data formats
- Testing visualization concepts

---

## STK Scenarios

The `STK-scenarios/` folder contains pre-configured STK scenario files for both production simulations and validation studies.

### Primary Scenario: Octahedron-Constellation/

**File:** `Cube-Constellation/OctahedronConstellationScenario.sc`

This is the **main production scenario** created by [octahedron-constellation.py](automation/octahedron-constellation.py). It contains:
- All 61 satellites (1 Base + 10 constellations × 6 satellites)
- 10 different station-keeping interval configurations (SK0.5h through SK28d)
- Optimized trajectories and propagated orbits for all satellites
- Complete mission sequences and maneuver definitions

**Status:** Most trajectories have been fully optimized and propagated, with the exceptions noted in [analysis-SK-duration.py](automation/analysis-SK-duration.py) (see "Known data issues" section).

**Supporting files:** All `.sa`, `.sa3`, `.sae`, `.sax`, and `.txt` files in this directory are required to fully recreate and reopen this scenario as it was saved.

### Validation Scenario: L2Test2/

**File:** `L2Test2/L2_2-sat-constellation.sc`

This scenario is used for:
- **Validation of STK setup** and coordinate system implementations
- **Analysis of perturbations** in the L2 orbit
- **Testing of differential correction** sequences
- Baseline comparisons for constellation algorithms

**Contents:** Simplified 2-satellite constellation for controlled testing and perturbation analysis.

**Supporting files:** All associated files in this directory (`.sa`, `.sa3`, etc.) support scenario recreation.

### Scenario File Notes

- **Primary purpose:** These scenarios are meant to be opened and explored in STK for visualization and analysis
- **Regeneration:** Running [octahedron-constellation.py](automation/octahedron-constellation.py) will regenerate/update the main Cube-Constellation scenario
- **Data export:** The octahedron scenario has associated CSV exports in `automation/data-export/` for analysis
- **File formats:**
  - `.sc`  - Main scenario file (open this in STK)
  - `.sa`  - STK file
  - `.sa3` - STK file
  - `.sae` - STK file
  - `.sax` - STK file
  - `.txt` - STK file

---

## Project Structure

```
code/
├── README.md                          (this file)
├── SA.code-workspace                  (VS Code workspace config)
│
├── automation/                        (MAIN ANALYSIS WORKFLOW)
│   ├── octahedron-constellation.py   ⭐ PRIMARY SCRIPT
│   ├── analysis-SK-duration.py       ⭐ ANALYSIS & PLOTS
│   ├── horizon_csv-to-STK_e.py       ⭐ DATA PREPARATION
│   ├── rotation-dv-estimate.py       (theoretical validation)
│   ├── collection-of-utility-commands.py (reference snippets)
│   ├── rename_octahedron_files.py    (one-time utility)
│   │
│   ├── helpers/                      (core modules)
│   │   ├── add_satellites.py
│   │   ├── scenario_setup.py
│   │   ├── analysis.py
│   │   ├── Maneuver-Summary-Detailed.rst
│   │   └── __pycache__/
│   │
│   ├── data-export/                  (generated data)
│   │   ├── maneuver-summaries/       (Delta-V CSV files)
│   │   ├── positions/                (Position tracking CSV)
│   │   └── temp/                     (intermediate files)
│   │
│   ├── results/                      (generated plots)
│   │   └── *.png files
│   │
│   └── archive/                      (legacy scripts)
│       ├── first-steps.py
│       ├── pyramid-constellation.py
│       └── refactoring.py
│
├── horizon-to-STK/                   (ephemeris conversion)
│   ├── horizon_csv-to-STK_e.py      ⭐ CONVERTER SCRIPT
│   └── data/                         (Horizons input/output)
│       ├── *.txt (Horizons CSV)
│       └── *.e (STK ephemeris)
│
├── STK-connect/                      (manual analysis - no active STK control)
│   ├── plot_2-sat-constellation_refactored.py
│   ├── plot_maneuver_comparison_refactored.py
│   ├── helpers/
│   ├── archive/
│   ├── exported_data/
│   ├── plots/
│   └── old_files/
│
├── STK-programming-help/             (reference documentation)
│   ├── STK Object Model_Python Code Snippets.txt
│   ├── Code Samples/
│   ├── Library Reference/
│   └── STK Python API/
│
├── STK-scenarios/                    (STK scenario files)
│   ├── Cube-Constellation/
│   │   └── OctahedronConstellationScenario.sc    ⭐ MAIN PRODUCTION SCENARIO
│   └── L2Test2/
│       └── L2_2-sat-constellation.sc    (validation & perturbation analysis)
│
└── SA-venv/                          (Python virtual environment)
    └── (dependencies installed here)
```

---


## Workflow Summary

| Step | Script | Input | Output | Time |
|------|--------|-------|--------|------|
| 1 | `horizon_csv-to-STK_e.py` | Horizons CSV | STK ephemeris (.e) | Minutes |
| 2 | `octahedron-constellation.py` | Ephemeris file | CSV data files | 2-4 hours |
| 3 | `analysis-SK-duration.py` | CSV files | PNG plots | Minutes |

---

## Performance Notes

**Simulation runtimes** (per constellation of 6 satellites):
- SK0.5h: Several hours (high frequency)
- SK1h: ~3 hours
- SK3h: ~1 hour
- SK6h: ~36.5 minutes
- SK12h: ~16 minutes
- SK1d: ~8 minutes

System performance significantly affects runtime. Modern multi-core CPUs recommended.

---

## Key Concepts

### Station Keeping (SK)
Periodic maneuvers to maintain constellation formation and counteract orbital drift
- **Shorter intervals**: More frequent corrections, higher fuel cost, lower position error
- **Longer intervals**: Less fuel, higher position drift, accumulating deviations

### Delta-V
Velocity change required for maneuvers, measured in m/s or km/s total consumption

### L2 Point (Sun-Earth)
Lagrange point ~1.5 million km from Earth, ideal for space telescopes and constellations

### Octahedron Formation
6-satellite configuration on coordinate axes for uniform coverage and redundancy

---

## Development Notes

### Adding New Constellations
Edit `CONSTELLATION_CONFIGS` in `octahedron-constellation.py`:
```python
{
    'num_satellites': 6,
    'base_name': 'MyConstellation',
    'satellite_names': [...],
    'offsets_m': {...},
    'station_keeping_interval_days': 7,
    'separation_delay_minutes': 10
}
```

### Modifying Analysis
Edit exclusion lists in `analysis-SK-duration.py`:
```python
excluded_sats = ['SK3d', 'SK1h_Yp', ...]  # Pattern matching
plot_delta_v_vs_sk_duration(exclude_names=excluded_sats)
```

### Custom Visualization
Use output data from `calculate_max_deviations()` with matplotlib:
```python
satellite_data = calculate_max_deviations()
# Create custom plots from satellite_data dictionary
```

---

## References

- [STK Python API Documentation](https://help.agi.com/stk/index.htm)
- [JPL Horizons System](https://ssd.jpl.nasa.gov/horizons/)
- [JWST Mission Details](https://www.jwst.nasa.gov/)
- Lagrange Points: https://en.wikipedia.org/wiki/Lagrange_point