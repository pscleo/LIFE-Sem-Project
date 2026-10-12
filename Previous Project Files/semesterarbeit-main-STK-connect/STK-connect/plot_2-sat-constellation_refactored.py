"""
Plot offset trajectories of satellite constellation relative to base satellite in SEM-L2 frame.

This refactored script uses helper modules for:
- STK connection and data retrieval (stk_connection.py)
- Coordinate transformations (coordinate_transforms.py)
- Data processing and analysis (data_processing.py)
- Visualization (visualization.py)
"""

import matplotlib
matplotlib.use('TkAgg')  # Force interactive backend for plot toolbar

import sys
import os
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Add Scripts folder to path to find pywin32 modules
scripts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'SA-venv', 'Scripts'))
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

# Import helper modules
from helpers.stk_connection import connect_to_stk, get_satellite_state_vectors, get_body_state_vectors
from helpers.coordinate_transforms import convert_to_barycentric, transform_trajectory_to_sem_l2
from helpers.data_processing import filter_time_range, compute_relative_positions, print_drift_analysis
from helpers.visualization import (plot_offsets_vs_time, plot_relative_trajectories_3d, 
                                   title_to_filename, plot_delta_movement)

# ============================================================================
# USER SETTINGS - Modify these to customize the analysis and plots
# ============================================================================

# Time range settings
START_DATE_YEAR = 2022
START_DATE_MONTH = 10
START_DATE_DAY = 6
START_DATE_HOUR = 6
START_DATE_MINUTE = 54
START_DATE_SECOND = 5
DURATION_DAYS = 50

# STK connection settings
TIMESTEP_SECONDS = 3600  # Data sampling interval (1 hour)

# Add a user-configurable plot title and output filename
PLOT_TITLE = "satellite_constellation_50d"
# Toggle: show/hide the plot title (filename still uses PLOT_TITLE)
PLOT_SHOW_TITLE = False

# Plot generation toggles - Set to False to skip generating specific plots
ENABLE_TIMESERIES_LINEAR = False   # Time series plots (linear scale)
ENABLE_TIMESERIES_LOG = False      # Time series plots (log scale)
ENABLE_3D_LINEAR = False           # 3D trajectory plots (linear scale)
ENABLE_3D_LOG = False              # 3D trajectory plots (log scale)
ENABLE_DELTA_MOVEMENT = True      # Delta movement rate plots (Δx/Δt, Δy/Δt, Δz/Δt)

# Satellite names to analyze
BASE_SATELLITE = "Base"  # Reference satellite
SATELLITE_NAMES = [
    "Base",
    "X100",
    "X-100",
    "Y100",
    "Y-100",
    "Z100",
    "Z-100"
]

# Plot settings - Time series plots
TIME_PLOT_SETTINGS = {
    'figsize': (16, 12),
    'dpi': 300,
    'linewidth': 2.0,
    'alpha': 0.8,
    'title_fontsize': 16,
    'subtitle_fontsize': 14,
    'label_fontsize': 14,
    'legend_fontsize': 11,
    'tick_fontsize': 12,
    'left': 0.08,
    'bottom': 0.08,
    'right': 0.98,
    'top': 0.93,
    'hspace': 0.30,
    'wspace': 0.25,
    'xlabel': 'Time (days)',
    'ylabel_offset': 'Offset (km)',
}

# Plot settings - 3D trajectory plots
TRAJECTORY_PLOT_SETTINGS = {
    'figsize': (16, 12),
    'dpi': 300,
    'linewidth': 1.5,
    'alpha': 0.7,
    'title_fontsize': 16,
    'subtitle_fontsize': 14,
    'label_fontsize': 14,
    'legend_fontsize': 11,
    'tick_fontsize': 12,
    'label_fontsize_3d': 11,
    'tick_fontsize_3d': 10,
    'left': 0.07,
    'bottom': 0.07,
    'right': 0.994,
    'top': 0.92,
    'hspace': 0.24,
    'wspace': 0.25,
    'base_marker_size': 150,
    'base_marker_size_3d': 200,
}

# Color scheme for satellite pairs
SATELLITE_COLORS = {
    'Base': "#FF00FF",
    'X100': '#00ff00',
    'X-100': '#008000',
    'Y100': '#ff0000',
    'Y-100': '#800000',
    'Z100': '#0000ff',
    'Z-100': '#000080',
}

