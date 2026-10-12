"""
================================================================================
SCENARIO SETUP HELPER FUNCTIONS
================================================================================

Module: helpers/scenario_setup.py
Purpose: Core utilities for STK scenario initialization and time management

FUNCTIONS
---------
get_current_time_string()           - Retrieve current animation time as string
set_current_time()                  - Set animation time from formatted string
time_string_to_epoch_seconds()      - Convert time string to epoch seconds
epoch_seconds_to_time_string()      - Convert epoch seconds to time string
create_cartesian_coordinate_components()  - Set up position/velocity components
setup_l2_coordinate_system()        - Initialize L2 system with visualization

KEY FEATURES
------------
✓ Time conversions between strings and epoch seconds
✓ L2 coordinate system creation and graphics setup
✓ Cartesian component management (X, Y, Z, Vx, Vy, Vz)
✓ Verbose logging for debugging

USAGE
-----
from helpers.scenario_setup import setup_l2_coordinate_system, set_current_time

setup_l2_coordinate_system(stkRoot, verbose=True)
set_current_time(stkRoot, scenario, "6 Oct 2022 07:00:00.000 UTCG")

================================================================================
"""

from datetime import datetime, timedelta

def get_current_time_string(stkRoot, scenario):
    """
    Get the current animation time as a formatted string.
    
    Args:
        stkRoot: STK Root object
        scenario: STK Scenario object
        
    Returns:
        str: Current time in format 'DD MMM YYYY HH:MM:SS.fff'
    """
    # Get epoch time from scenario
    epoch_str = scenario.Epoch
    
    # Parse epoch string to datetime
    epoch_datetime = datetime.strptime(epoch_str, '%d %b %Y %H:%M:%S.%f')
    
    # Get current time in epoch seconds
    current_epoch_seconds = stkRoot.CurrentTime
    
    # Add epoch seconds to epoch datetime
    current_datetime = epoch_datetime + timedelta(seconds=current_epoch_seconds)
    
    # Format back to string
    return current_datetime.strftime('%d %b %Y %H:%M:%S.%f')[:-3]


def set_current_time(stkRoot, scenario, time_string):
    """
    Set the current animation time using a formatted string.
    
    Args:
        stkRoot: STK Root object
        scenario: STK Scenario object
        time_string: Time in format 'DD MMM YYYY HH:MM:SS.fff' or 'DD MMM YYYY HH:MM:SS.fff UTCG'
    """
    # Get epoch time from scenario
    epoch_str = scenario.Epoch
    
    # Remove UTCG suffix if present
    time_string = time_string.replace(' UTCG', '')
    epoch_str = epoch_str.replace(' UTCG', '')
    
    # Parse both epoch and target time
    epoch_datetime = datetime.strptime(epoch_str, '%d %b %Y %H:%M:%S.%f')
    target_datetime = datetime.strptime(time_string, '%d %b %Y %H:%M:%S.%f')
    
    # Calculate difference in seconds
    time_delta = target_datetime - epoch_datetime
    epoch_seconds = time_delta.total_seconds()
    
    # Set the current time
    stkRoot.CurrentTime = epoch_seconds


def time_string_to_epoch_seconds(scenario, time_string):
    """
    Convert a formatted time string to epoch seconds.
    
    Args:
        scenario: STK Scenario object
        time_string: Time in format 'DD MMM YYYY HH:MM:SS.fff UTCG'
        
    Returns:
        float: Epoch seconds relative to scenario epoch
    """
    # Get epoch time from scenario
    epoch_str = scenario.Epoch
    
    # Remove UTCG suffix if present
    time_string = time_string.replace(' UTCG', '')
    epoch_str = epoch_str.replace(' UTCG', '')
    
    # Parse both epoch and target time
    epoch_datetime = datetime.strptime(epoch_str, '%d %b %Y %H:%M:%S.%f')
    target_datetime = datetime.strptime(time_string, '%d %b %Y %H:%M:%S.%f')
    
    # Calculate difference in seconds
    time_delta = target_datetime - epoch_datetime
    return time_delta.total_seconds()


