"""
================================================================================
PYRAMID CONSTELLATION SIMULATION - MANUAL WORKFLOW
================================================================================

Module: pyramid-constellation.py (LEGACY/UNOPTIMIZED)
Status: Functional but redundant - Consider refactoring with octahedron-constellation.py

PURPOSE
-------
Simulates four pyramid-shaped satellite constellations at the Sun-Earth L2 point,
each with a different station-keeping (SK) interval: 1, 7, 14, and 28 days.
Analyzes how constellation geometry affects fuel requirements and orbital stability.

SCOPE
-----
Sets up 16 constellation satellites (4 pyramids × 4 satellites each) in formation
around a Base satellite, with each pyramid representing a distinct SK strategy.

CONSTELLATION GEOMETRY
----------------------
Pyramid formation (rectangular base in Y-Z plane, offset in +X):
  
  Satellite A: X=+1000m, Y=+300m, Z=+30m   (NE corner, front-top)
  Satellite B: X=+1000m, Y=+300m, Z=-30m   (NE corner, front-bottom)
  Satellite C: X=+1000m, Y=-300m, Z=+30m   (SW corner, front-top)
  Satellite D: X=+1000m, Y=-300m, Z=-30m   (SW corner, front-bottom)

FOUR PYRAMID CONSTELLATIONS
----------------------------
Each constellation identical in geometry but different SK intervals:
  
  1. Pyramid_1:  1-day   station-keeping   (frequent maneuvers, high fuel)
  2. Pyramid_7:  7-day   station-keeping   (weekly maneuvers)
  3. Pyramid_14: 14-day  station-keeping   (biweekly maneuvers)
  4. Pyramid_28: 28-day  station-keeping   (monthly maneuvers, low fuel)

CODE STRUCTURE & ISSUES
-----------------------
✗ PROBLEM 1: Massive code duplication
   - 4 nearly identical sections for PYRAMID_CONFIG_1/7/14/28
   - Repeated satellite creation loops (4 times)
   - Repeated MCS execution loops (4 times)
   - Single change requires updates in 4 places

✗ PROBLEM 2: Poor scalability
   - Hardcoded for exactly 4 pyramids
   - Adding a 5th pyramid requires copying entire section
   - No parameterized configuration approach

✗ PROBLEM 3: Limited functionality
   - No automated report generation (unlike octahedron-constellation.py)
   - No data export or CSV parsing
   - Manual intervention required for analysis

✗ PROBLEM 4: Maintenance burden
   - Changes to helper functions must be tested 4× over
   - Different pyramids may get out of sync during updates
   - Higher risk of inconsistent behavior

COMPARISON WITH octahedron-constellation.py
--------------------------------------------
Feature                    Pyramid           Octahedron
────────────────────────────────────────────────────────
Config structure          4 separate vars   1 list (parameterized)
Satellite creation        4× loop copies    1× loop (scales to N)
MCS execution            4× loop copies    1× loop (scales to N)
Number of constellations 4 (hardcoded)     10 (parameterized)
Total satellites        16 (4×4)           61 (1 Base + 10×6)
Report generation       None              Fully automated
Data parsing           None               CSV export + parsing
Extensibility          Low               High

REFACTORING RECOMMENDATION
---------------------------
Consider consolidating pyramid configs into a parameterized list:

  CONSTELLATION_CONFIGS = [
      {
          'constellation_type': 'Pyramid',
          'num_satellites': 4,
          'base_name': 'Pyramid_1',
          'satellite_names': ['Pyramid_1_A', 'Pyramid_1_B', ...],
          'offsets_m': {...},
          'station_keeping_interval_days': 1,
          'separation_delay_minutes': 10
      },
      ...  # Other pyramids
  ]
  
Then use the single-loop approach from octahedron-constellation.py.
This would eliminate all duplication and enable report generation.

WHEN TO USE THIS FILE
---------------------
✓ Current use case: Running pyramid constellation simulations as-is
✓ Reference: Understanding the manual workflow before abstraction
✗ New work: Use octahedron-constellation.py pattern instead
✗ Maintenance: High effort due to code duplication

FUTURE WORK
-----------
1. Refactor configs into parameterized list
2. Merge with octahedron-constellation.py using unified framework
3. Add automated report generation and data export
4. Implement analysis pipeline (maneuver summaries, position deviations)

DEPENDENCIES
------------
- STK Python API (agi.stk13.*)
- helpers/add_satellites.py
- helpers/scenario_setup.py
- JWST ephemeris file

================================================================================
"""