# Custom labels for satellites (for legend)
SATELLITE_LABELS = {
    'Base': "Base",
    'X100': "X +100m",
    'X-100': "X -100m",
    'Y100': "Y +100m",
    'Y-100': "Y -100m",
    'Z100': "Z +100m",
    'Z-100': "Z -100m",
}

# ============================================================================
# END USER SETTINGS
# ============================================================================


def main():
    # Connect to STK
    root, scenario = connect_to_stk()
    root.UnitPreferences.SetCurrentUnit("DateFormat", "EpSec")
    
    # Define time range
    start_date = datetime(START_DATE_YEAR, START_DATE_MONTH, START_DATE_DAY, 
                          START_DATE_HOUR, START_DATE_MINUTE, START_DATE_SECOND)
    
    print(f"\n{'='*70}")
    print(f"TIME RANGE CONFIGURATION")
    print(f"{'='*70}")
    print(f"Start date: {start_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {DURATION_DAYS} days")
    print(f"End date: {(start_date + timedelta(days=DURATION_DAYS)).strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("="*70)
    print("SATELLITE CONSTELLATION OFFSET ANALYSIS")
    print("="*70)
    
    # Get Sun ephemeris (geocentric)
    print("\n=== Getting Sun ephemeris ===")
    sun_times, sun_pos_geocentric, sun_vel_geocentric = get_body_state_vectors(
        root, scenario, "Sun", TIMESTEP_SECONDS
    )
    
    # Filter Sun data to time range
    print(f"Filtering Sun ephemeris to {DURATION_DAYS} days starting {start_date.strftime('%Y-%m-%d')}...")
    sun_times, sun_pos_geocentric, sun_vel_geocentric = filter_time_range(
        sun_times, sun_pos_geocentric, sun_vel_geocentric, start_date, DURATION_DAYS
    )
    
    # Convert to barycentric
    _, _, earth_pos_bary, earth_vel_bary, sun_pos_bary, sun_vel_bary = convert_to_barycentric(
        np.zeros_like(sun_pos_geocentric),  # Dummy geocentric positions
        np.zeros_like(sun_vel_geocentric),  # Dummy geocentric velocities
        sun_pos_geocentric,
        sun_vel_geocentric
    )
    
    print(f"✓ Converted to barycentric frame")
    
    # Get each satellite and transform to SEM-L2
    trajectories_sem_l2 = {}
    sat_times = None
    
    for sat_name in SATELLITE_NAMES:
        print(f"\n=== Processing {sat_name} ===")
        
        # Get satellite data
        times, pos_icrf, vel_icrf = get_satellite_state_vectors(
            root, scenario, sat_name, TIMESTEP_SECONDS
        )
        
        # Filter to time range
        print(f"Filtering {sat_name} to {DURATION_DAYS} days...")
        times, pos_icrf, vel_icrf = filter_time_range(
            times, pos_icrf, vel_icrf, start_date, DURATION_DAYS
        )
        
        # Store times (should be same for all satellites)
        if sat_times is None:
            sat_times = times
        
        # Convert to barycentric (satellite positions from STK are geocentric)
        pos_bary, vel_bary, _, _, _, _ = convert_to_barycentric(
            pos_icrf, vel_icrf,
            sun_pos_geocentric, sun_vel_geocentric
        )
        
        # Transform to SEM-L2
        print(f"Transforming {sat_name} to SEM-L2 frame...")
        pos_sem_l2, vel_sem_l2 = transform_trajectory_to_sem_l2(
            times, pos_bary, vel_bary,
            sun_pos_bary, sun_vel_bary,
            earth_pos_bary, earth_vel_bary,
            sun_geocentric=sun_pos_geocentric,
            sun_vel_geocentric=sun_vel_geocentric
        )
        
        trajectories_sem_l2[sat_name] = pos_sem_l2
        print(f"✓ {sat_name} transformed to SEM-L2")
    
    # Compute relative positions (offsets from Base)
    offsets_dict = compute_relative_positions(trajectories_sem_l2, BASE_SATELLITE)
    
    # Drift rate analysis
    print_drift_analysis(sat_times, offsets_dict)
    
    # Create plots
    print(f"\n{'='*70}")
    print("Creating visualizations...")
    print(f"{'='*70}")
    
    plots_dir = Path(__file__).parent / "plots"
    plots_dir.mkdir(exist_ok=True)
    
    # Build filenames from the title
    time_series_linear_filename = title_to_filename(f"{PLOT_TITLE}_timeseries_linear", 'png')
    time_series_log_filename = title_to_filename(f"{PLOT_TITLE}_timeseries_log", 'png')
    trajectory_3d_linear_filename = title_to_filename(f"{PLOT_TITLE}_3d_linear", 'png')
    trajectory_3d_log_filename = title_to_filename(f"{PLOT_TITLE}_3d_log", 'png')
    delta_movement_filename = title_to_filename(f"{PLOT_TITLE}_delta_movement", 'png')
    
    time_series_linear_path = plots_dir / time_series_linear_filename
    time_series_log_path = plots_dir / time_series_log_filename
    trajectory_3d_linear_path = plots_dir / trajectory_3d_linear_filename
    trajectory_3d_log_path = plots_dir / trajectory_3d_log_filename
    delta_movement_path = plots_dir / delta_movement_filename
    
    # Determine custom title (None if PLOT_SHOW_TITLE is False)
    custom_title = PLOT_TITLE if PLOT_SHOW_TITLE else None
    
    # Generate plots based on toggles
    if ENABLE_TIMESERIES_LINEAR:
        print("Generating linear scale time series plot...")
        plot_offsets_vs_time(sat_times, offsets_dict, save_path=time_series_linear_path,
                             colors=SATELLITE_COLORS, labels=SATELLITE_LABELS,
                             plot_settings=TIME_PLOT_SETTINGS,
                             log_scale=False, title=custom_title)
    else:
        print("Skipping linear scale time series plot (disabled)")
    
    if ENABLE_TIMESERIES_LOG:
        print("Generating log scale time series plot...")
        plot_offsets_vs_time(sat_times, offsets_dict, save_path=time_series_log_path,
                             colors=SATELLITE_COLORS, labels=SATELLITE_LABELS,
                             plot_settings=TIME_PLOT_SETTINGS,
                             log_scale=True, title=custom_title)
    else:
        print("Skipping log scale time series plot (disabled)")
    
    if ENABLE_3D_LINEAR:
        print("Generating linear scale 3D trajectory plot...")
        plot_relative_trajectories_3d(offsets_dict, save_path=trajectory_3d_linear_path,
                                       colors=SATELLITE_COLORS, labels=SATELLITE_LABELS,
                                       plot_settings=TRAJECTORY_PLOT_SETTINGS,
                                       log_scale=False, title=custom_title,
                                       base_satellite_name=SATELLITE_LABELS['Base'],
                                       base_color=SATELLITE_COLORS['Base'])
    else:
        print("Skipping linear scale 3D trajectory plot (disabled)")
    
    if ENABLE_3D_LOG:
        print("Generating log scale 3D trajectory plot...")
        plot_relative_trajectories_3d(offsets_dict, save_path=trajectory_3d_log_path,
                                       colors=SATELLITE_COLORS, labels=SATELLITE_LABELS,
                                       plot_settings=TRAJECTORY_PLOT_SETTINGS,
                                       log_scale=True, title=custom_title,
                                       base_satellite_name=SATELLITE_LABELS['Base'],
                                       base_color=SATELLITE_COLORS['Base'])
    else:
        print("Skipping log scale 3D trajectory plot (disabled)")
    
    if ENABLE_DELTA_MOVEMENT:
        print("Generating delta movement plot...")
        plot_delta_movement(sat_times, offsets_dict, save_path=delta_movement_path,
                           colors=SATELLITE_COLORS, labels=SATELLITE_LABELS,
                           plot_settings=TIME_PLOT_SETTINGS,
                           title=custom_title)
    else:
        print("Skipping delta movement plot (disabled)")
    
    print("\n=== Complete! ===")
    print(f"Generated plots in: {plots_dir}")
    
    # Show interactive plots with toolbar
    print("\nDisplaying interactive plots...")
    plt.show()


if __name__ == "__main__":
    main()
