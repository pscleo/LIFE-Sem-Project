"""
================================================================================
OCTAHEDRON CONSTELLATION SIMULATION - PRODUCTION WORKFLOW
================================================================================

Module: octahedron-constellation.py
Status: Production (main simulation script)

PURPOSE
-------
Comprehensive simulation of 10 octahedron satellite constellations at Sun-Earth L2,
each with different station-keeping (SK) intervals (0.5h to 28 days). Generates
complete orbital mechanics data, maneuver analysis, and position tracking for
constellation design validation.

SCOPE
-----
Simulates 61 total satellites:
  - 1 Base satellite (orbit maintenance reference)
  - 60 constellation satellites (10 SK intervals × 6 satellites each)

Generates automated reports for Delta-V analysis and position deviation tracking.

CONSTELLATION STRUCTURE
-----------------------
Octahedron formation (6 satellites on coordinate axes, ±1000m offset):
  
  Satellite X+: X=+1000m, Y=0m, Z=0m
  Satellite X-: X=-1000m, Y=0m, Z=0m
  Satellite Y+: X=0m, Y=+1000m, Z=0m
  Satellite Y-: X=0m, Y=-1000m, Z=0m
  Satellite Z+: X=0m, Y=0m, Z=+1000m
  Satellite Z-: X=0m, Y=0m, Z=-1000m

TEN STATION-KEEPING INTERVALS
------------------------------
SK0p5h:  0.5 hours  (30 minutes)  - Frequent maneuvers, high fuel
SK1h:    1 hour
SK3h:    3 hours
SK6h:    6 hours
SK12h:   12 hours
SK1d:    1 day
SK3d:    3 days
SK7d:    7 days     - Default reference
SK14d:   14 days
SK28d:   28 days    - Infrequent maneuvers, low fuel

WORKFLOW
--------
1. Initialize STK scenario with L2 coordinate system
2. Load JWST ephemeris (reference satellite)
3. Create and optimize Base satellite (4 orbital plane crossings)
4. Create all 10 constellations (60 satellites total)
5. Run Mission Control Sequences for orbit optimization
6. Export maneuver summaries (Delta-V analysis)
7. Export relative position reports (deviation tracking)
8. Parse data to CSV for analysis pipeline

OUTPUT DATA
-----------
Maneuver Summaries:
  data-export/maneuver-summaries/Octahedron_SK*.csv
  - Maneuver timing, duration, Delta-V per maneuver

Position Reports:
  data-export/positions/Octahedron_SK*.csv
  - Orbital position, velocity, magnitude deviation
  - 10-minute time step data points

CONFIGURATION SECTION
---------------------
Edit CONSTELLATION_CONFIGS to:
  - Add/remove SK intervals
  - Change satellite counts (currently 6)
  - Modify offset distances (currently ±1000m)
  - Adjust separation delays

USER PARAMETERS
---------------
Easily configurable:
  - Base separation epoch
  - Scenario time bounds
  - Reference coordinate system
  - Export time step (600 seconds = 10 minutes)
  - Report styles (helpers/Maneuver-Summary-Detailed.rst)

DEPENDENCIES
------------
- STK 13+ with Python API
- helpers/add_satellites.py      (satellite creation)
- helpers/scenario_setup.py      (scenario initialization)
- helpers/analysis.py            (report generation & parsing)
- JWST ephemeris file (relative path resolution)
- Helper report styles (.rst files)

INTEGRATION WITH ANALYSIS PIPELINE
-----------------------------------
Output → analysis-SK-duration.py
  1. Reads generated CSV files
  2. Parses maneuver and position data
  3. Creates visualizations:
     - Delta-V vs SK interval
     - Position deviations vs time
     - Correlation plots

TYPICAL EXECUTION
-----------------
Run this script in Jupyter or Python REPL:
  - Full execution: ~5 minutes to several hours (depends on SK intervals)
  - Can be run cell-by-cell for iterative development
  - Supports reconnection to STK if kernel crashes, or if saved STK scenario is loaded

SCRIPT STRUCTURE
----------------
Configuration (constellation parameters: CONSTELLATION_CONFIGS list)
Imports and module reloading
STK Application initialization
Scenario setup (time bounds, coordinate system)
Base satellite creation and optimization
Constellation creation loop (all 10 SK intervals)
Mission Control Sequence execution
Constellation summary printing
Maneuver summary report export and parsing
Relative position report export and parsing
Position data spike removal (deprecated/commented)

KNOWN ISSUES & EXCLUSIONS
-------------------------
Some datasets excluded from analysis (see analysis-SK-duration.py):
  - SK3d:        Display noise (excessive vibrations)
  - SK1d_Xm/Zm:  Oscillation anomaly around 170 days
  - SK1h_Y*/Z*:  Optimization failed (diverging deviations), have to be re-run
  - SK0p5h_*:    Some incomplete simulations, have to be re-run

See analysis-SK-duration.py for complete exclusion list.

PERFORMANCE NOTES
-----------------
Approximate runtimes of the Maneuver Control Sequence (MCS) execution:
(per constellation of 6 satellites, varies by system performance)
  - SK0p5h:  Several hours (high maneuver frequency)
  - SK1h:   3 hours
  - SK3h:   1 hour
  - SK6h:   36.5 minutes
  - SK12h:  16 minutes
  - SK1d:   8 minutes
  - Full suite: several hours, depends on system performance

RESTART/RECONNECTION
-------------------
If Jupyter kernel crashes, reconnect without re-running everything:
  
  # 1. Restart Jupyter kernel
  # 2. Rerun satellite configuration and import cells (do not run the stk application launch)
  # 3. Copy-paste the reconnection code from collection-of-utility-commands.py
  
  # Then skip to desired section and continue, likely the analysis after MCS execution

VALIDATION CHECKLIST
--------------------
Before running:
  ✓ STK 13+ installed with Python API
  ✓ JWST ephemeris file exists (auto-checked)
  ✓ helpers/ directory present
  ✓ data-export/ directory structure created (auto-created)
  ✓ Report style files (.rst) in helpers/
  
After running:
  ✓ All CSV files generated in data-export/
  ✓ Maneuver summaries parsed (*.csv in maneuver-summaries/)
  ✓ Position reports parsed (*.csv in positions/)
  ✓ No exceptions in MCS execution (check console output)

NEXT STEPS
----------
1. Run octahedron-constellation.py (this file)
2. Check data-export/ for generated CSV files
3. Run analysis-SK-duration.py for visualization
4. Examine plots in results/ directory

================================================================================
"""

