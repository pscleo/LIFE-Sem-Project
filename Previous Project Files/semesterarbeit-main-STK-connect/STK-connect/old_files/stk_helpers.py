"""
Helper functions for STK Python automation
"""
import win32com.client
import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path

def connect_to_stk(version=13):
    """
    Connect to a running STK instance.
    
    Args:
        version (int): STK version number (default: 13)
    
    Returns:
        tuple: (root, scenario) objects
    """
    print(f"DEBUG01: Attempting to connect to STK {version}...")
    try:
        uiApp = win32com.client.Dispatch(f"STK{version}.Application")
        print("DEBUG01: Dispatch succeeded")
    except Exception as e:
        print(f"DEBUG01: Failed to get STK instance: {e}")
        raise
    
    print("DEBUG01: Getting Personality2...")
    try:
        root = uiApp.Personality2
        print("DEBUG01: Personality2 retrieved")
    except Exception as e:
        print(f"DEBUG01: Failed to get Personality2: {e}")
        raise
    
    print("DEBUG01: Connected to STK successfully")
    
    print("DEBUG01: Getting current scenario...")
    try:
        scenario = root.CurrentScenario
        print(f"DEBUG01: Current scenario: {scenario.InstanceName}")
    except Exception as e:
        print(f"DEBUG01: Failed to get scenario: {e}")
        print("DEBUG01: Make sure a scenario is open in STK!")
        raise
    
    return root, scenario


def get_sat_positions(root, scenario, sat_name, timestep_seconds, frame="ICRF"):
    """
    Get satellite position data from STK.
    
    Args:
        root: STK root object
        scenario: STK scenario object
        sat_name (str): Name of the satellite
        timestep_seconds (float): Time step in seconds
        frame (str): Coordinate frame (default: "ICRF")
    
    Returns:
        tuple: (times, positions) where positions is numpy array of shape (n, 3)
    """
    print(f"DEBUG01: Getting position data for {sat_name} in {frame} frame...")
    try:
        sat = root.GetObjectFromPath(f"Satellite/{sat_name}")
        print(f"DEBUG01: Satellite object retrieved: {sat_name}")
    except Exception as e:
        print(f"DEBUG01: Failed to get satellite {sat_name}: {e}")
        raise
    
    try:
        dp = sat.DataProviders.Item("Cartesian Position").Group.Item(frame)
        print(f"DEBUG01: Data provider accessed for {sat_name}")
    except Exception as e:
        print(f"DEBUG01: Failed to access data provider for {sat_name}: {e}")
        raise
    
    print(f"DEBUG01: Executing data provider for {sat_name}...")
    print(f"DEBUG01: Start: {scenario.StartTime}, Stop: {scenario.StopTime}, Step: {timestep_seconds}")
    try:
        result = dp.Exec(scenario.StartTime, scenario.StopTime, timestep_seconds)
        print(f"DEBUG01: Data provider execution complete for {sat_name}")
    except Exception as e:
        print(f"DEBUG01: Data provider execution failed for {sat_name}: {e}")
        raise
    
    times = np.array(result.DataSets.GetDataSetByName("Time").GetValues())
    x = np.array(result.DataSets.GetDataSetByName("x").GetValues())
    y = np.array(result.DataSets.GetDataSetByName("y").GetValues())
    z = np.array(result.DataSets.GetDataSetByName("z").GetValues())
    print(f"DEBUG01: Data extracted for {sat_name} - {len(times)} data points")
    
    return times, np.vstack((x, y, z)).T


def save_plot(fig, filename, subfolder="plots"):
    """
    Save a matplotlib figure to a subfolder.
    
    Args:
        fig: Matplotlib figure object
        filename (str): Name of the file (without extension)
        subfolder (str): Subfolder name relative to script location (default: "plots")
    """
    # Get the directory where the script is located
    script_dir = Path(__file__).parent
    plot_dir = script_dir / subfolder
    
    # Create the plots directory if it doesn't exist
    plot_dir.mkdir(exist_ok=True)
    
    # Save the figure
    filepath = plot_dir / f"{filename}.png"
    fig.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"DEBUG01: Plot saved to {filepath}")