# %% User Configuration
# Pyramid constellation settings
PYRAMID_CONFIG_7 = {
    'num_satellites': 4,
    'base_name': 'Pyramid_7',
    'satellite_names': ['Pyramid_7_A', 'Pyramid_7_B', 'Pyramid_7_C', 'Pyramid_7_D'],
    'offsets_m': {
        'Pyramid_7_A': {'x': 1000.0, 'y': 300.0, 'z': 30.0},    # +Y, +Z corner
        'Pyramid_7_B': {'x': 1000.0, 'y': 300.0, 'z': -30.0},   # +Y, -Z corner  
        'Pyramid_7_C': {'x': 1000.0, 'y': -300.0, 'z': 30.0},   # -Y, +Z corner
        'Pyramid_7_D': {'x': 1000.0, 'y': -300.0, 'z': -30.0},  # -Y, -Z corner
    },
    'station_keeping_interval_days': 7,
    'separation_delay_minutes': 10  # Minutes after Base separation
}


# %% User Configuration - Second Pyramid
# Pyramid constellation settings - 28 day station keeping
PYRAMID_CONFIG_28 = {
    'num_satellites': 4,
    'base_name': 'Pyramid_28',
    'satellite_names': ['Pyramid_28_A', 'Pyramid_28_B', 'Pyramid_28_C', 'Pyramid_28_D'],
    'offsets_m': {
        'Pyramid_28_A': {'x': 1000.0, 'y': 300.0, 'z': 30.0},    # +Y, +Z corner
        'Pyramid_28_B': {'x': 1000.0, 'y': 300.0, 'z': -30.0},   # +Y, -Z corner  
        'Pyramid_28_C': {'x': 1000.0, 'y': -300.0, 'z': 30.0},   # -Y, +Z corner
        'Pyramid_28_D': {'x': 1000.0, 'y': -300.0, 'z': -30.0},  # -Y, -Z corner
    },
    'station_keeping_interval_days': 28,
    'separation_delay_minutes': 10  # 10 minutes after Base separation
}

# %% User Configuration - Third Pyramid (14 days)
# Pyramid constellation settings - 14 day station keeping
PYRAMID_CONFIG_14 = {
    'num_satellites': 4,
    'base_name': 'Pyramid_14',
    'satellite_names': ['Pyramid_14_A', 'Pyramid_14_B', 'Pyramid_14_C', 'Pyramid_14_D'],
    'offsets_m': {
        'Pyramid_14_A': {'x': 1000.0, 'y': 300.0, 'z': 30.0},    # +Y, +Z corner
        'Pyramid_14_B': {'x': 1000.0, 'y': 300.0, 'z': -30.0},   # +Y, -Z corner  
        'Pyramid_14_C': {'x': 1000.0, 'y': -300.0, 'z': 30.0},   # -Y, +Z corner
        'Pyramid_14_D': {'x': 1000.0, 'y': -300.0, 'z': -30.0},  # -Y, -Z corner
    },
    'station_keeping_interval_days': 14,
    'separation_delay_minutes': 10  # 10 minutes after Base separation
}

# %% User Configuration - Fourth Pyramid (1 day)
# Pyramid constellation settings - 1 day station keeping
PYRAMID_CONFIG_1 = {
    'num_satellites': 4,
    'base_name': 'Pyramid_1',
    'satellite_names': ['Pyramid_1_A', 'Pyramid_1_B', 'Pyramid_1_C', 'Pyramid_1_D'],
    'offsets_m': {
        'Pyramid_1_A': {'x': 1000.0, 'y': 300.0, 'z': 30.0},    # +Y, +Z corner
        'Pyramid_1_B': {'x': 1000.0, 'y': 300.0, 'z': -30.0},   # +Y, -Z corner  
        'Pyramid_1_C': {'x': 1000.0, 'y': -300.0, 'z': 30.0},   # -Y, +Z corner
        'Pyramid_1_D': {'x': 1000.0, 'y': -300.0, 'z': -30.0},  # -Y, -Z corner
    },
    'station_keeping_interval_days': 1,
    'separation_delay_minutes': 10  # 10 minutes after Base separation
}

