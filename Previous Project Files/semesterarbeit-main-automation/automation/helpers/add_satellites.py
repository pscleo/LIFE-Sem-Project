"""
================================================================================
SATELLITE CREATION HELPER FUNCTIONS
================================================================================

Module: helpers/add_satellites.py
Purpose: STK satellite setup and Astrogator configuration utilities

FUNCTIONS
---------
add_satellite_external_ephemeris()           - Load satellite from ephemeris file
add_base_satellite_with_crossings()          - Create Base with N-crossing optimization
add_constellation_satellite_with_position_hold() - Create formation satellite with SK
set_constellation_attitudes()                - Configure attitudes for multiple satellites

KEY FEATURES
------------
✓ External ephemeris loading (JWST, etc.)
✓ Astrogator propagator setup
✓ Differential correction for orbit maintenance
✓ Position-hold station-keeping with configurable intervals
✓ XZ plane crossing detection and optimization
✓ Repeating sequence generation
✓ Batch attitude configuration

WORKFLOW
--------
1. add_satellite_external_ephemeris() → Load JWST reference
2. add_base_satellite_with_crossings() → Create Base satellite
3. add_constellation_satellite_with_position_hold() → Create constellation sats
4. set_constellation_attitudes() → Configure all attitudes (optional)

USAGE
-----
from helpers.add_satellites import (
    add_satellite_external_ephemeris,
    add_base_satellite_with_crossings,
    add_constellation_satellite_with_position_hold
)

# Load reference satellite
JWST = add_satellite_external_ephemeris(scenario, 'JWST', ephemeris_path)

# Create Base with 4 plane crossings
Base = add_base_satellite_with_crossings(
    scenario, stkRoot, 'Base', 'JWST',
    separation_epoch="6 Oct 2022 07:00:00.000 UTCG",
    num_crossings=4
)

# Create constellation satellite with 7-day SK
Sat = add_constellation_satellite_with_position_hold(
    scenario, stkRoot, 'Octahedron_SK7d_Xp1000m', 'Base',
    separation_epoch="6 Oct 2022 07:10:00.000 UTCG",
    x_offset_m=1000.0, station_keeping_interval_days=7
)

================================================================================
"""

from agi.stk13.stkobjects import *
from agi.stk13.stkobjects.astrogator import *


def add_satellite_external_ephemeris(scenario, name, ephemeris_filepath, verbose=False):
    """
    Add a satellite to a scenario using external ephemeris data.
    
    Parameters
    ----------
    scenario : IAgScenario
        The STK scenario object to add the satellite to
    name : str
        The name of the satellite object
    ephemeris_filepath : str
        Full file path to the ephemeris file (e.g., .e file)
    verbose : bool, optional
        Print status messages during execution (default: False)
    
    Returns
    -------
    IAgSatellite
        The newly created satellite object
    
    Raises
    ------
    Exception
        If the ephemeris file cannot be loaded or propagated
    """
    try:
        # Create satellite object
        satellite = scenario.Children.New(AgESTKObjectType.eSatellite, name)
        if verbose:
            print(f'Satellite object created: {name}')
        
        # Configure external propagator
        satellite.SetPropagatorType(AgEVePropagatorType.ePropagatorStkExternal)
        satellite.Propagator.Filename = ephemeris_filepath
        satellite.Propagator.Propagate()
        
        if verbose:
            print(f'Successfully loaded ephemeris file:\n  {ephemeris_filepath}')
        
        return satellite
        
    except Exception as exception:
        print(f'Error loading ephemeris for {name}: {str(exception)}')
        raise


