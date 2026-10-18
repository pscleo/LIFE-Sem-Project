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

from helpers.add_satellites import add_satellite_external_ephemeris
from helpers.scenario_setup import get_current_time_string, set_current_time, time_string_to_epoch_seconds, epoch_seconds_to_time_string

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
# Create an assembled coordinate system at L2 for visualization purposes
stkRoot.ExecuteCommand(f'VectorTool * CentralBody/Sun Create System Syst_SEM_L2 "Assembled" "CentralBody/Sun SEM_L2" "CentralBody/Sun SEM_L2"')

# Create and show planes in the 3D graphics window
stkRoot.ExecuteCommand(f'VO * SetVectorGeometry Add "CentralBody/Sun Syst_SEM_L2.Axes Axes"') # Create Axes
stkRoot.ExecuteCommand(f'VO * SetVectorGeometry Modify "CentralBody/Sun Syst_SEM_L2.Axes Axes" Show Off Color cyan ShowLabel On DrawAtCB On RefCrdn "CentralBody/Sun Syst_SEM_L2.Axes Axes" OriginPointDef "CentralBody/Sun SEM_L2 Point"') # Set Axes properties

# Create and show planes
stkRoot.ExecuteCommand(f'VO * SetVectorGeometry Add "CentralBody/Sun Syst_SEM_L2.XZ Plane" Show On Color gray ShowLabel On DrawAtObject Off Translucent On Translucency 0.3 ShowLabel Off ShowAxisLabel On PlaneSize 10')
stkRoot.ExecuteCommand(f'VO * SetVectorGeometry Add "CentralBody/Sun Syst_SEM_L2.YZ Plane" Show On Color gray ShowLabel On DrawAtObject Off Translucent On Translucency 0.3 ShowLabel Off ShowAxisLabel On PlaneSize 10')

# Set vector geometry scale for better visibility
stkRoot.ExecuteCommand(f'VO * SetVectorGeometry Data Scale 10') # Set scale to 10x for better visibility

# Set 3D Graphics Window max visible distance to 1e12 km for 3D graphics Window 1 (setting in meters)
stkRoot.ExecuteCommand(f'VO * Clipping Far 1e15 1') 

# %% Set up Components for Target Sequence Results
stkRoot.ExecuteCommand(f'ComponentBrowser */ Duplicate "Calculation Objects" Vx "Vx_L2"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ SetValue "Calculation Objects" "Vx_L2" CoordSystem "CentralBody/Sun Syst_SEM_L2"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ Duplicate "Calculation Objects" Vy "Vy_L2"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ SetValue "Calculation Objects" "Vy_L2" CoordSystem "CentralBody/Sun Syst_SEM_L2"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ Duplicate "Calculation Objects" Vz "Vz_L2"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ SetValue "Calculation Objects" "Vz_L2" CoordSystem "CentralBody/Sun Syst_SEM_L2"')

stkRoot.ExecuteCommand(f'ComponentBrowser */ Duplicate "Calculation Objects" X "X_L2"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ SetValue "Calculation Objects" "X_L2" CoordSystem "CentralBody/Sun Syst_SEM_L2"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ Duplicate "Calculation Objects" Y "Y_L2"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ SetValue "Calculation Objects" "Y_L2" CoordSystem "CentralBody/Sun Syst_SEM_L2"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ Duplicate "Calculation Objects" Z "Z_L2"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ SetValue "Calculation Objects" "Z_L2" CoordSystem "CentralBody/Sun Syst_SEM_L2"')

# %% Add a satellite object
print('Adding satellite objects...')
# satName = 'JWST'
JWSTephemerisFilePath = r'D:\Max\Uni\03-SpaceSystems\03-3. Semester\Semesterarbeit\code\horizon-to-STK\data\2025-11-06_horizons_JWST_hourly_from-launch.e'
JWST = add_satellite_external_ephemeris(scenario, 'JWST', JWSTephemerisFilePath)

# %% Set up Base Satellite
base_separation_epoch = "6 Oct 2022 06:54:04.908 UTCG"
# Add Base Satellite with Astrogator Propagator
Base = scenario.Children.New(AgESTKObjectType.eSatellite, 'Base')

# Set attitude to fixed to Sun Syst_SEM_L2
Base.Attitude.Basic.SetProfileType(AgEVeProfile.eProfileFixedInAxes) # Set attitude to Fixed in Axes
Base.Attitude.Basic.Profile.ReferenceAxes = 'CentralBody/Sun Syst_SEM_L2.Axes' # Set reference axes to L2 assembled system