# %% User Configuration
# Octahedron constellation configurations - list of all constellations to create
CONSTELLATION_CONFIGS = [
    { # 0.5h, took approximately ? min to run
        'num_satellites': 6,
        'base_name': 'Octahedron_SK0p5h',
        'satellite_names': ['Octahedron_SK0p5h_Xp1000m', 'Octahedron_SK0p5h_Xm1000m', 'Octahedron_SK0p5h_Yp1000m', 'Octahedron_SK0p5h_Ym1000m', 'Octahedron_SK0p5h_Zp1000m', 'Octahedron_SK0p5h_Zm1000m'],
        'offsets_m': {
            'Octahedron_SK0p5h_Xp1000m': {'x': 1000.0, 'y': 0.0, 'z': 0.0},    # +X
            'Octahedron_SK0p5h_Xm1000m': {'x': -1000.0, 'y': 0.0, 'z': 0.0},   # -X
            'Octahedron_SK0p5h_Yp1000m': {'x': 0.0, 'y': 1000.0, 'z': 0.0},    # +Y
            'Octahedron_SK0p5h_Ym1000m': {'x': 0.0, 'y': -1000.0, 'z': 0.0},   # -Y
            'Octahedron_SK0p5h_Zp1000m': {'x': 0.0, 'y': 0.0, 'z': 1000.0},    # +Z
            'Octahedron_SK0p5h_Zm1000m': {'x': 0.0, 'y': 0.0, 'z': -1000.0},   # -Z
        },
        'station_keeping_interval_days': 0.5 / 24, # 0.5 h in days
        'separation_delay_minutes': 10
    },
    { # 1h, took ? min to run
        'num_satellites': 6,
        'base_name': 'Octahedron_SK1h',
        'satellite_names': ['Octahedron_SK1h_Xp1000m', 'Octahedron_SK1h_Xm1000m', 'Octahedron_SK1h_Yp1000m', 'Octahedron_SK1h_Ym1000m', 'Octahedron_SK1h_Zp1000m', 'Octahedron_SK1h_Zm1000m'],
        'offsets_m': {
            'Octahedron_SK1h_Xp1000m': {'x': 1000.0, 'y': 0.0, 'z': 0.0},    # +X
            'Octahedron_SK1h_Xm1000m': {'x': -1000.0, 'y': 0.0, 'z': 0.0},   # -X
            'Octahedron_SK1h_Yp1000m': {'x': 0.0, 'y': 1000.0, 'z': 0.0},    # +Y
            'Octahedron_SK1h_Ym1000m': {'x': 0.0, 'y': -1000.0, 'z': 0.0},   # -Y
            'Octahedron_SK1h_Zp1000m': {'x': 0.0, 'y': 0.0, 'z': 1000.0},    # +Z
            'Octahedron_SK1h_Zm1000m': {'x': 0.0, 'y': 0.0, 'z': -1000.0},   # -Z
        },
        'station_keeping_interval_days': 1 /24, # 1 h in days
        'separation_delay_minutes': 10
    },
    { # 3h, took ? min to run
        'num_satellites': 6,
        'base_name': 'Octahedron_SK3h',
        'satellite_names': ['Octahedron_SK3h_Xp1000m', 'Octahedron_SK3h_Xm1000m', 'Octahedron_SK3h_Yp1000m', 'Octahedron_SK3h_Ym1000m', 'Octahedron_SK3h_Zp1000m', 'Octahedron_SK3h_Zm1000m'],
        'offsets_m': {
            'Octahedron_SK3h_Xp1000m': {'x': 1000.0, 'y': 0.0, 'z': 0.0},    # +X
            'Octahedron_SK3h_Xm1000m': {'x': -1000.0, 'y': 0.0, 'z': 0.0},   # -X
            'Octahedron_SK3h_Yp1000m': {'x': 0.0, 'y': 1000.0, 'z': 0.0},    # +Y
            'Octahedron_SK3h_Ym1000m': {'x': 0.0, 'y': -1000.0, 'z': 0.0},   # -Y
            'Octahedron_SK3h_Zp1000m': {'x': 0.0, 'y': 0.0, 'z': 1000.0},    # +Z
            'Octahedron_SK3h_Zm1000m': {'x': 0.0, 'y': 0.0, 'z': -1000.0},   # -Z
        },
        'station_keeping_interval_days': 3 /24, # 3 h in days
        'separation_delay_minutes': 10
    },
    { # 6h, took 36.5 min to run
        'num_satellites': 6,
        'base_name': 'Octahedron_SK6h',
        'satellite_names': ['Octahedron_SK6h_Xp1000m', 'Octahedron_SK6h_Xm1000m', 'Octahedron_SK6h_Yp1000m', 'Octahedron_SK6h_Ym1000m', 'Octahedron_SK6h_Zp1000m', 'Octahedron_SK6h_Zm1000m'],
        'offsets_m': {
            'Octahedron_SK6h_Xp1000m': {'x': 1000.0, 'y': 0.0, 'z': 0.0},    # +X
            'Octahedron_SK6h_Xm1000m': {'x': -1000.0, 'y': 0.0, 'z': 0.0},   # -X
            'Octahedron_SK6h_Yp1000m': {'x': 0.0, 'y': 1000.0, 'z': 0.0},    # +Y
            'Octahedron_SK6h_Ym1000m': {'x': 0.0, 'y': -1000.0, 'z': 0.0},   # -Y
            'Octahedron_SK6h_Zp1000m': {'x': 0.0, 'y': 0.0, 'z': 1000.0},    # +Z
            'Octahedron_SK6h_Zm1000m': {'x': 0.0, 'y': 0.0, 'z': -1000.0},   # -Z
        },
        'station_keeping_interval_days': 6 /24, # 6 h in days
        'separation_delay_minutes': 10
    },
    { # 12h, took 16 min to run
        'num_satellites': 6,
        'base_name': 'Octahedron_SK12h',
        'satellite_names': ['Octahedron_SK12h_Xp1000m', 'Octahedron_SK12h_Xm1000m', 'Octahedron_SK12h_Yp1000m', 'Octahedron_SK12h_Ym1000m', 'Octahedron_SK12h_Zp1000m', 'Octahedron_SK12h_Zm1000m'],
        'offsets_m': {
            'Octahedron_SK12h_Xp1000m': {'x': 1000.0, 'y': 0.0, 'z': 0.0},    # +X
            'Octahedron_SK12h_Xm1000m': {'x': -1000.0, 'y': 0.0, 'z': 0.0},   # -X
            'Octahedron_SK12h_Yp1000m': {'x': 0.0, 'y': 1000.0, 'z': 0.0},    # +Y
            'Octahedron_SK12h_Ym1000m': {'x': 0.0, 'y': -1000.0, 'z': 0.0},   # -Y
            'Octahedron_SK12h_Zp1000m': {'x': 0.0, 'y': 0.0, 'z': 1000.0},    # +Z
            'Octahedron_SK12h_Zm1000m': {'x': 0.0, 'y': 0.0, 'z': -1000.0},   # -Z
        },
        'station_keeping_interval_days': 12 /24, # 12 h in days
        'separation_delay_minutes': 10
    },
    {
        'num_satellites': 6,
        'base_name': 'Octahedron_SK1d',
        'satellite_names': ['Octahedron_SK1d_Xp1000m', 'Octahedron_SK1d_Xm1000m', 'Octahedron_SK1d_Yp1000m', 'Octahedron_SK1d_Ym1000m', 'Octahedron_SK1d_Zp1000m', 'Octahedron_SK1d_Zm1000m'],
        'offsets_m': {
            'Octahedron_SK1d_Xp1000m': {'x': 1000.0, 'y': 0.0, 'z': 0.0},    # +X
            'Octahedron_SK1d_Xm1000m': {'x': -1000.0, 'y': 0.0, 'z': 0.0},   # -X
            'Octahedron_SK1d_Yp1000m': {'x': 0.0, 'y': 1000.0, 'z': 0.0},    # +Y
            'Octahedron_SK1d_Ym1000m': {'x': 0.0, 'y': -1000.0, 'z': 0.0},   # -Y
            'Octahedron_SK1d_Zp1000m': {'x': 0.0, 'y': 0.0, 'z': 1000.0},    # +Z
            'Octahedron_SK1d_Zm1000m': {'x': 0.0, 'y': 0.0, 'z': -1000.0},   # -Z
        },
        'station_keeping_interval_days': 1,
        'separation_delay_minutes': 10
    },
    {
        'num_satellites': 6,
        'base_name': 'Octahedron_SK3d',
        'satellite_names': ['Octahedron_SK3d_Xp1000m', 'Octahedron_SK3d_Xm1000m', 'Octahedron_SK3d_Yp1000m', 'Octahedron_SK3d_Ym1000m', 'Octahedron_SK3d_Zp1000m', 'Octahedron_SK3d_Zm1000m'],
        'offsets_m': {
            'Octahedron_SK3d_Xp1000m': {'x': 1000.0, 'y': 0.0, 'z': 0.0},
            'Octahedron_SK3d_Xm1000m': {'x': -1000.0, 'y': 0.0, 'z': 0.0},
            'Octahedron_SK3d_Yp1000m': {'x': 0.0, 'y': 1000.0, 'z': 0.0},
            'Octahedron_SK3d_Ym1000m': {'x': 0.0, 'y': -1000.0, 'z': 0.0},
            'Octahedron_SK3d_Zp1000m': {'x': 0.0, 'y': 0.0, 'z': 1000.0},
            'Octahedron_SK3d_Zm1000m': {'x': 0.0, 'y': 0.0, 'z': -1000.0},
        },
        'station_keeping_interval_days': 3,
        'separation_delay_minutes': 10
    },
    {
        'num_satellites': 6,
        'base_name': 'Octahedron_SK7d',
        'satellite_names': ['Octahedron_SK7d_Xp1000m', 'Octahedron_SK7d_Xm1000m', 'Octahedron_SK7d_Yp1000m', 'Octahedron_SK7d_Ym1000m', 'Octahedron_SK7d_Zp1000m', 'Octahedron_SK7d_Zm1000m'],
        'offsets_m': {
            'Octahedron_SK7d_Xp1000m': {'x': 1000.0, 'y': 0.0, 'z': 0.0},
            'Octahedron_SK7d_Xm1000m': {'x': -1000.0, 'y': 0.0, 'z': 0.0},
            'Octahedron_SK7d_Yp1000m': {'x': 0.0, 'y': 1000.0, 'z': 0.0},
            'Octahedron_SK7d_Ym1000m': {'x': 0.0, 'y': -1000.0, 'z': 0.0},
            'Octahedron_SK7d_Zp1000m': {'x': 0.0, 'y': 0.0, 'z': 1000.0},
            'Octahedron_SK7d_Zm1000m': {'x': 0.0, 'y': 0.0, 'z': -1000.0},
        },
        'station_keeping_interval_days': 7,
        'separation_delay_minutes': 10
    },
    {
        'num_satellites': 6,
        'base_name': 'Octahedron_SK14d',
        'satellite_names': ['Octahedron_SK14d_Xp1000m', 'Octahedron_SK14d_Xm1000m', 'Octahedron_SK14d_Yp1000m', 'Octahedron_SK14d_Ym1000m', 'Octahedron_SK14d_Zp1000m', 'Octahedron_SK14d_Zm1000m'],
        'offsets_m': {
            'Octahedron_SK14d_Xp1000m': {'x': 1000.0, 'y': 0.0, 'z': 0.0},
            'Octahedron_SK14d_Xm1000m': {'x': -1000.0, 'y': 0.0, 'z': 0.0},
            'Octahedron_SK14d_Yp1000m': {'x': 0.0, 'y': 1000.0, 'z': 0.0},
            'Octahedron_SK14d_Ym1000m': {'x': 0.0, 'y': -1000.0, 'z': 0.0},
            'Octahedron_SK14d_Zp1000m': {'x': 0.0, 'y': 0.0, 'z': 1000.0},
            'Octahedron_SK14d_Zm1000m': {'x': 0.0, 'y': 0.0, 'z': -1000.0},
        },
        'station_keeping_interval_days': 14,
        'separation_delay_minutes': 10
    },
    {
        'num_satellites': 6,
        'base_name': 'Octahedron_SK28d',
        'satellite_names': ['Octahedron_SK28d_Xp1000m', 'Octahedron_SK28d_Xm1000m', 'Octahedron_SK28d_Yp1000m', 'Octahedron_SK28d_Ym1000m', 'Octahedron_SK28d_Zp1000m', 'Octahedron_SK28d_Zm1000m'],
        'offsets_m': {
            'Octahedron_SK28d_Xp1000m': {'x': 1000.0, 'y': 0.0, 'z': 0.0},
            'Octahedron_SK28d_Xm1000m': {'x': -1000.0, 'y': 0.0, 'z': 0.0},
            'Octahedron_SK28d_Yp1000m': {'x': 0.0, 'y': 1000.0, 'z': 0.0},
            'Octahedron_SK28d_Ym1000m': {'x': 0.0, 'y': -1000.0, 'z': 0.0},
            'Octahedron_SK28d_Zp1000m': {'x': 0.0, 'y': 0.0, 'z': 1000.0},
            'Octahedron_SK28d_Zm1000m': {'x': 0.0, 'y': 0.0, 'z': -1000.0},
        },
        'station_keeping_interval_days': 28,
        'separation_delay_minutes': 10
    }
]