def plot_position_differences(ref_times, diffs, reference_sat, show=True, save=True):
    """
    Plot and optionally save position differences between satellites.
    
    Args:
        ref_times (array): Time array
        diffs (dict): Dictionary of differences {sat_name: delta_positions}
        reference_sat (str): Name of reference satellite
        show (bool): Whether to display plots (default: True)
        save (bool): Whether to save plots (default: True)
    """
    print("DEBUG01: Creating difference plots...")
    for name, delta in diffs.items():
        print(f"DEBUG01: Plotting differences for {name}...")
        fig = plt.figure(figsize=(10, 6))
        plt.plot(ref_times, delta[:, 0], label="ΔX (km)")
        plt.plot(ref_times, delta[:, 1], label="ΔY (km)")
        plt.plot(ref_times, delta[:, 2], label="ΔZ (km)")
        plt.title(f"Relative Position: {name} - {reference_sat}")
        plt.xlabel("Time (s)")
        plt.ylabel("Δ Position (km)")
        plt.legend()
        plt.grid(True)
        
        if save:
            # Create a safe filename
            safe_name = f"{name}_vs_{reference_sat}".replace(" ", "_")
            save_plot(fig, safe_name)
        
        if show:
            plt.show()
            print(f"DEBUG01: Plot displayed for {name}")
        else:
            plt.close(fig)


def compute_position_differences(sat_positions, reference_sat):
    """
    Compute position differences relative to a reference satellite.
    
    Args:
        sat_positions (dict): Dictionary of positions {sat_name: positions}
        reference_sat (str): Name of reference satellite
    
    Returns:
        dict: Dictionary of differences {sat_name: delta_positions}
    """
    print("DEBUG01: Computing differences relative to reference satellite...")
    ref_pos = sat_positions[reference_sat]
    print(f"DEBUG01: Reference position shape: {ref_pos.shape}")
    diffs = {}
    
    for name, pos in sat_positions.items():
        if name == reference_sat:
            continue
        diffs[name] = pos - ref_pos
        print(f"DEBUG01: Computed difference for {name}, max delta: {np.max(np.abs(diffs[name]))} km")
    
    print(f"DEBUG01: Differences computed for {len(diffs)} satellites")
    return diffs


def get_sun_position_from_earth(scenario, n_points):
    """
    Approximate Sun position in ICRF frame (Earth-centered) using simple orbital model.
    
    Args:
        scenario: STK scenario object
        n_points: Number of time points
    
    Returns:
        numpy array: Sun positions in ICRF, Earth-centered (km), shape (n_points, 3)
    """
    # Sun-Earth distance (1 AU in km)
    au_km = 149597870.7
    
    # Approximate Sun position using circular orbit
    # This is a simplification - actual Sun position varies due to orbital eccentricity
    # For L2 calculation purposes, this approximation is sufficient
    
    # Generate time-varying Sun positions
    # Assume Sun orbits in approximate XY plane (ecliptic)
    angles = np.linspace(0, 2 * np.pi * n_points / 365.25, n_points)
    
    sun_positions = np.zeros((n_points, 3))
    sun_positions[:, 0] = -au_km * np.cos(angles)  # Negative because Sun is opposite to Earth's motion
    sun_positions[:, 1] = -au_km * np.sin(angles)
    sun_positions[:, 2] = 0  # Assume ecliptic plane
    
    return sun_positions


