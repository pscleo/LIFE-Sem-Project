"""
STK connection and data retrieval utilities.

This module provides functions for:
- Connecting to STK instances
- Retrieving satellite state vectors
- Retrieving celestial body (Sun, Earth) state vectors
"""

import sys
import os
import numpy as np
import win32com.client

# Add Scripts folder to path to find pywin32 modules
scripts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'SA-venv', 'Scripts'))
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


def connect_to_stk():
    """
    Connect to running STK instance.
    
    Returns:
        tuple: (root, scenario) - STK root object and current scenario
    """
    print("Connecting to STK 13...")
    uiApp = win32com.client.Dispatch("STK13.Application")
    uiApp.Visible = True
    root = uiApp.Personality2
    scenario = root.CurrentScenario
    print(f"Connected to scenario: {scenario.InstanceName}")
    return root, scenario


def get_satellite_state_vectors(root, scenario, sat_name, timestep_seconds):
    """
    Get state vectors for a satellite.
    
    Args:
        root: STK root object
        scenario: STK scenario object
        sat_name: Name of the satellite
        timestep_seconds: Time step for data retrieval (seconds)
    
    Returns:
        tuple: (times, positions, velocities)
            - times: Array of epoch seconds
            - positions: Geocentric positions in ICRF frame (km), shape (N, 3)
            - velocities: Geocentric velocities in ICRF frame (km/s), shape (N, 3)
    """
    print(f"Getting satellite state vectors for {sat_name}...")
    
    sat = root.GetObjectFromPath(f"Satellite/{sat_name}")
    
    # Get position
    pos_dp = sat.DataProviders.Item("Cartesian Position").Group.Item("ICRF")
    pos_result = pos_dp.Exec(scenario.StartTime, scenario.StopTime, timestep_seconds)
    
    times = np.array(pos_result.DataSets.GetDataSetByName("Time").GetValues())
    x = np.array(pos_result.DataSets.GetDataSetByName("x").GetValues())
    y = np.array(pos_result.DataSets.GetDataSetByName("y").GetValues())
    z = np.array(pos_result.DataSets.GetDataSetByName("z").GetValues())
    positions = np.vstack((x, y, z)).T
    
    # Get velocity
    vel_dp = sat.DataProviders.Item("Cartesian Velocity").Group.Item("ICRF")
    vel_result = vel_dp.Exec(scenario.StartTime, scenario.StopTime, timestep_seconds)
    
    vx = np.array(vel_result.DataSets.GetDataSetByName("x").GetValues())
    vy = np.array(vel_result.DataSets.GetDataSetByName("y").GetValues())
    vz = np.array(vel_result.DataSets.GetDataSetByName("z").GetValues())
    velocities = np.vstack((vx, vy, vz)).T
    
    print(f"  Retrieved {len(times)} data points for {sat_name}")
    return times, positions, velocities


def get_body_state_vectors(root, scenario, body_name, timestep_seconds):
    """
    Get state vectors for a celestial body (Sun, Earth, etc.).
    
    Args:
        root: STK root object
        scenario: STK scenario object
        body_name: Name of the celestial body ("Sun", "Earth", etc.)
        timestep_seconds: Time step for data retrieval (seconds)
    
    Returns:
        tuple: (times, positions, velocities)
            - times: Array of epoch seconds
            - positions: Geocentric positions in ICRF frame (km), shape (N, 3)
            - velocities: Geocentric velocities in ICRF frame (km/s), shape (N, 3)
    """
    print(f"Getting state vectors for {body_name}...")
    
    try:
        planet = root.GetObjectFromPath(f"Planet/{body_name}")
        print(f"  Found {body_name} as Planet")
    except:
        try:
            planet = root.GetObjectFromPath(f"Star/{body_name}")
            print(f"  Found {body_name} as Star")
        except:
            raise ValueError(f"Could not find {body_name} as Planet or Star")
    
    # Get position
    pos_dp = planet.DataProviders.Item("Cartesian Position").Group.Item("ICRF")
    pos_result = pos_dp.Exec(scenario.StartTime, scenario.StopTime, timestep_seconds)
    
    times = np.array(pos_result.DataSets.GetDataSetByName("Time").GetValues())
    x = np.array(pos_result.DataSets.GetDataSetByName("x").GetValues())
    y = np.array(pos_result.DataSets.GetDataSetByName("y").GetValues())
    z = np.array(pos_result.DataSets.GetDataSetByName("z").GetValues())
    positions = np.vstack((x, y, z)).T
    
    # Get velocity
    vel_dp = planet.DataProviders.Item("Cartesian Velocity").Group.Item("ICRF")
    vel_result = vel_dp.Exec(scenario.StartTime, scenario.StopTime, timestep_seconds)
    
    vx = np.array(vel_result.DataSets.GetDataSetByName("x").GetValues())
    vy = np.array(vel_result.DataSets.GetDataSetByName("y").GetValues())
    vz = np.array(vel_result.DataSets.GetDataSetByName("z").GetValues())
    velocities = np.vstack((vx, vy, vz)).T
    
    print(f"  Retrieved {len(times)} data points for {body_name}")
    return times, positions, velocities