# %% Imports (Run this ONCE at the start)
from pathlib import Path
import os
import importlib

try:
    from agi.stk13.stkdesktop import STKDesktop
    from agi.stk13.stkobjects import *
    from agi.stk13.stkutil import *
    from agi.stk13.utilities.colors import *
    from agi.stk13.stkobjects.astrogator import *
except:
    print("Failed to import stk modules...")

from helpers import add_satellites, scenario_setup, analysis

# %% Reload modules (Run this ANYTIME you edit a helper file)
import importlib
importlib.reload(scenario_setup)
importlib.reload(add_satellites)
importlib.reload(analysis)

# Re-import functions after reloading
from helpers.add_satellites import add_satellite_external_ephemeris, add_base_satellite_with_crossings, add_constellation_satellite_with_position_hold, set_constellation_attitudes
from helpers.scenario_setup import setup_l2_coordinate_system, create_cartesian_coordinate_components, set_current_time, time_string_to_epoch_seconds, epoch_seconds_to_time_string
from helpers.analysis import export_maneuver_summary_report, parse_maneuver_summary_report, export_relative_position_report, parse_relative_position_report, remove_position_spikes, parse_stk_position_txt

# %% Initialize STK Application
if os.name == "nt":
    stk = STKDesktop.StartApplication(
        visible=True,
        userControl=False,
        )
    stkRoot = stk.Root