Base.SetPropagatorType(AgEVePropagatorType.ePropagatorAstrogator)
Base.Propagator.MainSequence.RemoveAll() # Clear default segments
# Add follow segment
Base.Propagator.MainSequence.Insert(AgEVASegmentType.eVASegmentTypeFollow, 'Follow', '-') # Insert at the beginning
# command = f"Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Follow.Leader JWST"
# Have not figured out how to do the following using the python API, therefore using STK Connect Command
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Follow.Leader JWST') # Set leader to JWST
# stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Follow.Xoffset 1 m') # 1 meter offset in X
# Stop at specific epoch
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Follow.StoppingConditions Epoch') # Set stopping condition to Epoch
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Follow.StoppingConditions.Epoch.TripValue "{base_separation_epoch}"') # Set stopping epoch

# Create basic stable 4-crossing target setup
# Insert Target Sequence segment at end of Main Sequence
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base InsertSegment MainSequence.SegmentList.- Target_Sequence')

# Add a maneuver and set it up
# Insert Maneuver segment into Target Sequence
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base InsertSegment MainSequence.SegmentList.Target_Sequence.SegmentList.- Maneuver')
# Configure maneuver properties
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Maneuver.MnvrType Impulsive')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Maneuver.AttitudeControl Thrust Vector')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Maneuver.ImpulsiveMnvr.ThrustAxes "CentralBody/Sun Syst_SEM_L2.Axes"')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Maneuver.Propagator "Earth Default High Fidelity v13"')
# Set up control parameters for target sequence
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base AddMCSSegmentControl MainSequence.SegmentList.Target_Sequence.SegmentList.Maneuver ImpulsiveMnvr.Cartesian.X')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base AddMCSSegmentControl MainSequence.SegmentList.Target_Sequence.SegmentList.Maneuver ImpulsiveMnvr.Cartesian.Y')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base AddMCSSegmentControl MainSequence.SegmentList.Target_Sequence.SegmentList.Maneuver ImpulsiveMnvr.Cartesian.Z')

# Add return segment and set it up
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base InsertSegment MainSequence.SegmentList.Target_Sequence.SegmentList.- Return')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.return.RetState Enable (except Profiles bypass)')

# Add propagate for 30 days segment 1
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base InsertSegment MainSequence.SegmentList.Target_Sequence.SegmentList.- Propagate')
Base.Propagator.MainSequence.Item(1).Segments.Item(2).Name = "Prop_1"
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_1.Propagator "Earth Default High Fidelity v13"')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_1.StoppingConditions Duration') # Set stopping condition to Duration
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_1.StoppingConditions.Duration.TripValue 30 Day') # Set duration to 30 days
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_1.SegmentColor 65535')

# Add Propagate to XZ crossing segment 1
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base InsertSegment MainSequence.SegmentList.Target_Sequence.SegmentList.- Propagate')
Base.Propagator.MainSequence.Item(1).Segments.Item(3).Name = "Prop_to_XZ_1"
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_1.Propagator "Earth Default High Fidelity v13"') # Set propagator to "Earth Default High Fidelity v13"
# set color of propagate segment for better visibility
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_1.SegmentColor 65535')
# Set stopping condition to Z-X Plane Crossing
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_1.StoppingConditions Z-X_Plane_Cross')
# Set coordinate system for plane crossing to L2 assembled system
Base.Propagator.MainSequence.Item(1).Segments.Item("Prop_to_XZ_1").StoppingConditions.Item(0).Properties.CoordSystem = 'CentralBody/Sun Syst_SEM_L2'

# Add three more pairs of propagate segments (2, 3, 4) with differential correctors

# ===== PROPAGATE PAIR 2 (Cyan) =====
# Add propagate for 30 days segment 2
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base InsertSegment MainSequence.SegmentList.Target_Sequence.SegmentList.- Propagate')
Base.Propagator.MainSequence.Item(1).Segments.Item(4).Name = "Prop_2"
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_2.Propagator "Earth Default High Fidelity v13"')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_2.StoppingConditions Duration')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_2.StoppingConditions.Duration.TripValue 30 Day')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_2.SegmentColor 16776960')  # Cyan