def get_satellite_initial_state(root, scenario, sat_name, timestep_seconds):
    """
    Get initial state vector (position and velocity) of a satellite at scenario start time.
    
    Args:
        root: STK root object
        scenario: STK scenario object
        sat_name: Name of the satellite
        timestep_seconds: Time step for data retrieval (seconds)
    
    Returns:
        tuple: (position_icrf, velocity_icrf)
            - position_icrf: Initial position in ICRF frame (km)
            - velocity_icrf: Initial velocity in ICRF frame (km/s)
    """
    print(f"Getting initial state for {sat_name}...")
    
    sat = root.GetObjectFromPath(f"Satellite/{sat_name}")
    
    # Query for entire trajectory and take first point
    pos_dp = sat.DataProviders.Item("Cartesian Position").Group.Item("ICRF")
    pos_result = pos_dp.Exec(scenario.StartTime, scenario.StopTime, timestep_seconds)
    
    # Get data arrays
    times = np.array(pos_result.DataSets.GetDataSetByName("Time").GetValues())
    x = np.array(pos_result.DataSets.GetDataSetByName("x").GetValues())
    y = np.array(pos_result.DataSets.GetDataSetByName("y").GetValues())
    z = np.array(pos_result.DataSets.GetDataSetByName("z").GetValues())
    
    # Take first available point
    position_icrf = np.array([x[0], y[0], z[0]])
    
    # Get velocity - query entire trajectory and take first point
    vel_dp = sat.DataProviders.Item("Cartesian Velocity").Group.Item("ICRF")
    vel_result = vel_dp.Exec(scenario.StartTime, scenario.StopTime, timestep_seconds)
    
    vx = np.array(vel_result.DataSets.GetDataSetByName("x").GetValues())
    vy = np.array(vel_result.DataSets.GetDataSetByName("y").GetValues())
    vz = np.array(vel_result.DataSets.GetDataSetByName("z").GetValues())
    
    velocity_icrf = np.array([vx[0], vy[0], vz[0]])
    
    print(f"  Position: {position_icrf} km")
    print(f"  Velocity: {velocity_icrf} km/s")
    
    return position_icrf, velocity_icrf


def get_body_state_at_epoch(root, scenario, body_name, timestep_seconds):
    """
    Get state vectors for a celestial body at scenario start time.
    
    Args:
        root: STK root object
        scenario: STK scenario object
        body_name: Name of the celestial body
        timestep_seconds: Time step for data retrieval (seconds)
    
    Returns:
        tuple: (position, velocity)
            - position: Geocentric position in ICRF frame at epoch (km)
            - velocity: Geocentric velocity in ICRF frame at epoch (km/s)
    """
    print(f"Getting state for {body_name} at epoch...")
    
    try:
        planet = root.GetObjectFromPath(f"Planet/{body_name}")
    except:
        planet = root.GetObjectFromPath(f"Star/{body_name}")
    
    # Query for entire trajectory and take first point
    pos_dp = planet.DataProviders.Item("Cartesian Position").Group.Item("ICRF")
    pos_result = pos_dp.Exec(scenario.StartTime, scenario.StopTime, timestep_seconds)
    
    times = np.array(pos_result.DataSets.GetDataSetByName("Time").GetValues())
    x = np.array(pos_result.DataSets.GetDataSetByName("x").GetValues())
    y = np.array(pos_result.DataSets.GetDataSetByName("y").GetValues())
    z = np.array(pos_result.DataSets.GetDataSetByName("z").GetValues())
    position = np.array([x[0], y[0], z[0]])
    
    # Get velocity
    vel_dp = planet.DataProviders.Item("Cartesian Velocity").Group.Item("ICRF")
    vel_result = vel_dp.Exec(scenario.StartTime, scenario.StopTime, timestep_seconds)
    
    vx = np.array(vel_result.DataSets.GetDataSetByName("x").GetValues())
    vy = np.array(vel_result.DataSets.GetDataSetByName("y").GetValues())
    vz = np.array(vel_result.DataSets.GetDataSetByName("z").GetValues())
    velocity = np.array([vx[0], vy[0], vz[0]])
    
    return position, velocity