else:
    print("Only works on windows with the desktop application.")
    quit()

# %% Connect to a running instance of STK, e.g. if you want to reconnect after the jupyter kernel crashed.
# stk = STKDesktop.AttachToApplication()
# stkRoot = stk.Root

# %% Create a new scenario
print('Creating new scenario...')
stkRoot.NewScenario('OctahedronConstellationScenario')
scenario = stkRoot.CurrentScenario

# reset dimensions to default
dimensions = stkRoot.UnitPreferences
dimensions.ResetUnits()
dimensions.SetCurrentUnit("DateFormat", "UTCG")
dimensions.SetCurrentUnit("DistanceUnit", "km")

# Set scenario time bounds (JWST launch was 25 Dec 2021)
startTime = '26 Dec 2021 00:00:00.000'
stopTime = '26 Dec 2025 00:00:00.000'
epoch = '25 Dec 2021 00:00:00.000'
scenario.StartTime = startTime
scenario.StopTime = stopTime
scenario.Epoch = epoch
set_current_time(stkRoot, scenario, '26 Dec 2021 00:00:00.000')

print(f'Scenario created: {scenario.InstanceName}')

# %% Create L2 coordinate system, Graphics Setup
setup_l2_coordinate_system(stkRoot, verbose=True)

# %% Set up Components for Target Sequence Results
create_cartesian_coordinate_components(stkRoot, "CentralBody/Sun Syst_SEM_L2", "_L2", verbose=True)