# %% Imports
from pathlib import Path
try:
    from agi.stk13.stkdesktop import STKDesktop
    from agi.stk13.stkobjects import *
    from agi.stk13.stkutil import *
    from agi.stk13.utilities.colors import *
    from agi.stk13.stkobjects.astrogator import *
except:
    print("Failed to import stk modules. Make sure you have installed the STK Python API wheel (agi.stk<..ver..>-py3-none-any.whl) from the STK Install bin directory")

from helpers.add_satellites import *
from helpers.scenario_setup import *

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

# %% Create a new scenario
print('Creating new scenario...')
stkRoot.NewScenario('PyramidConstellationScenario')
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
current_dir = Path(__file__).resolve().parent.parent
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

# %% Create Pyramid Constellation Satellites
print(f'\nCreating pyramid constellation with {PYRAMID_CONFIG_7["num_satellites"]} satellites...')

# Calculate common separation epoch
pyramid_separation_epoch = epoch_seconds_to_time_string(
    scenario, 
    time_string_to_epoch_seconds(scenario, base_separation_epoch) + 
    PYRAMID_CONFIG_7['separation_delay_minutes'] * 60
)
print(f'Pyramid separation epoch: {pyramid_separation_epoch}')

# Store satellite objects
pyramid_satellites = {}

# Create each pyramid satellite
for i, sat_name in enumerate(PYRAMID_CONFIG_7['satellite_names']):
    print(f'\nCreating satellite {i+1}/{PYRAMID_CONFIG_7["num_satellites"]}: {sat_name}')
    
    # Get offsets for this satellite
    offsets = PYRAMID_CONFIG_7['offsets_m'][sat_name]
    
    # Create constellation satellite
    satellite = add_constellation_satellite_with_position_hold(
        scenario=scenario,
        stkRoot=stkRoot,
        satellite_name=sat_name,
        leader_satellite_name='Base',
        separation_epoch=pyramid_separation_epoch,
        x_offset_m=offsets['x'],
        y_offset_m=offsets['y'],
        z_offset_m=offsets['z'],
        station_keeping_interval_days=PYRAMID_CONFIG_7['station_keeping_interval_days'],
        verbose=True
    )
    
    pyramid_satellites[sat_name] = satellite

# %% Run Pyramid Satellites MCS
print(f'\nRunning Mission Control Sequence for all pyramid satellites...')