def add_constellation_satellite_with_position_hold(
    scenario,
    stkRoot,
    satellite_name,
    leader_satellite_name,
    separation_epoch,
    x_offset_m=0.0,
    y_offset_m=0.0,
    z_offset_m=0.0,
    station_keeping_interval_days=7,
    repeat_count=None,
    verbose=False
):
    """
    Add a constellation satellite that follows a leader satellite and maintains relative position.
    
    Parameters
    ----------
    scenario : IAgScenario
        The STK scenario object
    stkRoot : IAgStkObjectRoot
        The STK root object for executing commands
    satellite_name : str
        Name for the constellation satellite
    leader_satellite_name : str
        Name of the leader satellite to follow
    separation_epoch : str
        Epoch when satellite separates from leader (format: 'DD MMM YYYY HH:MM:SS.fff UTCG')
    x_offset_m : float, optional
        Desired X offset from leader in meters, in leader body frame (default: 0.0)
    y_offset_m : float, optional
        Desired Y offset from leader in meters, in leader body frame (default: 0.0)
    z_offset_m : float, optional
        Desired Z offset from leader in meters, in leader body frame (default: 0.0)
    station_keeping_interval_days : int, optional
        Station-keeping (position relative to leader satellite) interval in days (default: 7)
    repeat_count : int, optional
        Number of station-keeping maneuvers (default: calculated for ~180 days)
    verbose : bool, optional
        Print status messages (default: False)
    
    Returns
    -------
    IAgSatellite
        The newly created constellation satellite object
    """
    
    if verbose:
        print(f'Creating constellation satellite: {satellite_name}')
    
    # Calculate repeat count if not provided
    if repeat_count is None:
        repeat_count = int(180 / station_keeping_interval_days) + 1
    
    # Add Follower Satellite with Astrogator Propagator
    satellite = scenario.Children.New(AgESTKObjectType.eSatellite, satellite_name)
    satellite.SetPropagatorType(AgEVePropagatorType.ePropagatorAstrogator)
    satellite.Propagator.MainSequence.RemoveAll()

    # Set attitude to fixed to Sun Syst_SEM_L2
    satellite.Attitude.Basic.SetProfileType(AgEVeProfile.eProfileFixedInAxes)
    satellite.Attitude.Basic.Profile.ReferenceAxes = 'CentralBody/Sun Syst_SEM_L2.Axes'
    
    # Set View to the L2 Assembled System
    stkRoot.ExecuteCommand(f'VO */Satellite/{satellite_name} OrbitSystem Add System "CentralBody/Sun Syst_SEM_L2" WindowID All')
    stkRoot.ExecuteCommand(f'VO */Satellite/{satellite_name} OrbitSystem Modify System "InertialByWindow" WindowID All Show Off')
    
    # Add follow segment
    satellite.Propagator.MainSequence.Insert(AgEVASegmentType.eVASegmentTypeFollow, 'Follow', '-')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Follow.Leader {leader_satellite_name}')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Follow.Xoffset {x_offset_m} m')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Follow.Yoffset {y_offset_m} m')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Follow.Zoffset {z_offset_m} m')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Follow.StoppingConditions Epoch')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Follow.StoppingConditions.Epoch.TripValue "{separation_epoch}"')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Follow.SegmentColor 16777215')
    
    # Add repeating Sequence
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} InsertSegment MainSequence.SegmentList.- Sequence')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.RepeatCount {repeat_count}')
    
    # Add Target_Sequence inside Sequence
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} InsertSegment MainSequence.SegmentList.Sequence.SegmentList.- Target_Sequence')
    
    # Add Maneuver segment to Target_Sequence
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} InsertSegment MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.- Maneuver')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Maneuver.MnvrType Impulsive')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Maneuver.AttitudeControl Thrust Vector')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Maneuver.ImpulsiveMnvr.ThrustAxes "CentralBody/Sun Syst_SEM_L2.Axes"')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Maneuver.Propagator "Earth Default High Fidelity v13"')
    
    # Set up control parameters
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} AddMCSSegmentControl MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Maneuver ImpulsiveMnvr.Cartesian.X')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} AddMCSSegmentControl MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Maneuver ImpulsiveMnvr.Cartesian.Y')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} AddMCSSegmentControl MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Maneuver ImpulsiveMnvr.Cartesian.Z')
    
    # Add propagate segment to Target_Sequence
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} InsertSegment MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.- Propagate')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Propagate.Propagator "Earth Default High Fidelity v13"')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Propagate.StoppingConditions Duration')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Propagate.StoppingConditions.Duration.TripValue {station_keeping_interval_days} Day')
    
    # Set up Target Sequence Results and Differential Corrector
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Action Run active profiles')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.SegmentList.Propagate.Results X_Base Y_Base Z_Base')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles Differential_Corrector')
    
    # Set controlled parameters active
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSControlValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector Maneuver ImpulsiveMnvr.Cartesian.X Active True')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSControlValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector Maneuver ImpulsiveMnvr.Cartesian.Y Active True')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSControlValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector Maneuver ImpulsiveMnvr.Cartesian.Z Active True')
    
    # Set goal values (convert m to km)
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
    
    for i in range(satellite.Propagator.MainSequence.Item(1).Segments.Item(0).Profiles.Item(0).ControlParameters.Count):
        satellite.Propagator.MainSequence.Item(1).Segments.Item(0).Profiles.Item(0).ControlParameters.Item(i).Perturbation = 0.00001
        satellite.Propagator.MainSequence.Item(1).Segments.Item(0).Profiles.Item(0).ControlParameters.Item(i).MaxStep = 0.0001
    
    # Set Goals to active
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSConstraintValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector Propagate X_Base Active True')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSConstraintValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector Propagate Y_Base Active True')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSConstraintValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Profiles.Differential_Corrector Propagate Z_Base Active True')
    
    if verbose:
        print(f'Constellation satellite {satellite_name} created successfully')
        print(f'  Leader: {leader_satellite_name}')
        print(f'  Separation epoch: {separation_epoch}')
        print(f'  Target offset: ({x_offset_m}, {y_offset_m}, {z_offset_m}) m')
        print(f'  Station-keeping interval: {station_keeping_interval_days} days')
    
    return satellite