def epoch_seconds_to_time_string(scenario, epoch_seconds, append_UTCG=True):
    """
    Convert epoch seconds to a formatted time string.
    
    Args:
        scenario: STK Scenario object
        epoch_seconds: Seconds relative to scenario epoch
        append_UTCG: If True, append ' UTCG' suffix (default: True)
        
    Returns:
        str: Time in format 'DD MMM YYYY HH:MM:SS.fff' or 'DD MMM YYYY HH:MM:SS.fff UTCG'
    """
    # Get epoch time from scenario
    epoch_str = scenario.Epoch
    
    # Remove UTCG suffix if present
    epoch_str = epoch_str.replace(' UTCG', '')
    
    # Parse epoch string to datetime
    epoch_datetime = datetime.strptime(epoch_str, '%d %b %Y %H:%M:%S.%f')
    
    # Add epoch seconds to epoch datetime
    result_datetime = epoch_datetime + timedelta(seconds=epoch_seconds)
    
    # Format back to string
    time_str = result_datetime.strftime('%d %b %Y %H:%M:%S.%f')[:-3]
    
    # Append UTCG suffix if requested
    if append_UTCG:
        time_str += ' UTCG'
    
    return time_str


def create_cartesian_coordinate_components(stkRoot, coord_system_name, suffix="", verbose=False):
    """
    Create position and velocity components for a coordinate system in the Component Browser.
    
    Args:
        stkRoot: STK Root object
        coord_system_name: Name of the coordinate system (e.g., "CentralBody/Sun Syst_SEM_L2")
        suffix: Suffix to append to component names (e.g., "_L2", "_Base")
        verbose: Print status messages (default: False)
    """
    if verbose:
        print(f'Creating coordinate components with suffix "{suffix}" for system "{coord_system_name}"')
    
    # Define component mappings
    components = [
        ('Vx', f'Vx{suffix}'),
        ('Vy', f'Vy{suffix}'),
        ('Vz', f'Vz{suffix}'),
        ('X', f'X{suffix}'),
        ('Y', f'Y{suffix}'),
        ('Z', f'Z{suffix}')
    ]
    
    # Create and configure each component
    for original_name, new_name in components:
        try:
            # Duplicate the original component
            stkRoot.ExecuteCommand(f'ComponentBrowser */ Duplicate "Calculation Objects" {original_name} "{new_name}"')
            
            # Set the coordinate system for the new component
            stkRoot.ExecuteCommand(f'ComponentBrowser */ SetValue "Calculation Objects" "{new_name}" CoordSystem "{coord_system_name}"')
            
            if verbose:
                print(f'  Created component: {new_name}')
                
        except Exception as e:
            print(f'Warning: Failed to create component {new_name}: {str(e)}')
    
    if verbose:
        print(f'Coordinate components creation completed for system "{coord_system_name}"')


def setup_l2_coordinate_system(stkRoot, verbose=False):
    """
    Create L2 coordinate system and set up graphics visualization.
    
    Args:
        stkRoot: STK Root object
        verbose: Print status messages (default: False)
    """
    if verbose:
        print('Setting up L2 coordinate system and graphics...')
    
    # Create an assembled coordinate system at L2 for visualization purposes
    stkRoot.ExecuteCommand('VectorTool * CentralBody/Sun Create System Syst_SEM_L2 "Assembled" "CentralBody/Sun SEM_L2" "CentralBody/Sun SEM_L2"')
    
    # Create and show axes in the 3D graphics window
    stkRoot.ExecuteCommand('VO * SetVectorGeometry Add "CentralBody/Sun Syst_SEM_L2.Axes Axes"')
    stkRoot.ExecuteCommand('VO * SetVectorGeometry Modify "CentralBody/Sun Syst_SEM_L2.Axes Axes" Show Off Color cyan ShowLabel On DrawAtCB On RefCrdn "CentralBody/Sun Syst_SEM_L2.Axes Axes" OriginPointDef "CentralBody/Sun SEM_L2 Point"')
    
    # Create and show planes
    stkRoot.ExecuteCommand('VO * SetVectorGeometry Add "CentralBody/Sun Syst_SEM_L2.XZ Plane" Show On Color gray ShowLabel On DrawAtObject Off Translucent On Translucency 0.3 ShowLabel Off ShowAxisLabel On PlaneSize 10')
    stkRoot.ExecuteCommand('VO * SetVectorGeometry Add "CentralBody/Sun Syst_SEM_L2.YZ Plane" Show On Color gray ShowLabel On DrawAtObject Off Translucent On Translucency 0.3 ShowLabel Off ShowAxisLabel On PlaneSize 10')
    
    # Set vector geometry scale for better visibility
    stkRoot.ExecuteCommand('VO * SetVectorGeometry Data Scale 10')
    
    # Set 3D Graphics Window max visible distance to 1e15 m for better L2 visualization
    stkRoot.ExecuteCommand('VO * Clipping Far 1e15 1')
    
    if verbose:
        print('  L2 coordinate system created: Syst_SEM_L2')
        print('  Graphics setup: axes (cyan), XZ/YZ planes (gray), scale 10x')
        print('  Clipping distance set to 1e15 m')