def transform_to_sem_l2(sat_positions_icrf, sun_positions_icrf, earth_positions_icrf):
    """
    Transform satellite positions from ICRF to SEM-L2 frame.
    
    SEM-L2 frame definition:
    - Origin: Sun-Earth-Moon L2 point (approximated as Sun-Earth L2)
    - X-axis: Anti-sunward (from Sun towards Earth and beyond)
    - Z-axis: Ecliptic north (approximated as perpendicular to Sun-Earth orbital plane)
    
    Args:
        sat_positions_icrf: Satellite positions in ICRF (n, 3)
        sun_positions_icrf: Sun positions in ICRF (n, 3)
        earth_positions_icrf: Earth positions in ICRF (n, 3)
    
    Returns:
        numpy array: Satellite positions in SEM-L2 frame (n, 3)
    """
    n_points = sat_positions_icrf.shape[0]
    transformed_positions = np.zeros_like(sat_positions_icrf)
    
    for i in range(n_points):
        sun_pos = sun_positions_icrf[i]
        earth_pos = earth_positions_icrf[i]
        sat_pos = sat_positions_icrf[i]
        
        # Sun-Earth vector
        sun_to_earth = earth_pos - sun_pos
        sun_earth_distance = np.linalg.norm(sun_to_earth)
        
        # L2 is approximately 1.5 million km from Earth anti-sunward
        # L2 distance ratio: about 0.01 of Sun-Earth distance beyond Earth
        l2_distance_from_sun = sun_earth_distance * 1.01
        l2_position = sun_pos + (sun_to_earth / sun_earth_distance) * l2_distance_from_sun
        
        # Define X-axis: anti-sunward (Earth to Sun direction, normalized)
        x_axis = -sun_to_earth / sun_earth_distance
        
        # Define Z-axis: perpendicular to orbital plane (ecliptic north approximation)
        # Use Earth's velocity vector (approximated from position changes) to define orbital plane
        # For simplicity, use a fixed ecliptic north approximation: perpendicular to Sun-Earth line
        # True ecliptic north would require more complex calculation
        
        # Temporary Y direction (will be orthogonalized)
        temp_y = np.array([0, 0, 1])  # Use ICRF Z as initial guess
        
        # Ensure Y is perpendicular to X
        temp_y = temp_y - np.dot(temp_y, x_axis) * x_axis
        temp_y = temp_y / np.linalg.norm(temp_y)
        
        # Z-axis: perpendicular to both X and Y (right-hand rule)
        z_axis = np.cross(x_axis, temp_y)
        z_axis = z_axis / np.linalg.norm(z_axis)
        
        # Recalculate Y to ensure orthogonality
        y_axis = np.cross(z_axis, x_axis)
        
        # Rotation matrix from ICRF to SEM-L2
        rotation_matrix = np.array([x_axis, y_axis, z_axis])
        
        # Translate to L2-centered frame
        sat_pos_centered = sat_pos - l2_position
        
        # Rotate to SEM-L2 frame
        transformed_positions[i] = rotation_matrix @ sat_pos_centered
    
    return transformed_positions


def get_sat_positions_sem_l2(root, scenario, sat_name, timestep_seconds):
    """
    Get satellite position data in SEM-L2 frame.
    
    Args:
        root: STK root object
        scenario: STK scenario object
        sat_name (str): Name of the satellite
        timestep_seconds (float): Time step in seconds
    
    Returns:
        tuple: (times, positions) where positions is numpy array of shape (n, 3) in SEM-L2 frame
    """
    # Get satellite position in ICRF
    times, sat_pos_icrf = get_sat_positions(root, scenario, sat_name, timestep_seconds, frame="ICRF")
    
    # Get Sun position (approximate)
    sun_pos_icrf = get_sun_position_from_earth(scenario, len(times))
    earth_pos_icrf = np.zeros_like(sun_pos_icrf)  # Earth at origin
    
    # Transform to SEM-L2 frame
    sat_pos_sem_l2 = transform_to_sem_l2(sat_pos_icrf, sun_pos_icrf, earth_pos_icrf)
    
    return times, sat_pos_sem_l2