def add_base_satellite_with_crossings(
    scenario,
    stkRoot,
    satellite_name,
    leader_satellite_name,
    separation_epoch,
    num_crossings=4,
    min_propagate_duration=30,
    verbose=False
):
    """
    Add a base satellite that follows a leader and performs N-crossing orbit maintenance.
    
    Parameters
    ----------
    scenario : IAgScenario
        The STK scenario object
    stkRoot : IAgStkObjectRoot
        The STK root object for executing commands
    satellite_name : str
        Name for the base satellite
    leader_satellite_name : str
        Name of the leader satellite to follow
    separation_epoch : str
        Epoch when satellite separates from leader (format: 'DD MMM YYYY HH:MM:SS.fff UTCG')
    num_crossings : int, optional
        Number of XZ plane crossings to optimize (default: 4)
    min_propagate_duration : int, optional
        Minimum propagate duration to avoid premature segment termination with the XZ-crossing detection (default: 30)
    verbose : bool, optional
        Print status messages (default: False)
    
    Returns
    -------
    IAgSatellite
        The newly created base satellite object
    """
    
    if verbose:
        print(f'Creating base satellite: {satellite_name}')
        print(f'  Number of crossings: {num_crossings}')
        print(f'  Crossing interval: {min_propagate_duration} days')
    
    # Add Base Satellite with Astrogator Propagator
    satellite = scenario.Children.New(AgESTKObjectType.eSatellite, satellite_name)
    
    # Set attitude to fixed to Sun Syst_SEM_L2
    satellite.Attitude.Basic.SetProfileType(AgEVeProfile.eProfileFixedInAxes)
    satellite.Attitude.Basic.Profile.ReferenceAxes = 'CentralBody/Sun Syst_SEM_L2.Axes'
    
    satellite.SetPropagatorType(AgEVePropagatorType.ePropagatorAstrogator)
    satellite.Propagator.MainSequence.RemoveAll()
    
    # Add follow segment
    satellite.Propagator.MainSequence.Insert(AgEVASegmentType.eVASegmentTypeFollow, 'Follow', '-')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Follow.Leader {leader_satellite_name}')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Follow.StoppingConditions Epoch')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Follow.StoppingConditions.Epoch.TripValue "{separation_epoch}"')
    
    # Insert Target Sequence segment
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} InsertSegment MainSequence.SegmentList.- Target_Sequence')
    
    # Add maneuver segment
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} InsertSegment MainSequence.SegmentList.Target_Sequence.SegmentList.- Maneuver')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Maneuver.MnvrType Impulsive')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Maneuver.AttitudeControl Thrust Vector')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Maneuver.ImpulsiveMnvr.ThrustAxes "CentralBody/Sun Syst_SEM_L2.Axes"')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Maneuver.Propagator "Earth Default High Fidelity v13"')
    
    # Set up control parameters
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} AddMCSSegmentControl MainSequence.SegmentList.Target_Sequence.SegmentList.Maneuver ImpulsiveMnvr.Cartesian.X')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} AddMCSSegmentControl MainSequence.SegmentList.Target_Sequence.SegmentList.Maneuver ImpulsiveMnvr.Cartesian.Y')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} AddMCSSegmentControl MainSequence.SegmentList.Target_Sequence.SegmentList.Maneuver ImpulsiveMnvr.Cartesian.Z')
    
    # Add return segment
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} InsertSegment MainSequence.SegmentList.Target_Sequence.SegmentList.- Return')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.return.RetState Enable (except Profiles bypass)')
    
    # Add N pairs of propagate segments with alternating colors
    colors = [65535, 16776960]  # Yellow, Cyan alternating
    
    for i in range(1, num_crossings + 1):
        color = colors[(i-1) % 2]
        
        # Add crossing interval propagate segment
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} InsertSegment MainSequence.SegmentList.Target_Sequence.SegmentList.- Propagate')
        # Correct indexing: For crossing i, this is segment at position (2 + 2*(i-1)) = 2*i
        satellite.Propagator.MainSequence.Item(1).Segments.Item(2*i).Name = f"Prop_{i}"
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_{i}.Propagator "Earth Default High Fidelity v13"')
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_{i}.StoppingConditions Duration')
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_{i}.StoppingConditions.Duration.TripValue {min_propagate_duration} Day')
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_{i}.SegmentColor {color}')
        
        # Add XZ crossing propagate segment  
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} InsertSegment MainSequence.SegmentList.Target_Sequence.SegmentList.- Propagate')
        # Correct indexing: For crossing i, this is segment at position (2 + 2*(i-1) + 1) = 2*i + 1
        satellite.Propagator.MainSequence.Item(1).Segments.Item(2*i + 1).Name = f"Prop_to_XZ_{i}"
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_{i}.Propagator "Earth Default High Fidelity v13"')
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_{i}.SegmentColor {color}')
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_{i}.StoppingConditions Z-X_Plane_Cross')
        satellite.Propagator.MainSequence.Item(1).Segments.Item(f"Prop_to_XZ_{i}").StoppingConditions.Item(0).Properties.CoordSystem = 'CentralBody/Sun Syst_SEM_L2'
        
        # Set results for all crossings
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_{i}.Results Vx_L2')
    
    # Add 2-year propagate segment at end of main sequence
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} InsertSegment MainSequence.SegmentList.- Propagate')
    satellite.Propagator.MainSequence.Item(2).Name = "Prop_2yr"
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Prop_2yr.Propagator "Earth Default High Fidelity v13"')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Prop_2yr.StoppingConditions Duration')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Prop_2yr.StoppingConditions.Duration.TripValue 2 Years')
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Prop_2yr.SegmentColor 16777215')  # White
    
    # Set up Target Sequence
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Target_Sequence.Action Run active profiles')
    
    # Initialize N Differential Correctors
    dc_list = ' '.join(['Differential_Corrector'] * num_crossings)
    stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Target_Sequence.Profiles {dc_list}')
    
    # Configure each Differential Corrector
    for i in range(num_crossings):
        dc_name = f'DC_XZ_{i+1}'
        segment_name = f'Prop_to_XZ_{i+1}'
        
        # Rename the profile
        satellite.Propagator.MainSequence.Item(1).Profiles.Item(i).Name = dc_name
        
        # Set controlled parameters active
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSControlValue MainSequence.SegmentList.Target_Sequence.Profiles.{dc_name} Maneuver ImpulsiveMnvr.Cartesian.X Active True')
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSControlValue MainSequence.SegmentList.Target_Sequence.Profiles.{dc_name} Maneuver ImpulsiveMnvr.Cartesian.Y Active True')
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSControlValue MainSequence.SegmentList.Target_Sequence.Profiles.{dc_name} Maneuver ImpulsiveMnvr.Cartesian.Z Active True')
        
        # Set scaling for controls
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Target_Sequence.Profiles.{dc_name}.ScaleControls By tolerance')
        for j in range(satellite.Propagator.MainSequence.Item(1).Profiles.Item(i).ControlParameters.Count):
            satellite.Propagator.MainSequence.Item(1).Profiles.Item(i).ControlParameters.Item(j).Perturbation = 0.00001
            satellite.Propagator.MainSequence.Item(1).Profiles.Item(i).ControlParameters.Item(j).MaxStep = 0.0001
        
        # Set constraint active (target Vx_L2)
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetMCSConstraintValue MainSequence.SegmentList.Target_Sequence.Profiles.{dc_name} {segment_name} Vx_L2 Active True')
        
        # Set scaling for goals
        stkRoot.ExecuteCommand(f'Astrogator */Satellite/{satellite_name} SetValue MainSequence.SegmentList.Target_Sequence.Profiles.{dc_name}.ScaleGoals By tolerance')
    
    if verbose:
        print(f'Base satellite {satellite_name} created successfully')
        print(f'  Leader: {leader_satellite_name}')
        print(f'  Separation epoch: {separation_epoch}')
        print(f'  {num_crossings}-crossing orbit maintenance configured')
        print(f'  {num_crossings} Differential Correctors set up for XZ plane crossings')
    
    return satellite