for sat_name in PYRAMID_CONFIG_7['satellite_names']:
    print(f'Running MCS for {sat_name}...')
    try:
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{sat_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Action Run active profiles')
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{sat_name} RunMCS')
        print(f'  ✓ {sat_name} MCS completed successfully')
    except Exception as e:
        print(f'  ✗ {sat_name} MCS failed: {str(e)}')

# %% Create Second Pyramid Constellation Satellites (28-day SK)
print(f'\nCreating second pyramid constellation with {PYRAMID_CONFIG_28["num_satellites"]} satellites...')

# Calculate common separation epoch for second pyramid
pyramid_28_separation_epoch = epoch_seconds_to_time_string(
    scenario, 
    time_string_to_epoch_seconds(scenario, base_separation_epoch) + 
    PYRAMID_CONFIG_28['separation_delay_minutes'] * 60
)
print(f'Second pyramid separation epoch: {pyramid_28_separation_epoch}')

# Store satellite objects for second pyramid
pyramid_28_satellites = {}

# Create each pyramid satellite
for i, sat_name in enumerate(PYRAMID_CONFIG_28['satellite_names']):
    print(f'\nCreating satellite {i+1}/{PYRAMID_CONFIG_28["num_satellites"]}: {sat_name}')
    
    # Get offsets for this satellite
    offsets = PYRAMID_CONFIG_28['offsets_m'][sat_name]
    
    # Create constellation satellite
    satellite = add_constellation_satellite_with_position_hold(
        scenario=scenario,
        stkRoot=stkRoot,
        satellite_name=sat_name,
        leader_satellite_name='Base',
        separation_epoch=pyramid_28_separation_epoch,
        x_offset_m=offsets['x'],
        y_offset_m=offsets['y'],
        z_offset_m=offsets['z'],
        station_keeping_interval_days=PYRAMID_CONFIG_28['station_keeping_interval_days'],
        verbose=True
    )
    
    pyramid_28_satellites[sat_name] = satellite

# %% Run Second Pyramid Satellites MCS
print(f'\nRunning Mission Control Sequence for all second pyramid satellites...')

for sat_name in PYRAMID_CONFIG_28['satellite_names']:
    print(f'Running MCS for {sat_name}...')
    try:
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{sat_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Action Run active profiles')
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{sat_name} RunMCS')
        print(f'  ✓ {sat_name} MCS completed successfully')
    except Exception as e:
        print(f'  ✗ {sat_name} MCS failed: {str(e)}')

# %% Create Third Pyramid Constellation Satellites (14-day SK)
print(f'\nCreating third pyramid constellation with {PYRAMID_CONFIG_14["num_satellites"]} satellites...')

# Calculate common separation epoch for third pyramid
pyramid_14_separation_epoch = epoch_seconds_to_time_string(
    scenario, 
    time_string_to_epoch_seconds(scenario, base_separation_epoch) + 
    PYRAMID_CONFIG_14['separation_delay_minutes'] * 60
)
print(f'Third pyramid separation epoch: {pyramid_14_separation_epoch}')

# Store satellite objects for third pyramid
pyramid_14_satellites = {}

# Create each pyramid satellite
for i, sat_name in enumerate(PYRAMID_CONFIG_14['satellite_names']):
    print(f'\nCreating satellite {i+1}/{PYRAMID_CONFIG_14["num_satellites"]}: {sat_name}')
    
    # Get offsets for this satellite
    offsets = PYRAMID_CONFIG_14['offsets_m'][sat_name]
    
    # Create constellation satellite
    satellite = add_constellation_satellite_with_position_hold(
        scenario=scenario,
        stkRoot=stkRoot,
        satellite_name=sat_name,
        leader_satellite_name='Base',
        separation_epoch=pyramid_14_separation_epoch,
        x_offset_m=offsets['x'],
        y_offset_m=offsets['y'],
        z_offset_m=offsets['z'],
        station_keeping_interval_days=PYRAMID_CONFIG_14['station_keeping_interval_days'],
        verbose=True
    )
    
    pyramid_14_satellites[sat_name] = satellite

# %% Run Third Pyramid Satellites MCS
print(f'\nRunning Mission Control Sequence for all third pyramid satellites...')

for sat_name in PYRAMID_CONFIG_14['satellite_names']:
    print(f'Running MCS for {sat_name}...')
    try:
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{sat_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Action Run active profiles')
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{sat_name} RunMCS')
        print(f'  ✓ {sat_name} MCS completed successfully')
    except Exception as e:
        print(f'  ✗ {sat_name} MCS failed: {str(e)}')

# %% Create Fourth Pyramid Constellation Satellites (1-day SK)
print(f'\nCreating fourth pyramid constellation with {PYRAMID_CONFIG_1["num_satellites"]} satellites...')

# Calculate common separation epoch for fourth pyramid
pyramid_1_separation_epoch = epoch_seconds_to_time_string(
    scenario, 
    time_string_to_epoch_seconds(scenario, base_separation_epoch) + 
    PYRAMID_CONFIG_1['separation_delay_minutes'] * 60
)
print(f'Fourth pyramid separation epoch: {pyramid_1_separation_epoch}')

# Store satellite objects for fourth pyramid
pyramid_1_satellites = {}

# Create each pyramid satellite
for i, sat_name in enumerate(PYRAMID_CONFIG_1['satellite_names']):
    print(f'\nCreating satellite {i+1}/{PYRAMID_CONFIG_1["num_satellites"]}: {sat_name}')
    
    # Get offsets for this satellite
    offsets = PYRAMID_CONFIG_1['offsets_m'][sat_name]
    
    # Create constellation satellite
    satellite = add_constellation_satellite_with_position_hold(
        scenario=scenario,
        stkRoot=stkRoot,
        satellite_name=sat_name,
        leader_satellite_name='Base',
        separation_epoch=pyramid_1_separation_epoch,
        x_offset_m=offsets['x'],
        y_offset_m=offsets['y'],
        z_offset_m=offsets['z'],
        station_keeping_interval_days=PYRAMID_CONFIG_1['station_keeping_interval_days'],
        verbose=True
    )
    
    pyramid_1_satellites[sat_name] = satellite

# %% Run Fourth Pyramid Satellites MCS
print(f'\nRunning Mission Control Sequence for all fourth pyramid satellites...')

for sat_name in PYRAMID_CONFIG_1['satellite_names']:
    print(f'Running MCS for {sat_name}...')
    try:
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{sat_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Action Run active profiles')
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{sat_name} RunMCS')
        print(f'  ✓ {sat_name} MCS completed successfully')
    except Exception as e:
        print(f'  ✗ {sat_name} MCS failed: {str(e)}')

# %% Set current time and refresh view
stkRoot.Rewind()
print(f"\nSetting current time to pyramid release: {pyramid_separation_epoch}")
set_current_time(stkRoot, scenario, pyramid_separation_epoch)

# %% Print Complete Constellation Summary
print(f'\n{"="*80}')
print(f'COMPLETE CONSTELLATION SUMMARY')
print(f'{"="*80}')
print(f'Base satellite: Base')
print(f'Leader satellite: JWST')
print(f'Base separation: {base_separation_epoch}')

print(f'\n--- FIRST PYRAMID (7-day station-keeping) ---')
print(f'Pyramid separation: {pyramid_separation_epoch}')
print(f'Number of satellites: {PYRAMID_CONFIG_7["num_satellites"]}')
print(f'Station-keeping interval: {PYRAMID_CONFIG_7["station_keeping_interval_days"]} days')
print(f'Satellite configuration:')
for sat_name in PYRAMID_CONFIG_7['satellite_names']:
    offsets = PYRAMID_CONFIG_7['offsets_m'][sat_name]
    print(f'  {sat_name}: X={offsets["x"]:+6.1f}m, Y={offsets["y"]:+6.1f}m, Z={offsets["z"]:+6.1f}m')

print(f'\n--- SECOND PYRAMID (14-day station-keeping) ---')
print(f'Pyramid separation: {pyramid_14_separation_epoch}')
print(f'Number of satellites: {PYRAMID_CONFIG_14["num_satellites"]}')
print(f'Station-keeping interval: {PYRAMID_CONFIG_14["station_keeping_interval_days"]} days')
print(f'Satellite configuration:')
for sat_name in PYRAMID_CONFIG_14['satellite_names']:
    offsets = PYRAMID_CONFIG_14['offsets_m'][sat_name]
    print(f'  {sat_name}: X={offsets["x"]:+6.1f}m, Y={offsets["y"]:+6.1f}m, Z={offsets["z"]:+6.1f}m')

print(f'\n--- THIRD PYRAMID (28-day station-keeping) ---')
print(f'Pyramid separation: {pyramid_28_separation_epoch}')
print(f'Number of satellites: {PYRAMID_CONFIG_28["num_satellites"]}')
print(f'Station-keeping interval: {PYRAMID_CONFIG_28["station_keeping_interval_days"]} days')
print(f'Satellite configuration:')
for sat_name in PYRAMID_CONFIG_28['satellite_names']:
    offsets = PYRAMID_CONFIG_28['offsets_m'][sat_name]
    print(f'  {sat_name}: X={offsets["x"]:+6.1f}m, Y={offsets["y"]:+6.1f}m, Z={offsets["z"]:+6.1f}m')

print(f'\n--- FOURTH PYRAMID (1-day station-keeping) ---')
print(f'Pyramid separation: {pyramid_1_separation_epoch}')
print(f'Number of satellites: {PYRAMID_CONFIG_1["num_satellites"]}')
print(f'Station-keeping interval: {PYRAMID_CONFIG_1["station_keeping_interval_days"]} days')
print(f'Satellite configuration:')
for sat_name in PYRAMID_CONFIG_1['satellite_names']:
    offsets = PYRAMID_CONFIG_1['offsets_m'][sat_name]
    print(f'  {sat_name}: X={offsets["x"]:+6.1f}m, Y={offsets["y"]:+6.1f}m, Z={offsets["z"]:+6.1f}m')

total_satellites = 1 + PYRAMID_CONFIG_7["num_satellites"] + PYRAMID_CONFIG_14["num_satellites"] + PYRAMID_CONFIG_28["num_satellites"] + PYRAMID_CONFIG_1["num_satellites"]
print(f'\nTotal constellation satellites: {total_satellites} (1 Base + 4×4 pyramids)')
print(f'Station-keeping intervals: 1, 7, 14, and 28 days')
print(f'\nConstellation setup complete! 🚀🚀🚀🚀')

# %%
