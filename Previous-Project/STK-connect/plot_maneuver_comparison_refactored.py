"""
Plot and compare JWST trajectories with different velocity maneuvers in SEM-L2 frame.

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
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt

# Add Scripts folder to path to find pywin32 modules
scripts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'SA-venv', 'Scripts'))
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

# Import helper modules
from helpers.stk_connection import connect_to_stk, get_satellite_state_vectors, get_body_state_vectors
from helpers.coordinate_transforms import (convert_to_barycentric, transform_trajectory_to_sem_l2,
                                   transform_trajectory_to_sem_l2_true,
                                   build_sem_l2_axes_from_true_l2)
from helpers.data_processing import filter_time_range
from helpers.visualization import plot_trajectories_3d, title_to_filename

# ============================================================================
# USER SETTINGS - Modify these to customize the analysis and plots
# ============================================================================

# Time range settings
START_DATE_YEAR = 2022
START_DATE_MONTH = 10
START_DATE_DAY = 6
DURATION_DAYS = 359 * 1 + 2

# # First Year of Webb Operations
# START_DATE_YEAR = 2021
# START_DATE_MONTH = 12
# START_DATE_DAY = 25
# DURATION_DAYS = 359 * 1 + 2


# STK connection settings
TIMESTEP_SECONDS = 3600  # Data sampling interval (1 hour)

# Satellite names to analyze
SATELLITE_NAMES = [
    # "Base",
    # "Webb-no-correction",
    # "Webb-Vz-p1",
    # "Webb-Vz-m1",
    # "Webb-Vy-p1",
    # "Webb-Vy-m1",
    # "Webb-Vx-p1",
    # "Webb-Vx-m1",
    "X1000",
    "X-1000",
    "Y1000",
    "Y-1000",
    "Z1000",
    "Z-1000",
    "JWST",
    # "SEMB-L2-horizon",
    # "Webb-5-years"
]

# Plot settings
PLOT_SETTINGS = {
    'figsize': (8, 6),  # A4-friendly: ~20cm x 15cm at 100mm margins
    'dpi': 300,         # Standard for print (keep this)
    'linewidth': 2.0,   # Thicker lines for print clarity
    'alpha': 0.8,       # Slightly more opaque for print
    
    # JWST reference trajectory settings (highlighter effect)
    'jwst_linewidth': 1, 
    'jwst_alpha': 0.9,
    'jwst_centerline_width': 0, #10 for highlight line
    'jwst_centerline_alpha': 0.25,
    'jwst_zorder': 1,
    'jwst_centerline_zorder': 3,
    'other_zorder': 2,
    
    # Font sizes (optimized for A4 print)
    'title_fontsize': 14,      # Reduced from 16
    'subtitle_fontsize': 12,   # Reduced from 14
    'label_fontsize': 12,      # Reduced from 14
    'legend_fontsize': 9,     # Reduced from 11
    'tick_fontsize': 10,       # Reduced from 12
    
    # Font sizes (3D plot - separate settings)
    'label_fontsize_3d': 10,   # Reduced from 11
    'tick_fontsize_3d': 9,     # Reduced from 10
    
    # Subplot spacing (tighter for A4)
    'left': 0.12,
    'bottom': 0.12,
    'right': 0.98,
    'top': 0.94,
    'hspace': 0.30,
    'wspace': 0.28,
    
    # Marker sizes
    'l2_marker_size': 120,     # Reduced from 150
    'l2_marker_size_3d': 150,  # Reduced from 200
    'earth_marker_size': 80,   # Reduced from 100
}

# Color scheme for trajectories
TRAJECTORY_COLORS = {
    'JWST': "#000000",
    'Webb-no-correction': "#ff00ff",
    'Webb-Vx-p1': "#00ff00",
    'Webb-Vx-m1': "#008000",
    'Webb-Vy-p1': "#ff0000",
    'Webb-Vy-m1': "#800000",
    'Webb-Vz-p1': "#0000ff",
    'Webb-Vz-m1': '#000080',
    'X1000': "#00ff00",
    'X-1000': "#008000",
    'Y1000': "#ff0000",
    'Y-1000': "#800000",
    'Z1000': "#0000ff",
    'Z-1000': '#000080',
    'Webb-Actual-with-bias': "#FF0000",
    'Base': "#FF0000",
    'Webb-5-years': "#FF0000",
}

# Custom labels for trajectories (for legend)
TRAJECTORY_LABELS = {
    'JWST': "JWST",
    'Webb-no-correction': "no stationkeeping",
    'Webb-Vx-p1': "$v_x$ $+1$ m/s",
    'Webb-Vx-m1': "v$_x$ $-1$ m/s",
    'Webb-Vy-p1': "v$_y$ $+1$ m/s",
    'Webb-Vy-m1': "v$_y$ $-1$ m/s",
    'Webb-Vz-p1': "v$_z$ $+1$ m/s",
    'Webb-Vz-m1': "v$_z$ $-1$ m/s",
    'X1000': "x $+1000$ m/s",
    'X-1000': "x $-1000$ m/s",
    'Y1000': "y $+1000$ m/s",
    'Y-1000': "y $-1000$ m/s",
    'Z1000': "z $+1000$ m/s",
    'Z-1000': "z $-1000$ m/s",
    'Webb-Actual-with-bias': "Simulation",
    'Base': "Simulation",
    'Webb-5-years': "Simulation",
}

# Add a user-configurable plot title
PLOT_TITLE = "Trajectory-1000m-offsets-1yr"
# Toggle: show/hide the plot title (filename still uses PLOT_TITLE)
PLOT_SHOW_TITLE = False

# Plot generation toggle - Set to False to skip generating the plot
ENABLE_3D_PLOT = True

# ============================================================================
# END USER SETTINGS
# ============================================================================


def main():
    # Connect to STK
    root, scenario = connect_to_stk()
    root.UnitPreferences.SetCurrentUnit("DateFormat", "EpSec")
    
    # Define time range using user settings
    start_date = datetime(START_DATE_YEAR, START_DATE_MONTH, START_DATE_DAY, 0, 0, 0)
    
    print(f"\n{'='*70}")
    print(f"TIME RANGE CONFIGURATION")
    print(f"{'='*70}")
    print(f"Start date: {start_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {DURATION_DAYS} days")
    print(f"End date: {(start_date + timedelta(days=DURATION_DAYS)).strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("="*70)
    print("MANEUVER COMPARISON ANALYSIS")
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
    # Convert Sun (geocentric) to barycentric Earth and Sun positions; satellites start as zero placeholder
    _, _, earth_pos_bary, earth_vel_bary, sun_pos_bary, sun_vel_bary = convert_to_barycentric(
        np.zeros_like(sun_pos_geocentric),
        np.zeros_like(sun_vel_geocentric),
        sun_pos_geocentric,
        sun_vel_geocentric
    )
    
    print(f"✓ Converted to barycentric frame")
    
    # Get SEMB-L2 satellite (true L2 position)
    print(f"\n{'='*70}")
    print("Getting SEMB-L2 (True L2 Point)")
    print(f"{'='*70}")
    
    use_true_l2 = False
    l2_pos_bary = np.zeros_like(sun_pos_bary)  # Initialize with zeros
    l2_vel_bary = np.zeros_like(sun_vel_bary)
    l2_times = sun_times  # Default to sun times
    
    try:
        l2_times, l2_pos_geo, l2_vel_geo = get_satellite_state_vectors(
            root, scenario, "SEMB-L2-horizon", TIMESTEP_SECONDS
        )
        
        # Filter to time range
        print(f"Filtering SEMB-L2 to {DURATION_DAYS} days starting {start_date.strftime('%Y-%m-%d')}...")
        l2_times, l2_pos_geo, l2_vel_geo = filter_time_range(
            l2_times, l2_pos_geo, l2_vel_geo, start_date, DURATION_DAYS
        )
        
        # Convert L2 to barycentric
        l2_pos_bary, l2_vel_bary, _, _, _, _ = convert_to_barycentric(
            l2_pos_geo, l2_vel_geo,
            sun_pos_geocentric[:len(l2_times)], sun_vel_geocentric[:len(l2_times)]
        )
        
        print(f"✓ SEMB-L2 retrieved and converted to barycentric")
        print(f"  L2 barycentric[0] norm: {np.linalg.norm(l2_pos_bary[0]):.2e} km")
        use_true_l2 = True
        
    except Exception as e:
        print(f"✗ Could not retrieve SEMB-L2-horizon satellite: {e}")
        print(f"  Falling back to approximate L2 calculation")
    
    # Get each satellite and transform
    trajectories_sem_l2 = {}
    earth_trajectory_sem_l2 = None  # Will store Earth position in SEM-L2
    
    for sat_name in SATELLITE_NAMES:
        print(f"\n{'='*70}")
        print(f"Processing: {sat_name}")
        print(f"{'='*70}")
        
        try:
            # Get satellite data (geocentric)
            sat_times, sat_pos_geo, sat_vel_geo = get_satellite_state_vectors(
                root, scenario, sat_name, TIMESTEP_SECONDS
            )
            
            # Filter to time range
            print(f"  Filtering to {DURATION_DAYS} days starting {start_date.strftime('%Y-%m-%d')}...")
            sat_times, sat_pos_geo, sat_vel_geo = filter_time_range(
                sat_times, sat_pos_geo, sat_vel_geo, start_date, DURATION_DAYS
            )
            
            # Interpolate Sun/Earth if needed
            if len(sun_times) != len(sat_times):
                print(f"  Interpolating Sun/Earth to match satellite times...")
                sat_times_array = np.array(sat_times, dtype=float)
                sun_times_array = np.array(sun_times, dtype=float)
                
                sun_geo_interp = np.zeros((len(sat_times), 3))
                sun_vel_geo_interp = np.zeros((len(sat_times), 3))
                for i in range(3):
                    sun_geo_interp[:, i] = np.interp(sat_times_array, sun_times_array, 
                                                     sun_pos_geocentric[:, i])
                    sun_vel_geo_interp[:, i] = np.interp(sat_times_array, sun_times_array, 
                                                         sun_vel_geocentric[:, i])
                
                # Recompute barycentric
                _, _, earth_pos, earth_vel, sun_pos, sun_vel = convert_to_barycentric(
                    np.zeros_like(sun_geo_interp),
                    np.zeros_like(sun_vel_geo_interp),
                    sun_geo_interp,
                    sun_vel_geo_interp
                )
                sun_geocentric = sun_geo_interp
                sun_vel_geocentric_interp = sun_vel_geo_interp
                
                # Interpolate L2 if using true L2
                if use_true_l2:
                    l2_pos_sat = np.zeros((len(sat_times), 3))
                    l2_vel_sat = np.zeros((len(sat_times), 3))
                    l2_times_array = np.array(l2_times, dtype=float)
                    for i in range(3):
                        l2_pos_sat[:, i] = np.interp(sat_times_array, l2_times_array, 
                                                        l2_pos_bary[:, i])
                        l2_vel_sat[:, i] = np.interp(sat_times_array, l2_times_array, 
                                                        l2_vel_bary[:, i])
                else:
                    l2_pos_sat = l2_pos_bary
                    l2_vel_sat = l2_vel_bary
            else:
                earth_pos = earth_pos_bary
                earth_vel = earth_vel_bary
                sun_pos = sun_pos_bary
                sun_vel = sun_vel_bary
                sun_geocentric = sun_pos_geocentric
                sun_vel_geocentric_interp = sun_vel_geocentric
                l2_pos_sat = l2_pos_bary
                l2_vel_sat = l2_vel_bary
            
            # Convert satellite to barycentric
            sat_pos_bary, sat_vel_bary, _, _, _, _ = convert_to_barycentric(
                sat_pos_geo, sat_vel_geo,
                sun_geocentric, sun_vel_geocentric_interp
            )
            
            print(f"  Satellite geocentric[0] norm: {np.linalg.norm(sat_pos_geo[0]):.2e} km")
            print(f"  Satellite barycentric[0] norm: {np.linalg.norm(sat_pos_bary[0]):.2e} km")
            
            # Transform to SEM-L2
            if use_true_l2:
                print(f"  Transforming to SEM-L2 (using true L2)...")
                pos_sem_l2, vel_sem_l2 = transform_trajectory_to_sem_l2_true(
                    sat_times, sat_pos_bary, sat_vel_bary,
                    l2_pos_sat, l2_vel_sat,
                    sun_pos
                )
            else:
                print(f"  Transforming to SEM-L2 (using approximate L2)...")
                pos_sem_l2, vel_sem_l2 = transform_trajectory_to_sem_l2(
                    sat_times, sat_pos_bary, sat_vel_bary,
                    sun_pos, sun_vel,
                    earth_pos, earth_vel,
                    sun_geocentric, sun_vel_geocentric_interp
                )
            
            trajectories_sem_l2[sat_name] = pos_sem_l2
            
            # Calculate Earth position in SEM-L2 (only need to do once)
            if earth_trajectory_sem_l2 is None:
                print(f"  Computing Earth position in SEM-L2...")
                earth_trajectory_sem_l2 = np.zeros((len(sat_times), 3))
                
                if use_true_l2:
                    # Use true L2 for frame definition
                    for i in range(len(sat_times)):
                        _, _, _, R = build_sem_l2_axes_from_true_l2(
                            l2_pos_sat[i], l2_vel_sat[i], sun_pos[i]
                        )
                        dr_earth = earth_pos[i] - l2_pos_sat[i]
                        earth_trajectory_sem_l2[i] = R @ dr_earth
                    # Diagnostics: print raw Earth Z samples and basic stats
                    sample_count = min(10, len(sat_times))
                    earth_z_samples = earth_trajectory_sem_l2[:sample_count, 2]
                    print("    Diagnostic (Earth Z in SEM-L2 frame, first {} points):".format(sample_count))
                    print("      " + ", ".join(f"{z:.3f}" for z in earth_z_samples))
                    print("    Earth Z stats: min={:.3f} km, max={:.3f} km, mean={:.3f} km".format(
                        np.min(earth_trajectory_sem_l2[:, 2]),
                        np.max(earth_trajectory_sem_l2[:, 2]),
                        np.mean(earth_trajectory_sem_l2[:, 2])
                    ))
                else:
                    # Fallback: Earth position is just relative to Sun (less accurate)
                    print(f"    WARNING: Using approximate mode - Earth position may be inaccurate")
                    earth_trajectory_sem_l2 = earth_pos - sun_pos  # Simple relative position
                    # Diagnostics for approximate case
                    sample_count = min(10, len(sat_times))
                    earth_z_samples = earth_trajectory_sem_l2[:sample_count, 2]
                    print("    Diagnostic (Earth Z approx SEM-L2 frame, first {} points):".format(sample_count))
                    print("      " + ", ".join(f"{z:.3f}" for z in earth_z_samples))
                    print("    Earth Z stats: min={:.3f} km, max={:.3f} km, mean={:.3f} km".format(
                        np.min(earth_trajectory_sem_l2[:, 2]),
                        np.max(earth_trajectory_sem_l2[:, 2]),
                        np.mean(earth_trajectory_sem_l2[:, 2])
                    ))
                
                print(f"    Earth position in SEM-L2:")
                print(f"      X: [{np.min(earth_trajectory_sem_l2[:, 0]):.0f}, {np.max(earth_trajectory_sem_l2[:, 0]):.0f}] km")
                print(f"      Y: [{np.min(earth_trajectory_sem_l2[:, 1]):.0f}, {np.max(earth_trajectory_sem_l2[:, 1]):.0f}] km")
                print(f"      Z: [{np.min(earth_trajectory_sem_l2[:, 2]):.0f}, {np.max(earth_trajectory_sem_l2[:, 2]):.0f}] km")
            
            print(f"  ✓ Transformation complete")
            print(f"    Position range:")
            print(f"      X: [{np.min(pos_sem_l2[:, 0]):.0f}, {np.max(pos_sem_l2[:, 0]):.0f}] km")
            print(f"      Y: [{np.min(pos_sem_l2[:, 1]):.0f}, {np.max(pos_sem_l2[:, 1]):.0f}] km")
            print(f"      Z: [{np.min(pos_sem_l2[:, 2]):.0f}, {np.max(pos_sem_l2[:, 2]):.0f}] km")
            
        except Exception as e:
            print(f"  ✗ Failed to process {sat_name}: {e}")
            continue
    
    # Create plots
    print(f"\n{'='*70}")
    print("Creating visualizations...")
    print(f"{'='*70}")
    
    plots_dir = Path(__file__).parent / "plots"
    plots_dir.mkdir(exist_ok=True)
    
    if len(trajectories_sem_l2) > 0:
        if ENABLE_3D_PLOT:
            # Build filename from the title
            output_filename = title_to_filename(PLOT_TITLE, 'png')
            output_path = plots_dir / output_filename

            fig = plot_trajectories_3d(
                trajectories_sem_l2,
                earth_pos=earth_trajectory_sem_l2,
                title=(PLOT_TITLE if PLOT_SHOW_TITLE else None),
                save_path=output_path,
                colors=TRAJECTORY_COLORS,
                labels=TRAJECTORY_LABELS,
                plot_settings=PLOT_SETTINGS
            )
            
            print(f"\nSaved plot as: {output_path}")
            print(f"✓ Successfully processed {len(trajectories_sem_l2)} trajectories")
            
            # Show interactive plot with toolbar
            print("\nDisplaying interactive plot...")
            plt.show()
        else:
            print("Skipping 3D plot generation (disabled)")
            print(f"✓ Successfully processed {len(trajectories_sem_l2)} trajectories")
    else:
        print("\n✗ No trajectories were successfully processed")
    
    print("\n=== Complete! ===")


if __name__ == "__main__":
    main()