# %% Add JWST satellite
print('Adding satellite objects...')
# Find JWST ephemeris file using relative path from automation folder
current_dir = Path(__file__).resolve().parent
jwst_data_dir = current_dir.parent / "horizon-to-STK" / "data"
JWSTephemerisFilePath = str(jwst_data_dir / "2025-11-06_horizons_JWST_hourly_from-launch.e")

# Verify file exists
if not Path(JWSTephemerisFilePath).exists():
    raise FileNotFoundError(f"JWST ephemeris file not found at: {JWSTephemerisFilePath}")

JWST = add_satellite_external_ephemeris(scenario, 'JWST', JWSTephemerisFilePath)

# %% Set up Base Satellite
base_separation_epoch = "6 Oct 2022 07:00:00.000 UTCG"

Base = add_base_satellite_with_crossings(
    scenario=scenario,
    stkRoot=stkRoot,
    satellite_name='Base',
    leader_satellite_name='JWST',
    separation_epoch=base_separation_epoch,
    num_crossings=4,
    min_propagate_duration=30,
    verbose=True
)

# %% Set View to the L2 Assembled System
stkRoot.ExecuteCommand(f'VO */Satellite/* OrbitSystem Add System "CentralBody/Sun Syst_SEM_L2" WindowID All')
stkRoot.ExecuteCommand(f'VO */Satellite/* OrbitSystem Modify System "InertialByWindow" WindowID All Show Off')

