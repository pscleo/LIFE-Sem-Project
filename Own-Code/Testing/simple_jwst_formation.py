"""Three freely coasting spacecraft, initialised from the supplied JWST ephemeris.

Requires Windows, STK 13 with Astrogator/Analysis Workbench, and agi.stk13.
Run the whole file, or use the # %% sections individually in VS Code.
"""

# %% Imports
import os
from datetime import datetime, timedelta
from pathlib import Path

if os.name != 'nt':
    raise SystemExit('Run this script on Windows with STK Desktop installed.')

from agi.stk13.stkdesktop import STKDesktop
from agi.stk13.stkobjects import AgESTKObjectType, AgEVePropagatorType, AgEVeProfile
from agi.stk13.stkobjects.astrogator import AgEVASegmentType, AgEVAElementType

# %% User configuration
folder = Path(__file__).resolve().parent
ephemeris_file = folder / '2025-11-06_horizons_JWST_hourly_from-launch.e'
start_time = '6 Oct 2022 07:00:00.000'  # Same Base departure epoch as the previous project
duration_days = 30
separation_m = 300.0  # Distance BETWEEN the two outer spacecraft at the start
propagator_name = 'Earth Default High Fidelity v13'  # Same component as the previous project

if not ephemeris_file.is_file():
    raise FileNotFoundError(f'Place the supplied JWST .e file beside this script: {ephemeris_file}')
if duration_days <= 0 or separation_m <= 0:
    raise ValueError('duration_days and separation_m must be positive.')

start_date = datetime.strptime(start_time, '%d %b %Y %H:%M:%S.%f')
stop_time = (start_date + timedelta(days=duration_days)).strftime('%d %b %Y %H:%M:%S.%f')[:-3]

# %% Start a new STK application and create the scenario
stk = STKDesktop.StartApplication(visible=True, userControl=True)
stkRoot = stk.Root
stkRoot.NewScenario('JWST_Three_Spacecraft_No_SK')
scenario = stkRoot.CurrentScenario

stkRoot.UnitPreferences.ResetUnits()
stkRoot.UnitPreferences.SetCurrentUnit('DateFormat', 'UTCG')
stkRoot.UnitPreferences.SetCurrentUnit('DistanceUnit', 'km')
stkRoot.UnitPreferences.SetCurrentUnit('TimeUnit', 'sec')
stkRoot.ExecuteCommand('SetUnits / km')  # Connect commands have their own unit preferences
scenario.SetTimePeriod(start_time, stop_time)
scenario.Epoch = start_time
stkRoot.Rewind()

# %% Create the same rotating L2 coordinate system as the previous project
# Origin: Sun/Earth-Moon L2. Axes: STK's built-in SEM_L2 axes.
# X points along the Sun-to-L2 direction; Z is normal to the associated orbital plane.
stkRoot.ExecuteCommand('VectorTool * CentralBody/Sun Create System Syst_SEM_L2 "Assembled" "CentralBody/Sun SEM_L2" "CentralBody/Sun SEM_L2"')
l2_system = stkRoot.CentralBodies.Sun.Vgt.Systems.Item('Syst_SEM_L2')

# %% Read JWST's position and velocity at the start time
# JWST is a temporary reference only. It will be removed after reading its state.
print('Reading the JWST ephemeris...')
jwst = scenario.Children.New(AgESTKObjectType.eSatellite, 'JWST_Reference')
jwst.SetPropagatorType(AgEVePropagatorType.ePropagatorStkExternal)
jwst.Propagator.Filename = str(ephemeris_file)
jwst.Propagator.Propagate()

jwst_state = jwst.Vgt.Points.Item('Center').LocateInSystemWithRate(start_time, l2_system)
if not jwst_state.IsValid:
    raise RuntimeError('The JWST state is unavailable. Choose a start time within the supplied ephemeris.')
position = jwst_state.Position.ToArray()
velocity = jwst_state.Velocity.ToArray()
jwst.Unload()

# %% Create and propagate the three spacecraft
# Equal velocity components in the rotating L2 frame mean zero initial relative velocity there.
# These are INITIAL offsets only. No segment holds the spacecraft at these offsets.
spacecraft = [('Base', 0.0, 'white'), ('X_Minus', -separation_m / 2, 'cyan'), ('X_Plus', separation_m / 2, 'yellow')]