# Add propagate to XZ crossing segment 2
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base InsertSegment MainSequence.SegmentList.Target_Sequence.SegmentList.- Propagate')
Base.Propagator.MainSequence.Item(1).Segments.Item(5).Name = "Prop_to_XZ_2"
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_2.Propagator "Earth Default High Fidelity v13"')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_2.SegmentColor 16776960')  # Cyan
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_2.StoppingConditions Z-X_Plane_Cross')
Base.Propagator.MainSequence.Item(1).Segments.Item("Prop_to_XZ_2").StoppingConditions.Item(0).Properties.CoordSystem = 'CentralBody/Sun Syst_SEM_L2'
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_2.Results Vx_L2')

# ===== PROPAGATE PAIR 3 (Yellow) =====
# Add propagate for 30 days segment 3
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base InsertSegment MainSequence.SegmentList.Target_Sequence.SegmentList.- Propagate')
Base.Propagator.MainSequence.Item(1).Segments.Item(6).Name = "Prop_3"
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_3.Propagator "Earth Default High Fidelity v13"')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_3.StoppingConditions Duration')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_3.StoppingConditions.Duration.TripValue 30 Day')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_3.SegmentColor 65535')  # Yellow

# Add propagate to XZ crossing segment 3
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base InsertSegment MainSequence.SegmentList.Target_Sequence.SegmentList.- Propagate')
Base.Propagator.MainSequence.Item(1).Segments.Item(7).Name = "Prop_to_XZ_3"
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_3.Propagator "Earth Default High Fidelity v13"')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_3.SegmentColor 65535')  # Yellow
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_3.StoppingConditions Z-X_Plane_Cross')
Base.Propagator.MainSequence.Item(1).Segments.Item("Prop_to_XZ_3").StoppingConditions.Item(0).Properties.CoordSystem = 'CentralBody/Sun Syst_SEM_L2'
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_3.Results Vx_L2')

# ===== PROPAGATE PAIR 4 (Cyan) =====
# Add propagate for 30 days segment 4
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base InsertSegment MainSequence.SegmentList.Target_Sequence.SegmentList.- Propagate')
Base.Propagator.MainSequence.Item(1).Segments.Item(8).Name = "Prop_4"
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_4.Propagator "Earth Default High Fidelity v13"')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_4.StoppingConditions Duration')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_4.StoppingConditions.Duration.TripValue 30 Day')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_4.SegmentColor 16776960')  # Cyan

# Add propagate to XZ crossing segment 4
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base InsertSegment MainSequence.SegmentList.Target_Sequence.SegmentList.- Propagate')
Base.Propagator.MainSequence.Item(1).Segments.Item(9).Name = "Prop_to_XZ_4"
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_4.Propagator "Earth Default High Fidelity v13"')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_4.SegmentColor 16776960')  # Cyan
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_4.StoppingConditions Z-X_Plane_Cross')
Base.Propagator.MainSequence.Item(1).Segments.Item("Prop_to_XZ_4").StoppingConditions.Item(0).Properties.CoordSystem = 'CentralBody/Sun Syst_SEM_L2'
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_4.Results Vx_L2')

# Add a single 2 year propagate segment at the end of the main sequence

stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base InsertSegment MainSequence.SegmentList.- Propagate')
Base.Propagator.MainSequence.Item(2).Name = "Prop_2yr"
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Prop_2yr.Propagator "Earth Default High Fidelity v13"') 
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Prop_2yr.StoppingConditions Duration')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Prop_2yr.StoppingConditions.Duration.TripValue 2 Years')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Prop_2yr.SegmentColor 16777215')  # White

# Set up Target Sequence Results and Differential Corrector
# Set action to run active profiles
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.Action Run active profiles')

# Set results
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_1.Results Vx_L2')

# Set up four Differential Correctors for the four crossings

# Initialize all four Differential Correctors at once
stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.Profiles Differential_Corrector Differential_Corrector Differential_Corrector Differential_Corrector')

# Define DC configuration for each crossing
dc_configs = [
    {'name': 'DC_XZ_1', 'segment': 'Prop_to_XZ_1', 'index': 0},
    {'name': 'DC_XZ_2', 'segment': 'Prop_to_XZ_2', 'index': 1},
    {'name': 'DC_XZ_3', 'segment': 'Prop_to_XZ_3', 'index': 2},
    {'name': 'DC_XZ_4', 'segment': 'Prop_to_XZ_4', 'index': 3},
]