# %% Run Base Satellite MCS
print('Running Base satellite Mission Control Sequence...')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.Action Run active profiles')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base RunMCS')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base ApplyAllProfileChanges')

# Clear Graphics, set Target Sequence to run nominal sequence and refresh graphics
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base ClearDWCGraphics')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.Action Run nominal sequence')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base RunMCS')

# %% Create Base coordinate system
stkRoot.ExecuteCommand(f'VectorTool * CentralBody/Sun Create System Syst_Base_L2 "Assembled" "Satellite/Base Center" "CentralBody/Sun SEM_L2"')

# %% Set up Components for Base Satellite Coordinate System Results  
create_cartesian_coordinate_components(stkRoot, "CentralBody/Sun Syst_Base_L2", "_Base", verbose=True)

# %% Create All Constellations
# Store all constellation satellites
all_constellations = {}

# Iterate through each configuration
for config_idx, config in enumerate(CONSTELLATION_CONFIGS):
    print(f'\n{"="*80}')
    print(f'Creating constellation {config_idx+1}/{len(CONSTELLATION_CONFIGS)}: {config["base_name"]}')
    print(f'{"="*80}')
    
    # Calculate separation epoch for this constellation
    constellation_separation_epoch = epoch_seconds_to_time_string(
        scenario, 
        time_string_to_epoch_seconds(scenario, base_separation_epoch) + 
        config['separation_delay_minutes'] * 60
    )
    print(f'Constellation separation epoch: {constellation_separation_epoch}')
    print(f'Number of satellites: {config["num_satellites"]}')
    print(f'Station-keeping interval: {config["station_keeping_interval_days"]} days')
    
    # Store satellites for this constellation
    constellation_satellites = {}
    
    # Create each satellite in the constellation
    for i, sat_name in enumerate(config['satellite_names']):
        print(f'\nCreating satellite {i+1}/{config["num_satellites"]}: {sat_name}')
        
        # Get offsets for this satellite
        offsets = config['offsets_m'][sat_name]
        
        # Create constellation satellite
        satellite = add_constellation_satellite_with_position_hold(
            scenario=scenario,
            stkRoot=stkRoot,
            satellite_name=sat_name,
            leader_satellite_name='Base',
            separation_epoch=constellation_separation_epoch,
            x_offset_m=offsets['x'],
            y_offset_m=offsets['y'],
            z_offset_m=offsets['z'],
            station_keeping_interval_days=config['station_keeping_interval_days'],
            verbose=True
        )
        
        constellation_satellites[sat_name] = satellite
    
    # Store this constellation
    all_constellations[config['base_name']] = {
        'config': config,
        'satellites': constellation_satellites,
        'separation_epoch': constellation_separation_epoch
    }