for name, x_offset_m, colour in spacecraft:
    print(f'Creating {name}: initial x offset = {x_offset_m:+.1f} m')
    satellite = scenario.Children.New(AgESTKObjectType.eSatellite, name)
    satellite.SetPropagatorType(AgEVePropagatorType.ePropagatorAstrogator)
    mcs = satellite.Propagator.MainSequence
    mcs.RemoveAll()

    # Initial State: JWST state plus the selected X offset, converted from metres to km
    initial_state = mcs.Insert(AgEVASegmentType.eVASegmentTypeInitialState, 'Initial_State', '-')
    initial_state.SetElementType(AgEVAElementType.eVAElementTypeCartesian)
    initial_state.CoordSystemName = 'CentralBody/Sun Syst_SEM_L2'
    initial_state.OrbitEpoch = start_time
    initial_state.Element.X = position[0] + x_offset_m / 1000
    initial_state.Element.Y = position[1]
    initial_state.Element.Z = position[2]
    initial_state.Element.Vx = velocity[0]
    initial_state.Element.Vy = velocity[1]
    initial_state.Element.Vz = velocity[2]

    # Coast: propagate freely for the requested duration, with no manoeuvres or targeting
    coast = mcs.Insert(AgEVASegmentType.eVASegmentTypePropagate, 'Coast', '-')
    coast.PropagatorName = propagator_name
    coast.EnableMaxPropagationTime = False
    coast.StoppingConditions.Item('Duration').Properties.Trip = duration_days * 86400
    satellite.Propagator.RunMCS()

    # Align displayed body axes with L2 axes. This is attitude, not orbital station keeping.
    satellite.Attitude.Basic.SetProfileType(AgEVeProfile.eProfileFixedInAxes)
    satellite.Attitude.Basic.Profile.ReferenceAxes = 'CentralBody/Sun Syst_SEM_L2.Axes'

# %% Create a Base-centred frame for viewing relative motion
# This frame follows Base's centre but keeps the same rotating L2 axis directions.
stkRoot.ExecuteCommand('VectorTool * CentralBody/Sun Create System Syst_Base_L2 "Assembled" "Satellite/Base Center" "CentralBody/Sun SEM_L2"')
base_system = stkRoot.CentralBodies.Sun.Vgt.Systems.Item('Syst_Base_L2')

# Check the propagated initial offsets and that all three trajectories reach the stop time
print('\nInitial positions relative to Base [m]:')
for name, x_offset_m, colour in spacecraft:
    satellite = stkRoot.GetObjectFromPath(f'Satellite/{name}')
    centre = satellite.Vgt.Points.Item('Center')
    state = centre.LocateInSystemWithRate(start_time, base_system)
    final_state = centre.LocateInSystemWithRate(stop_time, base_system)
    if not state.IsValid or not final_state.IsValid:
        raise RuntimeError(f'{name}: the propagated trajectory does not cover the requested interval.')
    x, y, z = [value * 1000 for value in state.Position.ToArray()]
    if max(abs(x - x_offset_m), abs(y), abs(z)) > 0.01:
        raise RuntimeError(f'{name}: initial offset check failed: {x}, {y}, {z} m.')
    print(f'  {name:8s}: x = {x:+.3f}, y = {y:+.3f}, z = {z:+.3f}')

# %% Set up a close view of the formation
# Graphics are separate from the dynamics. A graphics warning does not invalidate propagation.
graphics_commands = []
for name, x_offset_m, colour in spacecraft:
    graphics_commands += [f'Graphics */Satellite/{name} SetColor {colour}',
        f'VO */Satellite/{name} Model Show Off',
        f'VO */Satellite/{name} Marker Show On MarkerType Line Shape Circle Size 8',
        f'VO */Satellite/{name} OrbitSystem Add System "CentralBody/Sun Syst_Base_L2" WindowID All',
        f'VO */Satellite/{name} OrbitSystem Modify System "InertialByWindow" WindowID All Show Off']
graphics_commands += ['VO * ViewFromTo Normal From Satellite/Base To Satellite/Base WindowID 1',
    'VO * View AddReferenceFrame "CentralBody/Sun SEM_L2 Axes" Object Satellite/Base',
    'VO * View SetReferenceFrame "CentralBody/Sun SEM_L2 Axes" WindowID 1',
    'VO * ViewFromTo Parameters Distance From 1 WindowID 1',
    'VO * ViewFromTo Reset WindowID 1']
for command in graphics_commands:
    try:
        stkRoot.ExecuteCommand(command)
    except Exception as error:
        print(f'Graphics warning: {command}\n  {error}')
stkRoot.Rewind()

# %% Save the scenario in a new folder beside this script
output_folder = folder / ('STK_scenario_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
output_folder.mkdir()
stkRoot.ExecuteCommand(f'Save / * "{output_folder}"')
print(f'\nScenario saved in: {output_folder}')
print('STK stays open. Use the animation controls to inspect the relative drift.')
print('Initial outer-spacecraft separation: %.1f m. No spacecraft has any SK manoeuvres.' % separation_m)