# Configure each Differential Corrector
for config in dc_configs:
    dc_name = config['name']
    segment_name = config['segment']
    dc_index = config['index']
    
    # Rename the profile
    Base.Propagator.MainSequence.Item(1).Profiles.Item(dc_index).Name = dc_name
    
    # Set controlled parameters active
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetMCSControlValue MainSequence.SegmentList.Target_Sequence.Profiles.{dc_name} Maneuver ImpulsiveMnvr.Cartesian.X Active True')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetMCSControlValue MainSequence.SegmentList.Target_Sequence.Profiles.{dc_name} Maneuver ImpulsiveMnvr.Cartesian.Y Active True')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetMCSControlValue MainSequence.SegmentList.Target_Sequence.Profiles.{dc_name} Maneuver ImpulsiveMnvr.Cartesian.Z Active True')
    
    # Set Scaling for Controls
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.Profiles.{dc_name}.ScaleControls By tolerance')
    for i in range(Base.Propagator.MainSequence.Item(1).Profiles.Item(dc_index).ControlParameters.Count):
        Base.Propagator.MainSequence.Item(1).Profiles.Item(dc_index).ControlParameters.Item(i).Perturbation = 0.00001
        Base.Propagator.MainSequence.Item(1).Profiles.Item(dc_index).ControlParameters.Item(i).MaxStep = 0.0001
    
    # Set Constraint Active (target Vx_L2)
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetMCSConstraintValue MainSequence.SegmentList.Target_Sequence.Profiles.{dc_name} {segment_name} Vx_L2 Active True')
    
    # Set Scaling for Goals
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.Profiles.{dc_name}.ScaleGoals By tolerance')

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

# Set up Components for Base Satellite Coordinate System Results
stkRoot.ExecuteCommand(f'ComponentBrowser */ Duplicate "Calculation Objects" Vx "Vx_Base"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ SetValue "Calculation Objects" "Vx_Base" CoordSystem "CentralBody/Sun Syst_Base_L2"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ Duplicate "Calculation Objects" Vy "Vy_Base"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ SetValue "Calculation Objects" "Vy_Base" CoordSystem "CentralBody/Sun Syst_Base_L2"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ Duplicate "Calculation Objects" Vz "Vz_Base"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ SetValue "Calculation Objects" "Vz_Base" CoordSystem "CentralBody/Sun Syst_Base_L2"')

stkRoot.ExecuteCommand(f'ComponentBrowser */ Duplicate "Calculation Objects" X "X_Base"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ SetValue "Calculation Objects" "X_Base" CoordSystem "CentralBody/Sun Syst_Base_L2"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ Duplicate "Calculation Objects" Y "Y_Base"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ SetValue "Calculation Objects" "Y_Base" CoordSystem "CentralBody/Sun Syst_Base_L2"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ Duplicate "Calculation Objects" Z "Z_Base"')
stkRoot.ExecuteCommand(f'ComponentBrowser */ SetValue "Calculation Objects" "Z_Base" CoordSystem "CentralBody/Sun Syst_Base_L2"')

# %% Set up Follower Satellite
# Arguments to pass to helper function
satellite_name = 'Follower'
leader_satellite_name = 'Base'
separation_epoch = epoch_seconds_to_time_string(scenario, time_string_to_epoch_seconds(scenario, base_separation_epoch) + 600)  # 1 minute after Base separation
x_offset_m = 100.0 # offset in X
y_offset_m = 0.0 # offset in Y
z_offset_m = 0.0 # offset in Z
repeat_interval = 7 # 7 days
# Add Follower Satellite with Astrogator Propagator
Follower = scenario.Children.New(AgESTKObjectType.eSatellite, satellite_name)
Follower.SetPropagatorType(AgEVePropagatorType.ePropagatorAstrogator)
Follower.Propagator.MainSequence.RemoveAll() # Clear default segments
# Set View to the L2 Assembled System (need to do this after creating all satellites)
stkRoot.ExecuteCommand(f'VO */Satellite/{satellite_name} OrbitSystem Add System "CentralBody/Sun Syst_SEM_L2" WindowID All')
stkRoot.ExecuteCommand(f'VO */Satellite/{satellite_name} OrbitSystem Modify System "InertialByWindow" WindowID All Show Off')

