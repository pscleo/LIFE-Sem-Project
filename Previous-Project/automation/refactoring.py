# %% Imports
import os

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
stkRoot.NewScenario('SatelliteLoadingScenario')
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

# %% Add a satellite object
print('Adding satellite objects...')
# satName = 'JWST'
JWSTephemerisFilePath = r'D:\Max\Uni\03-SpaceSystems\03-3. Semester\Semesterarbeit\code\horizon-to-STK\data\2025-11-06_horizons_JWST_hourly_from-launch.e'
JWST = add_satellite_external_ephemeris(scenario, 'JWST', JWSTephemerisFilePath)

# %% Set up Base Satellite
base_separation_epoch = "6 Oct 2022 07:00:00.000 UTCG"

Base = add_base_satellite_with_crossings(
    scenario=scenario,
    stkRoot=stkRoot,
    satellite_name='Base',
    leader_satellite_name='JWST',
    separation_epoch=base_separation_epoch,
    num_crossings=4,  # Can be changed to any number
    min_propagate_duration=30,  # Can also be customized
    verbose=True
)

# %% Set view
# Set View to the L2 Assembled System (need to do this after creating all satellites)
stkRoot.ExecuteCommand(f'VO */Satellite/* OrbitSystem Add System "CentralBody/Sun Syst_SEM_L2" WindowID All')
stkRoot.ExecuteCommand(f'VO */Satellite/* OrbitSystem Modify System "InertialByWindow" WindowID All Show Off')

# %% Run Astrogator to test setup
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.Action Run active profiles')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base RunMCS')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base ApplyAllProfileChanges')

# Clear Graphics, set Target Sequence to run nominal sequence and refresh graphics
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base ClearDWCGraphics')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.Action Run nominal sequence')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base RunMCS')

# %% Create an assembled coordinate system centered on Base satellite with L2 axes orientation
stkRoot.ExecuteCommand(f'VectorTool * CentralBody/Sun Create System Syst_Base_L2 "Assembled" "Satellite/Base Center" "CentralBody/Sun SEM_L2"')

# %% Set up Components for Base Satellite Coordinate System Results  
create_cartesian_coordinate_components(stkRoot, "CentralBody/Sun Syst_Base_L2", "_Base", verbose=True)

# %% Set up Follower Satellite
from helpers.add_satellites import add_constellation_satellite_with_position_hold

# Arguments for constellation satellite
satellite_name = 'Follower'
leader_satellite_name = 'Base'
separation_epoch = epoch_seconds_to_time_string(scenario, time_string_to_epoch_seconds(scenario, base_separation_epoch) + 600)  # 10 minutes after Base separation
x_offset_m = 100.0  # offset in X
y_offset_m = 0.0    # offset in Y
z_offset_m = 0.0    # offset in Z
station_keeping_interval = 1/24  # 1 hour

# Create Follower satellite using helper function
Follower = add_constellation_satellite_with_position_hold(
    scenario=scenario,
    stkRoot=stkRoot,
    satellite_name=satellite_name,
    leader_satellite_name=leader_satellite_name,
    separation_epoch=separation_epoch,
    x_offset_m=x_offset_m,
    y_offset_m=y_offset_m,
    z_offset_m=z_offset_m,
    station_keeping_interval_days=station_keeping_interval,
    verbose=True
)

# %% Run Follower Astrogator to test setup
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Action Run active profiles')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} RunMCS')

# %% Refresh visualization
stkRoot.Rewind()

# Set current time to follower release epoch and refresh view
print(f"Setting current time to follower release: {separation_epoch}")
set_current_time(stkRoot, scenario, separation_epoch)

# %% Shut down STK Application
stk.ShutDown()
# %%