# %% Run All Constellation Satellites MCS
print(f'\n{"="*80}')
print(f'RUNNING MISSION CONTROL SEQUENCES')
print(f'{"="*80}')

for config in CONSTELLATION_CONFIGS:
    print(f'\n--- Running MCS for {config["base_name"]} ---')
    
    for sat_name in config['satellite_names']:
        print(f'Running MCS for {sat_name}...')
        try:
            stkRoot.ExecuteCommand(f'Astrogator */Satellite/{sat_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Action Run active profiles')
            stkRoot.ExecuteCommand(f'Astrogator */Satellite/{sat_name} RunMCS')
            stkRoot.ExecuteCommand(f'Astrogator */Satellite/{sat_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Action Run nominal sequence')
            print(f'  ✓ {sat_name} MCS completed successfully')
        except Exception as e:
            print(f'  ✗ {sat_name} MCS failed: {str(e)}')

# %% Set current time and refresh view
stkRoot.Rewind()
# Use the first constellation's separation epoch
first_separation_epoch = list(all_constellations.values())[0]['separation_epoch']
print(f"\nSetting current time to first constellation release: {first_separation_epoch}")
set_current_time(stkRoot, scenario, first_separation_epoch)

# %% Print Complete Constellation Summary
print(f'\n{"="*80}')
print(f'COMPLETE CONSTELLATION SUMMARY')
print(f'{"="*80}')
print(f'Base satellite: Base')
print(f'Leader satellite: JWST')
print(f'Base separation: {base_separation_epoch}')

for constellation_name, constellation_data in all_constellations.items():
    config = constellation_data['config']
    separation_epoch = constellation_data['separation_epoch']
    
    print(f'\n--- {constellation_name} ({config["station_keeping_interval_days"]}-day station-keeping) ---')
    print(f'Constellation separation: {separation_epoch}')
    print(f'Number of satellites: {config["num_satellites"]}')
    print(f'Station-keeping interval: {config["station_keeping_interval_days"]} days')
    print(f'Satellite configuration:')
    for sat_name in config['satellite_names']:
        offsets = config['offsets_m'][sat_name]
        print(f'  {sat_name}: X={offsets["x"]:+7.1f}m, Y={offsets["y"]:+7.1f}m, Z={offsets["z"]:+7.1f}m')