# Add follow segment
Follower.Propagator.MainSequence.Insert(AgEVASegmentType.eVASegmentTypeFollow, 'Follow', '-') # Insert at the beginning
# Set leader to Base
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Follow.Leader {leader_satellite_name}') # Set leader to Base
# Set offsets
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Follow.Xoffset {x_offset_m} m') # X offset
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Follow.Yoffset {y_offset_m} m') # Y offset
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Follow.Zoffset {z_offset_m} m') # Z offset
# Stop at specific epoch
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Follow.StoppingConditions Epoch') # Set stopping condition to Epoch
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Follow.StoppingConditions.Epoch.TripValue "{separation_epoch}"') # Set stopping epoch
# set color to white
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Follow.SegmentColor 16777215')  # White
# %% Set up repeating Sequence

stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} InsertSegment MainSequence.SegmentList.- Sequence')
# Add repeating sequence to repeat for at least 180 days (~1 orbit)
repeat_count = int(180 / repeat_interval)+1  # Repeat to cover at least 6 months
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.RepeatCount {repeat_count}')  # Repeat 1000 times

# Add Target_Sequence segment inside Sequence
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} InsertSegment MainSequence.SegmentList.Sequence.SegmentList.- Target_Sequence')

# Add Maneuver segment to Target_Sequence
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} InsertSegment MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.- Maneuver')
# Configure maneuver properties: Impulsive, Thrust Vector, Earth Default High Fidelity v13
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Maneuver.MnvrType Impulsive')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Maneuver.AttitudeControl Thrust Vector')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Maneuver.ImpulsiveMnvr.ThrustAxes "CentralBody/Sun Syst_SEM_L2.Axes"')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Maneuver.Propagator "Earth Default High Fidelity v13"')
# Set up control parameters for target sequence
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} AddMCSSegmentControl MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Maneuver ImpulsiveMnvr.Cartesian.X')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} AddMCSSegmentControl MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Maneuver ImpulsiveMnvr.Cartesian.Y')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} AddMCSSegmentControl MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Maneuver ImpulsiveMnvr.Cartesian.Z')

# Add propagate segment to Target_Sequence
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} InsertSegment MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.- Propagate')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Propagate.Propagator "Earth Default High Fidelity v13"')
# Set Propagate Time to repeat interval
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Propagate.StoppingConditions Duration')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Propagate.StoppingConditions.Duration.TripValue {repeat_interval} Day')

# Set up Target Sequence Results and Differential Corrector
# Set action to run active profiles
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Action Run active profiles')
# Set results
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Propagate.Results X_Base Y_Base Z_Base')
# Set up Differential Corrector
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles Differential_Corrector')
# Set controlled parameters active
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSControlValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector Maneuver ImpulsiveMnvr.Cartesian.X Active True')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSControlValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector Maneuver ImpulsiveMnvr.Cartesian.Y Active True')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSControlValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector Maneuver ImpulsiveMnvr.Cartesian.Z Active True')

# Set goal values for X, Y, Z offsets (convert m to km)
x_offset_km = x_offset_m / 1000
y_offset_km = y_offset_m / 1000
z_offset_km = z_offset_m / 1000
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSConstraintValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector Propagate X_Base Desired {x_offset_km} km')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSConstraintValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector Propagate Y_Base Desired {y_offset_km} km')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSConstraintValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector Propagate Z_Base Desired {z_offset_km} km')
# Set tolerance to 1cm
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSConstraintValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector Propagate X_Base Tolerance 0.01 m')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSConstraintValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector Propagate Y_Base Tolerance 0.01 m')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSConstraintValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector Propagate Z_Base Tolerance 0.01 m')

# Set scaling for controls and goals
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector.ScaleControls By tolerance')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector.ScaleGoals By tolerance')
for i in range(Follower.Propagator.MainSequence.Item(1).Segments.Item(0).Profiles.Item(0).ControlParameters.Count):
    Follower.Propagator.MainSequence.Item(1).Segments.Item(0).Profiles.Item(0).ControlParameters.Item(i).Perturbation = 0.00001
    Follower.Propagator.MainSequence.Item(1).Segments.Item(0).Profiles.Item(0).ControlParameters.Item(i).MaxStep = 0.0001

# Set Goals to active
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSConstraintValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector Propagate X_Base Active True')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSConstraintValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector Propagate Y_Base Active True')
stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSConstraintValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector Propagate Z_Base Active True')

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