# Helper function to set attitudes for constellation satellites
# Should not have to be used, as this functionality is now integrated into add_constellation_satellite_with_position_hold
def set_constellation_attitudes(scenario, stkRoot, constellation_configs, reference_axes='CentralBody/Sun Syst_SEM_L2.Axes', verbose=True):
    """
    Set the attitude for all constellation satellites to be fixed in specified reference axes.
    
    Parameters
    ----------
    scenario : IAgScenario
        The STK scenario object
    stkRoot : IAgStkObjectRoot
        The STK root object
    constellation_configs : list
        List of constellation configuration dictionaries containing 'satellite_names'
    reference_axes : str, optional
        Reference axes for fixed attitude (default: 'CentralBody/Sun Syst_SEM_L2.Axes')
    verbose : bool, optional
        Print status messages (default: True)
    
    Returns
    -------
    int
        Total number of satellites configured
    """
    total_count = 0
    
    for config_idx, config in enumerate(constellation_configs):
        constellation_name = config.get('base_name', f'Constellation_{config_idx}')
        satellite_names = config.get('satellite_names', [])
        
        if verbose:
            print(f'\nSetting attitude for {constellation_name}:')
            print(f'  Reference axes: {reference_axes}')
            print(f'  Number of satellites: {len(satellite_names)}')
        
        for sat_name in satellite_names:
            try:
                # Get the satellite object
                satellite = scenario.Children.Item(sat_name)
                
                # Set attitude to fixed in reference axes
                satellite.Attitude.Basic.SetProfileType(AgEVeProfile.eProfileFixedInAxes)
                satellite.Attitude.Basic.Profile.ReferenceAxes = reference_axes
                
                if verbose:
                    print(f'  ✓ {sat_name}')
                
                total_count += 1
                
            except Exception as e:
                print(f'  ✗ {sat_name} - Error: {str(e)}')
    
    if verbose:
        print(f'\nTotal satellites configured: {total_count}')
    
    return total_count