total_satellites = 1 + sum(config['num_satellites'] for config in CONSTELLATION_CONFIGS)
print(f'\nTotal constellation satellites: {total_satellites} (1 Base + {len(CONSTELLATION_CONFIGS)} octahedrons × 6 satellites)')
print(f'Station-keeping intervals: {", ".join(str(c["station_keeping_interval_days"]) for c in CONSTELLATION_CONFIGS)} days')
print(f'\nConstellation setup complete! 🚀')

# %% Load Detailed Maneuver Summary Report Style
# Load the detailed maneuver summary report style
# located in the helpers directory
stkRoot.ExecuteCommand(f'ReportStyle * Load "{str((Path(__file__).resolve().parent / "helpers" / "Maneuver-Summary-Detailed.rst").absolute())}"')

# %% Export Maneuver Summary Reports for All Constellation Satellites
exported_files = []

for config in CONSTELLATION_CONFIGS:
    for sat_name in config['satellite_names']:
        txt_file = export_maneuver_summary_report(stkRoot, sat_name, verbose=False)
        exported_files.append(txt_file)

# %% Parse and Convert Maneuver Summary Reports to CSV
for txt_file in exported_files:
    try:
        parse_maneuver_summary_report(txt_file, delete_source=False, verbose=False)
    except Exception as e:
        print(f'✗ Failed to parse {txt_file}: {str(e)}')


# %% Export Relative Position Reports for All Constellation Satellites
# Export for all constellation satellites
for config in CONSTELLATION_CONFIGS:
    for sat_name in config['satellite_names']:
        # Calculate start time for report (next full hour after separation) - WITHOUT UTCG for this connect command
        start_epoch = time_string_to_epoch_seconds(scenario, constellation_separation_epoch) + ((-config['separation_delay_minutes']) % 60) * 60
        # The next step is very important  to ensure clean data.
        # If a datapoint is exported exactly at the time of a maneuver, STK outputs a value which is off by several orders of magnitude.
        # To avoid this, the export start time is set to one second after the full hour.
        # With the regular time step of 10 minutes, this ensures no data point coincides with a maneuver time (set to be in regular multiples or fractions of hours).
        start_epoch += 1  # move to next full hour
        start_time_str = epoch_seconds_to_time_string(scenario, start_epoch, append_UTCG=False)
        
        export_relative_position_report(stkRoot, sat_name, 
                        time_period_start=start_time_str,
                        time_step_seconds=600,  # 10 minutes
                        verbose=False)

# %% Parse Relative Position Reports to CSV
# Parse without trimming (all data), since this functionality has since been integrated into the export function
for config in CONSTELLATION_CONFIGS:
    for sat_name in config['satellite_names']:
        txt_file = str(Path(__file__).resolve().parent / 'data-export' / 'temp' / 'position' / f'{sat_name}.txt')
        try:
            parse_stk_position_txt(txt_file, trim_data=False, verbose=False)
            # parse_relative_position_report(txt_file, trim_data=False, verbose=False)
        except Exception as e:
            print(f'✗ Failed to parse {txt_file}: {str(e)}')
            
# %% Remove spikes from position data
# DEPRECATED: Issue solved by shifting export start time by 1 second to avoid maneuvers
# 
# Remove spikes from all constellation satellites position data
# This was added after observing spikes (single data values which are off by orders of magnitude)
# in the relative position data
# Replaces the spikes with averaged values from neighboring data points
# print(f'\n{"="*80}')
# print('REMOVING POSITION DATA SPIKES')
# print(f'{"="*80}')

# for config in CONSTELLATION_CONFIGS:
#     for sat_name in config['satellite_names']:
#         csv_file = str(Path(__file__).resolve().parent / 'data-export' / 'positions' / f'{sat_name}.csv')
#         try:
#             remove_position_spikes(csv_file,
#                                    window_size=5,
#                                    threshold_mad=5, # empirical, set by trying out and looking at the data graphs
#                                    verbose=True
#                                    )
#         except Exception as e:
#             print(f'✗ Failed to clean spikes in {sat_name}: {str(e)}')

# print(f'\n{"="*80}')
# print('SPIKE REMOVAL COMPLETE')
# print(f'{"="*80}')



# %%
