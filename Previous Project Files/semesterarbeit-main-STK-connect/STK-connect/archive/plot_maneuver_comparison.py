"""
Plot and compare JWST trajectories with different velocity maneuvers in SEM-L2 frame.

This script transforms multiple satellite trajectories:
- horizon-JWST: Original trajectory from launch
- Webb-no-correction: Trajectory without correction maneuver
- Webb-Vx-p1, Webb-Vx-m1: X-direction velocity corrections (+/-)
- Webb-Vy-p1, Webb-Vy-m1: Y-direction velocity corrections (+/-)
- Webb-Vz-p1, Webb-Vz-m1: Z-direction velocity corrections (+/-)

All trajectories are transformed to the SEM-L2 rotating synodic frame.
"""

import sys
import os
from pathlib import Path

# Add Scripts folder to path to find pywin32 modules
scripts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'SA-venv', 'Scripts'))
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

import win32com.client
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# ============================================================================
# USER SETTINGS - Modify these to customize the analysis and plots
# ============================================================================

# Time range settings
START_DATE_YEAR = 2022
START_DATE_MONTH = 10
START_DATE_DAY = 6
DURATION_DAYS = 359 * 1 +2
# DURATION_DAYS = 360*5

# STK connection settings
TIMESTEP_SECONDS = 3600  # Data sampling interval (1 hour)

# Satellite names to analyze
SATELLITE_NAMES = [
    "JWST",
    "Webb-no-correction",
    # "Webb-Vx-p1",
    # "Webb-Vx-m1",
    # "Webb-Vy-p1",
    # "Webb-Vy-m1",
    "Webb-Vz-p1",
    "Webb-Vz-m1",
    # "Base",
    # "Webb-Actual-with-bias",
]

# Plot settings
PLOT_SETTINGS = {
    'figsize': (16, 12),
    'dpi': 300,
    'linewidth': 1.5,
    'alpha': 0.7,
    
    # JWST reference trajectory settings (highlighter effect)
    'jwst_linewidth': 8,      # Thick line for JWST highlight
    'jwst_alpha': 0.3, #0.3,        # More transparent (highlighter effect)
    'jwst_centerline_width': 1.0,  # Thin centerline
    'jwst_centerline_alpha': 0.8,  # Centerline transparency
    'jwst_zorder': 1,         # Draw JWST highlight first (in background)
    'jwst_centerline_zorder': 1, #3,  # Draw centerline on top of everything
    'other_zorder': 2,        # Draw other trajectories in middle
    
    # Font sizes (2D plots)
    'title_fontsize': 16,
    'subtitle_fontsize': 14,
    'label_fontsize': 14,
    'legend_fontsize': 11,
    'tick_fontsize': 12,
    
    # Font sizes (3D plot - separate settings)
    'label_fontsize_3d': 11,
    'tick_fontsize_3d': 10,
    
    # Subplot spacing
    'left': 0.07,
    'bottom': 0.07,
    'right': 0.994,
    'top': 0.92,
    'hspace': 0.24,
    'wspace': 0.25,
    
    # Marker sizes
    'l2_marker_size': 150,      # L2 marker size (2D plots)
    'l2_marker_size_3d': 200,   # L2 marker size (3D plot)
    'earth_marker_size': 100,   # Earth marker size
}

# Color scheme for trajectories
TRAJECTORY_COLORS = {
    'JWST': "#000000",      # Black
    'Webb-no-correction': "#ff00ff",   # Magenta
    'Webb-Vx-p1': "#00ff00",          # Green
    'Webb-Vx-m1': "#008000",          # Dark green
    'Webb-Vy-p1': "#ff0000",          # Red
    'Webb-Vy-m1': "#800000",          # Dark red
    'Webb-Vz-p1': "#0000ff",          # Blue
    'Webb-Vz-m1': '#000080',          # Dark blue
    'Webb-Actual-with-bias': "#FF0000",  # Red
    'Base': "#FF0000",                # Red
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
    'Webb-Actual-with-bias': "Simulation",
    'Base': "Simulation",
}

# Add a user-configurable plot title
PLOT_TITLE = "test-pre-refactoring-maneuver_comparison_sem_l2-closeup-v2-Z"
# Toggle: show/hide the plot title (filename still uses PLOT_TITLE)
PLOT_SHOW_TITLE = False

# ============================================================================
# END USER SETTINGS
# ============================================================================

# Physical constants
M_SUN = 1.989e30  # kg
M_EARTH = 5.972e24  # kg
AU_KM = 149597870.7  # km

# Utility: turn a title into a safe Windows filename
def title_to_filename(title: str, ext: str = "png") -> str:
    s = (title or "").strip()
    # Replace invalid characters with underscores
    s = ''.join(c if c.isalnum() or c in (' ', '-', '_', '.') else '_' for c in s)
    # Collapse whitespace to single underscores
    s = '_'.join(s.split())
    # Trim leading/trailing dots/underscores
    s = s.strip('._')
    if not s:
        s = "plot"
    # Avoid Windows reserved device names
    reserved = {
        'CON','PRN','AUX','NUL',
        'COM1','COM2','COM3','COM4','COM5','COM6','COM7','COM8','COM9',
        'LPT1','LPT2','LPT3','LPT4','LPT5','LPT6','LPT7','LPT8','LPT9'
    }
    if s.upper() in reserved:
        s = f"_{s}"
    # Limit length
    s = s[:120]
    return f"{s}.{ext}"


def connect_to_stk():
    """Connect to running STK instance"""
    print("Connecting to STK 13...")
    uiApp = win32com.client.Dispatch("STK13.Application")
    uiApp.Visible = True
    root = uiApp.Personality2
    scenario = root.CurrentScenario
    print(f"Connected to scenario: {scenario.InstanceName}")
    return root, scenario


def get_body_state_vectors(root, scenario, body_name, timestep_seconds):
    """
    Get state vectors for a celestial body (Sun, Earth, etc.)
    Returns geocentric positions in ICRF frame.
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
            raise Exception(f"Could not find {body_name} as Planet or Star")
    
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


def get_satellite_state_vectors(root, scenario, sat_name, timestep_seconds):
    """
    Get state vectors for a satellite.
    Returns geocentric positions in ICRF frame.
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
    
    print(f"Retrieved {len(times)} data points for {sat_name}")
    return times, positions, velocities


def compute_l2_position_approximate(r_sun, r_earth):
    """Compute approximate L2 position using cubic approximation (geocentric frame)"""
    r_es = r_earth - r_sun
    a = np.linalg.norm(r_es)
    mu = M_EARTH / (M_SUN + M_EARTH)
    d = a * (mu / 3) ** (1/3)
    r_l2 = r_earth + d * (r_es / a)
    return r_l2


def build_sem_l2_axes(r_sun, r_earth, v_earth, fixed_ecliptic_normal=None):
    """
    Build SEM-L2 coordinate frame axes with fixed ecliptic normal.
    Uses geocentric positions for geometry.
    """
    # Compute L2 position (geocentric)
    r_l2 = compute_l2_position_approximate(r_sun, r_earth)
    
    # X-axis: from Sun to L2
    r_sun_to_l2 = r_l2 - r_sun
    x_hat = r_sun_to_l2 / np.linalg.norm(r_sun_to_l2)
    
    # Z-axis: ecliptic north (use fixed normal if provided)
    if fixed_ecliptic_normal is not None:
        z_hat = fixed_ecliptic_normal / np.linalg.norm(fixed_ecliptic_normal)
    else:
        # Fallback: use Earth's orbital angular momentum
        n_ecl = np.cross(r_earth, v_earth)
        z_hat = n_ecl / np.linalg.norm(n_ecl)
    
    # Y-axis: completes right-handed system
    y_hat = np.cross(z_hat, x_hat)
    y_hat = y_hat / np.linalg.norm(y_hat)
    
    # Rotation matrix (from ICRF to SEM-L2)
    R = np.vstack([x_hat, y_hat, z_hat])
    
    return x_hat, y_hat, z_hat, R


def compute_l2_velocity(r_sun_1, r_earth_1, r_sun_2, r_earth_2, dt):
    """Compute L2 velocity using finite differences (geocentric frame)"""
    r_l2_1 = compute_l2_position_approximate(r_sun_1, r_earth_1)
    r_l2_2 = compute_l2_position_approximate(r_sun_2, r_earth_2)
    v_l2 = (r_l2_2 - r_l2_1) / dt
    return v_l2


def compute_frame_angular_velocity(R1, R2, dt):
    """Compute frame angular velocity from two rotation matrices"""
    dR = (R2 - R1) / dt
    omega_skew = dR @ R1.T
    omega = np.array([
        omega_skew[2, 1],
        omega_skew[0, 2],
        omega_skew[1, 0]
    ])
    return omega


def transform_trajectory_to_sem_l2(times, positions_icrf, velocities_icrf,
                                     sun_positions, sun_velocities,
                                     earth_positions, earth_velocities,
                                     sun_geocentric=None, sun_vel_geocentric=None):
    """
    Transform trajectory to SEM-L2 frame with fixed ecliptic normal.
    
    Args:
        positions_icrf: Barycentric positions (km)
        sun_positions: Barycentric Sun positions (km)
        earth_positions: Barycentric Earth positions (km)
        sun_geocentric: Geocentric Sun for frame geometry (optional)
    """
    n_points = len(times)
    positions_sem_l2 = np.zeros_like(positions_icrf)
    velocities_sem_l2 = np.zeros_like(velocities_icrf)
    
    # Use geocentric Sun if provided for frame geometry
    if sun_geocentric is not None:
        earth_geo = np.zeros_like(earth_positions)  # Earth at origin
        sun_geo = sun_geocentric
        sun_vel_geo = sun_vel_geocentric
    else:
        earth_geo = earth_positions
        sun_geo = sun_positions
        sun_vel_geo = sun_velocities
    
    # Compute mean ecliptic normal from barycentric Earth orbit
    ecliptic_normals = []
    for i in range(min(100, n_points)):
        r_earth_norm = np.linalg.norm(earth_positions[i])
        if r_earth_norm > 1.0:
            n_ecl = np.cross(earth_positions[i], earth_velocities[i])
            norm_n_ecl = np.linalg.norm(n_ecl)
            if norm_n_ecl > 1e-6:
                ecliptic_normals.append(n_ecl / norm_n_ecl)
    
    if len(ecliptic_normals) > 0:
        mean_ecliptic_normal = np.mean(ecliptic_normals, axis=0)
        mean_ecliptic_normal = mean_ecliptic_normal / np.linalg.norm(mean_ecliptic_normal)
    else:
        mean_ecliptic_normal = np.array([0, 0, 1])
    
    # Transform each point
    for i in range(n_points - 1):
        # Position transformation
        r_l2 = compute_l2_position_approximate(sun_geo[i], earth_geo[i])
        if sun_geocentric is not None:
            r_l2_bary = earth_positions[i] + r_l2  # L2 in barycentric frame
        else:
            r_l2_bary = r_l2
        
        _, _, _, R = build_sem_l2_axes(sun_geo[i], earth_geo[i], 
                                        earth_velocities[i], mean_ecliptic_normal)
        dr = positions_icrf[i] - r_l2_bary
        positions_sem_l2[i] = R @ dr
        
        # Velocity transformation
        dt = times[i+1] - times[i]
        v_l2 = compute_l2_velocity(sun_geo[i], earth_geo[i],
                                    sun_geo[i+1], earth_geo[i+1], dt)
        if sun_geocentric is not None:
            v_l2_bary = earth_velocities[i] + v_l2
        else:
            v_l2_bary = v_l2
        
        _, _, _, R_next = build_sem_l2_axes(sun_geo[i+1], earth_geo[i+1],
                                             earth_velocities[i+1], mean_ecliptic_normal)
        omega_vec = compute_frame_angular_velocity(R, R_next, dt)
        
        dv = velocities_icrf[i] - v_l2_bary
        v_sem_l2_uncorrected = R @ dv
        velocities_sem_l2[i] = v_sem_l2_uncorrected - np.cross(omega_vec, positions_sem_l2[i])
    
    # Handle last point
    r_l2 = compute_l2_position_approximate(sun_geo[-1], earth_geo[-1])
    if sun_geocentric is not None:
        r_l2_bary = earth_positions[-1] + r_l2
    else:
        r_l2_bary = r_l2
    
    _, _, _, R = build_sem_l2_axes(sun_geo[-1], earth_geo[-1],
                                    earth_velocities[-1], mean_ecliptic_normal)
    dr = positions_icrf[-1] - r_l2_bary
    positions_sem_l2[-1] = R @ dr
    velocities_sem_l2[-1] = velocities_sem_l2[-2]  # Copy previous
    
    return positions_sem_l2, velocities_sem_l2


def filter_time_range(times, positions, velocities, start_date, duration_days):
    """
    Filter data to only include specified time range.
    
    Args:
        times: Array of epoch seconds
        positions: Position array (N, 3)
        velocities: Velocity array (N, 3)
        start_date: datetime object for start
        duration_days: Duration in days
    
    Returns:
        Filtered times, positions, velocities
    """
    from datetime import datetime, timedelta
    
    # STK epoch is typically January 1, 2000 12:00:00 UTC (J2000)
    # But we need to work with the actual scenario epoch
    # For simplicity, we'll use the first time value as reference
    
    # Convert start_date to days since first data point
    # Assume times[0] corresponds to some known date
    # We'll compute the offset based on April 7, 2022
    
    # JWST launched on Dec 25, 2021
    # April 7, 2022 is 103 days after launch
    # We need to find the index corresponding to this
    
    launch_date = datetime(2021, 12, 25, 12, 19, 0)  # JWST launch time
    days_since_launch = (start_date - launch_date).total_seconds() / 86400
    
    # Convert to seconds since first data point
    start_offset_seconds = days_since_launch * 86400
    end_offset_seconds = start_offset_seconds + (duration_days * 86400)
    
    # Find time range relative to first data point
    time_relative = times - times[0]
    
    # Find indices within range
    mask = (time_relative >= start_offset_seconds) & (time_relative <= end_offset_seconds)
    
    if np.sum(mask) == 0:
        print(f"  WARNING: No data points found in specified range!")
        print(f"    Requested: {start_offset_seconds/86400:.1f} to {end_offset_seconds/86400:.1f} days")
        print(f"    Available: 0 to {(times[-1]-times[0])/86400:.1f} days")
        return times, positions, velocities
    
    times_filtered = times[mask]
    positions_filtered = positions[mask]
    velocities_filtered = velocities[mask]
    
    n_filtered = len(times_filtered)
    n_total = len(times)
    print(f"  Filtered to {n_filtered}/{n_total} points ({n_filtered/n_total*100:.1f}%)")
    print(f"    Time range: {(times_filtered[0]-times[0])/86400:.1f} to {(times_filtered[-1]-times[0])/86400:.1f} days after start")
    
    return times_filtered, positions_filtered, velocities_filtered


def plot_trajectories_3d(trajectories_dict, earth_pos=None, 
                         title="JWST Trajectories in SEM-L2 Frame", 
                         save_path=None,
                         colors=None,
                         labels=None,
                         plot_settings=None,
                         lock_scale_to_jwst=True):
    """
    Plot multiple trajectories in 3D.
    
    Args:
        trajectories_dict: Dict of {name: positions} where positions is (N, 3) array
        earth_pos: Earth position trajectory in SEM-L2 (N, 3) array
        title: Main plot title
        save_path: Path to save figure
        colors: Dict of {trajectory_name: color}
        labels: Dict of {trajectory_name: display_label}
        plot_settings: Dict with plot customization settings
        lock_scale_to_jwst: If True, scale axes based on JWST trajectory only (no rescaling for others)
    """
    # Use default settings if not provided
    if colors is None:
        colors = TRAJECTORY_COLORS
    if labels is None:
        labels = TRAJECTORY_LABELS
    if plot_settings is None:
        plot_settings = PLOT_SETTINGS
    
    fig = plt.figure(figsize=plot_settings['figsize'])
    
    # Create 4 subplots: 3D, XY, XZ, YZ
    ax1 = fig.add_subplot(221, projection='3d')
    ax2 = fig.add_subplot(222)  # XY plane
    ax3 = fig.add_subplot(223)  # XZ plane
    ax4 = fig.add_subplot(224)  # YZ plane
    
    # If locking scale to JWST, compute bounds first
    if lock_scale_to_jwst and 'horizon-JWST' in trajectories_dict:
        jwst_pos = trajectories_dict['horizon-JWST']
        jwst_x = jwst_pos[:, 0] / 1e6
        jwst_y = jwst_pos[:, 1] / 1e6
        jwst_z = jwst_pos[:, 2] / 1e6
        
        # Include Earth position in bounds calculation for 3D
        all_x_3d = list(jwst_x)
        all_y_3d = list(jwst_y)
        all_z_3d = list(jwst_z)
        
        if earth_pos is not None:
            all_x_3d.append(earth_pos[0, 0] / 1e6)
            all_y_3d.append(earth_pos[0, 1] / 1e6)
            all_z_3d.append(earth_pos[0, 2] / 1e6)
        
        max_range_3d = max(
            max(all_x_3d) - min(all_x_3d),
            max(all_y_3d) - min(all_y_3d),
            max(all_z_3d) - min(all_z_3d)
        ) / 2
        
        mid_x_3d = (max(all_x_3d) + min(all_x_3d)) / 2
        mid_y_3d = (max(all_y_3d) + min(all_y_3d)) / 2
        mid_z_3d = (max(all_z_3d) + min(all_z_3d)) / 2
        
        # 2D scales (in 1000 km) - also include Earth
        jwst_x_2d = jwst_pos[:, 0] / 1000
        jwst_y_2d = jwst_pos[:, 1] / 1000
        jwst_z_2d = jwst_pos[:, 2] / 1000
        
        all_x_xy = list(jwst_x_2d)
        all_y_xy = list(jwst_y_2d)
        all_x_xz = list(jwst_x_2d)
        all_z_xz = list(jwst_z_2d)
        all_y_yz = list(jwst_y_2d)
        all_z_yz = list(jwst_z_2d)
        
        if earth_pos is not None:
            all_x_xy.append(earth_pos[0, 0] / 1000)
            all_y_xy.append(earth_pos[0, 1] / 1000)
            all_x_xz.append(earth_pos[0, 0] / 1000)
            all_z_xz.append(earth_pos[0, 2] / 1000)
            all_y_yz.append(earth_pos[0, 1] / 1000)
            all_z_yz.append(earth_pos[0, 2] / 1000)
        
        max_range_xy = max(
            max(all_x_xy) - min(all_x_xy),
            max(all_y_xy) - min(all_y_xy)
        ) / 2
        mid_x_xy = (max(all_x_xy) + min(all_x_xy)) / 2
        mid_y_xy = (max(all_y_xy) + min(all_y_xy)) / 2
        
        max_range_xz = max(
            max(all_x_xz) - min(all_x_xz),
            max(all_z_xz) - min(all_z_xz)
        ) / 2
        mid_x_xz = (max(all_x_xz) + min(all_x_xz)) / 2
        mid_z_xz = (max(all_z_xz) + min(all_z_xz)) / 2
        
        max_range_yz = max(
            max(all_y_yz) - min(all_y_yz),
            max(all_z_yz) - min(all_z_yz)
        ) / 2
        mid_y_yz = (max(all_y_yz) + min(all_y_yz)) / 2
        mid_z_yz = (max(all_z_yz) + min(all_z_yz)) / 2
    # Plot JWST first as thick transparent background (if present)
    if 'horizon-JWST' in trajectories_dict:
        pos = trajectories_dict['horizon-JWST']
        color = colors.get('horizon-JWST', 'black')
        label = labels.get('horizon-JWST', 'horizon-JWST')
        
        # 3D plot - thick transparent highlight with rounded caps
        ax1.plot(pos[:, 0]/1e6, pos[:, 1]/1e6, pos[:, 2]/1e6, 
                color=color, alpha=plot_settings['jwst_alpha'], 
                linewidth=plot_settings['jwst_linewidth'],
                solid_capstyle='round',
                zorder=plot_settings['jwst_zorder'])
        
        # 2D projections - thick transparent highlight with rounded caps and label only in XY
        ax2.plot(pos[:, 0]/1000, pos[:, 1]/1000, label=label, color=color, 
                alpha=plot_settings['jwst_alpha'], 
                linewidth=plot_settings['jwst_linewidth'],
                solid_capstyle='round',
                zorder=plot_settings['jwst_zorder'])
        ax3.plot(pos[:, 0]/1000, pos[:, 2]/1000, color=color, 
                alpha=plot_settings['jwst_alpha'], 
                linewidth=plot_settings['jwst_linewidth'],
                solid_capstyle='round',
                zorder=plot_settings['jwst_zorder'])
        ax4.plot(pos[:, 1]/1000, pos[:, 2]/1000, color=color, 
                alpha=plot_settings['jwst_alpha'], 
                linewidth=plot_settings['jwst_linewidth'],
                solid_capstyle='round',
                zorder=plot_settings['jwst_zorder'])
    
    # Plot other trajectories on top with normal settings
    for name, pos in trajectories_dict.items():
        if name == 'horizon-JWST':
            continue  # Already plotted (will add centerline later)
            
        color = colors.get(name, 'black')
        label = labels.get(name, name)
        
        # 3D plot (no label for legend) - scale to 10^6 km
        ax1.plot(pos[:, 0]/1e6, pos[:, 1]/1e6, pos[:, 2]/1e6, 
                color=color, alpha=plot_settings['alpha'], 
                linewidth=plot_settings['linewidth'],
                zorder=plot_settings['other_zorder'])
        
        # 2D projections (only XY gets labels) - keep at 1000 km
        ax2.plot(pos[:, 0]/1000, pos[:, 1]/1000, label=label, color=color, 
                alpha=plot_settings['alpha'], 
                linewidth=plot_settings['linewidth'],
                zorder=plot_settings['other_zorder'])
        ax3.plot(pos[:, 0]/1000, pos[:, 2]/1000, color=color, 
                alpha=plot_settings['alpha'], 
                linewidth=plot_settings['linewidth'],
                zorder=plot_settings['other_zorder'])
        ax4.plot(pos[:, 1]/1000, pos[:, 2]/1000, color=color, 
                alpha=plot_settings['alpha'], 
                linewidth=plot_settings['linewidth'],
                zorder=plot_settings['other_zorder'])
    
    # Plot JWST centerline on top of everything (if present)
    if 'horizon-JWST' in trajectories_dict:
        pos = trajectories_dict['horizon-JWST']
        color = colors.get('horizon-JWST', 'black')
        
        # 3D plot - thin centerline with rounded caps
        ax1.plot(pos[:, 0]/1e6, pos[:, 1]/1e6, pos[:, 2]/1e6, 
                color=color, alpha=plot_settings['jwst_centerline_alpha'], 
                linewidth=plot_settings['jwst_centerline_width'],
                solid_capstyle='round',
                zorder=plot_settings['jwst_centerline_zorder'])
        
        # 2D projections - thin centerline with rounded caps (no label, already labeled with highlight)
        ax2.plot(pos[:, 0]/1000, pos[:, 1]/1000, color=color, 
                alpha=plot_settings['jwst_centerline_alpha'], 
                linewidth=plot_settings['jwst_centerline_width'],
                solid_capstyle='round',
                zorder=plot_settings['jwst_centerline_zorder'])
        ax3.plot(pos[:, 0]/1000, pos[:, 2]/1000, color=color, 
                alpha=plot_settings['jwst_centerline_alpha'], 
                linewidth=plot_settings['jwst_centerline_width'],
                solid_capstyle='round',
                zorder=plot_settings['jwst_centerline_zorder'])
        ax4.plot(pos[:, 1]/1000, pos[:, 2]/1000, color=color, 
                alpha=plot_settings['jwst_centerline_alpha'], 
                linewidth=plot_settings['jwst_centerline_width'],
                solid_capstyle='round',
                zorder=plot_settings['jwst_centerline_zorder'])
    
    # L2 at origin (only labeled in XY plot)
    ax1.scatter([0], [0], [0], c='gold', s=plot_settings['l2_marker_size_3d'], 
               marker='*', edgecolors='orange', linewidths=2, zorder=1000)
    ax2.scatter([0], [0], c='gold', s=plot_settings['l2_marker_size'], marker='*', 
               label='L2', edgecolors='orange', linewidths=2, zorder=1000)
    ax3.scatter([0], [0], c='gold', s=plot_settings['l2_marker_size'], marker='*', 
               edgecolors='orange', linewidths=2, zorder=1000)
    ax4.scatter([0], [0], c='gold', s=plot_settings['l2_marker_size'], marker='*', 
               edgecolors='orange', linewidths=2, zorder=1000)
    
    # Earth position (if provided) - only labeled in XY plot
    if earth_pos is not None:
        # Mark Earth start position - 3D uses 10^6 km scale
        ax1.scatter([earth_pos[0, 0]/1e6], [earth_pos[0, 1]/1e6], [earth_pos[0, 2]/1e6],
                   c='darkblue', s=plot_settings['earth_marker_size'], marker='o', 
                   edgecolors='blue', linewidths=2, zorder=900)
        ax2.scatter([earth_pos[0, 0]/1000], [earth_pos[0, 1]/1000],
                   c='darkblue', s=plot_settings['earth_marker_size'], marker='o', 
                   label='Earth', edgecolors='blue', linewidths=2, zorder=900)
        ax3.scatter([earth_pos[0, 0]/1000], [earth_pos[0, 2]/1000],
                   c='darkblue', s=plot_settings['earth_marker_size'], marker='o', 
                   edgecolors='blue', linewidths=2, zorder=900)
        ax4.scatter([earth_pos[0, 1]/1000], [earth_pos[0, 2]/1000],
                   c='darkblue', s=plot_settings['earth_marker_size'], marker='o', 
                   edgecolors='blue', linewidths=2, zorder=900)
    
    # Format 3D plot (no legend) - uses separate 3D font sizes and 10^6 km scale
    ax1.set_xlabel('X (10⁶ km)\n← Toward Sun', fontsize=plot_settings['label_fontsize_3d'])
    ax1.set_ylabel('Y (10⁶ km)', fontsize=plot_settings['label_fontsize_3d'])
    ax1.set_zlabel('Z (10⁶ km)\nEcliptic North →', fontsize=plot_settings['label_fontsize_3d'])
    ax1.set_title('3D View', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax1.tick_params(labelsize=plot_settings['tick_fontsize_3d'])
    ax1.grid(True, alpha=0.3)
    
    # Set axis limits
    if lock_scale_to_jwst and 'horizon-JWST' in trajectories_dict:
        # Use pre-computed JWST-based scales
        ax1.set_xlim(mid_x_3d - max_range_3d, mid_x_3d + max_range_3d)
        ax1.set_ylim(mid_y_3d - max_range_3d, mid_y_3d + max_range_3d)
        ax1.set_zlim(mid_z_3d - max_range_3d, mid_z_3d + max_range_3d)
        
        ax2.set_xlim(mid_x_xy - max_range_xy, mid_x_xy + max_range_xy)
        ax2.set_ylim(mid_y_xy - max_range_xy, mid_y_xy + max_range_xy)
        
        ax3.set_xlim(mid_x_xz - max_range_xz, mid_x_xz + max_range_xz)
        ax3.set_ylim(mid_z_xz - max_range_xz, mid_z_xz + max_range_xz)
        
        ax4.set_xlim(mid_y_yz - max_range_yz, mid_y_yz + max_range_yz)
        ax4.set_ylim(mid_z_yz - max_range_yz, mid_z_yz + max_range_yz)
    else:
        # Original behavior: scale to fit all trajectories
        all_x = []
        all_y = []
        all_z = []
        for name, pos in trajectories_dict.items():
            all_x.extend(pos[:, 0]/1e6)
            all_y.extend(pos[:, 1]/1e6)
            all_z.extend(pos[:, 2]/1e6)
        if earth_pos is not None:
            all_x.extend(earth_pos[:, 0]/1e6)
            all_y.extend(earth_pos[:, 1]/1e6)
            all_z.extend(earth_pos[:, 2]/1e6)
        
        max_range = max(
            max(all_x) - min(all_x),
            max(all_y) - min(all_y),
            max(all_z) - min(all_z)
        ) / 2
        
        mid_x = (max(all_x) + min(all_x)) / 2
        mid_y = (max(all_y) + min(all_y)) / 2
        mid_z = (max(all_z) + min(all_z)) / 2
        
        ax1.set_xlim(mid_x - max_range, mid_x + max_range)
        ax1.set_ylim(mid_y - max_range, mid_y + max_range)
        ax1.set_zlim(mid_z - max_range, mid_z + max_range)
    
    # Format XY plot (with legend) - keeps 1000 km scale
    ax2.set_xlabel('X (1000 km) ← Toward Sun', fontsize=plot_settings['label_fontsize'])
    ax2.set_ylabel('Y (1000 km)', fontsize=plot_settings['label_fontsize'])
    ax2.set_title('XY Plane (Ecliptic)', fontsize=plot_settings['subtitle_fontsize'], 
                  fontweight='bold')
    ax2.legend(fontsize=plot_settings['legend_fontsize'])
    ax2.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
    ax2.axvline(x=0, color='k', linewidth=0.5, alpha=0.3)
    ax2.axis('equal')
    # Set limits AFTER axis('equal') to enforce them
    if lock_scale_to_jwst and 'horizon-JWST' in trajectories_dict:
        ax2.set_xlim(mid_x_xy - max_range_xy, mid_x_xy + max_range_xy)
        ax2.set_ylim(mid_y_xy - max_range_xy, mid_y_xy + max_range_xy)
    
    # Format XZ plot (no legend)
    ax3.set_xlabel('X (1000 km) ← Toward Sun', fontsize=plot_settings['label_fontsize'])
    ax3.set_ylabel('Z (1000 km) Ecliptic North →', fontsize=plot_settings['label_fontsize'])
    ax3.set_title('XZ Plane', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax3.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax3.grid(True, alpha=0.3)
    ax3.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
    ax3.axvline(x=0, color='k', linewidth=0.5, alpha=0.3)
    ax3.axis('equal')
    # Set limits AFTER axis('equal') to enforce them
    if lock_scale_to_jwst and 'horizon-JWST' in trajectories_dict:
        ax3.set_xlim(mid_x_xz - max_range_xz, mid_x_xz + max_range_xz)
        ax3.set_ylim(mid_z_xz - max_range_xz, mid_z_xz + max_range_xz)
    
    # Format YZ plot (no legend)
    ax4.set_xlabel('Y (1000 km)', fontsize=plot_settings['label_fontsize'])
    ax4.set_ylabel('Z (1000 km) Ecliptic North →', fontsize=plot_settings['label_fontsize'])
    ax4.set_title('YZ Plane', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax4.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax4.grid(True, alpha=0.3)
    ax4.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
    ax4.axvline(x=0, color='k', linewidth=0.5, alpha=0.3)
    ax4.axis('equal')
    # Set limits AFTER axis('equal') to enforce them
    if lock_scale_to_jwst and 'horizon-JWST' in trajectories_dict:
        ax4.set_xlim(mid_y_yz - max_range_yz, mid_y_yz + max_range_yz)
        ax4.set_ylim(mid_z_yz - max_range_yz, mid_z_yz + max_range_yz)
    
    # Only add the main title if provided
    if title is not None and str(title).strip():
        plt.suptitle(title, fontsize=plot_settings['title_fontsize'], fontweight='bold', y=0.98)
    
    # Set custom subplot spacing
    plt.subplots_adjust(
        left=plot_settings['left'], 
        bottom=plot_settings['bottom'], 
        right=plot_settings['right'], 
        top=plot_settings['top'], 
        hspace=plot_settings['hspace'], 
        wspace=plot_settings['wspace']
    )
    
    if save_path:
        plt.savefig(save_path, dpi=plot_settings['dpi'], bbox_inches='tight')
        print(f"Figure saved to {save_path}")
    
    return fig


def main():
    # Connect to STK
    root, scenario = connect_to_stk()
    root.UnitPreferences.SetCurrentUnit("DateFormat", "EpSec")
    
    # Define time range using user settings
    from datetime import datetime, timedelta
    start_date = datetime(START_DATE_YEAR, START_DATE_MONTH, START_DATE_DAY, 0, 0, 0)
    
    # Get scenario start time for reference
    scenario_start = scenario.StartTime  # This is in EpSec
    
    # We'll filter data after retrieval based on the time arrays
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
    M_total = M_SUN + M_EARTH
    f_earth = M_EARTH / M_total
    f_sun = M_SUN / M_total
    
    earth_pos_bary = sun_pos_geocentric * f_sun
    earth_vel_bary = sun_vel_geocentric * f_sun
    sun_pos_bary = -sun_pos_geocentric * f_earth
    sun_vel_bary = -sun_vel_geocentric * f_earth
    
    print(f"✓ Converted to barycentric frame")
    
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
                earth_pos = sun_geo_interp * f_sun
                earth_vel = sun_vel_geo_interp * f_sun
                sun_pos = -sun_geo_interp * f_earth
                sun_vel = -sun_vel_geo_interp * f_earth
                sun_geocentric = sun_geo_interp
                sun_vel_geocentric_interp = sun_vel_geo_interp
            else:
                earth_pos = earth_pos_bary
                earth_vel = earth_vel_bary
                sun_pos = sun_pos_bary
                sun_vel = sun_vel_bary
                sun_geocentric = sun_pos_geocentric
                sun_vel_geocentric_interp = sun_vel_geocentric
            
            # Convert satellite to barycentric
            sat_pos_bary = sat_pos_geo + earth_pos
            sat_vel_bary = sat_vel_geo + earth_vel
            
            print(f"  Satellite geocentric[0] norm: {np.linalg.norm(sat_pos_geo[0]):.2e} km")
            print(f"  Satellite barycentric[0] norm: {np.linalg.norm(sat_pos_bary[0]):.2e} km")
            
            # Transform to SEM-L2
            print(f"  Transforming to SEM-L2...")
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
                for i in range(len(sat_times)):
                    # Earth position in SEM-L2 frame
                    r_l2_geo = compute_l2_position_approximate(sun_geocentric[i], np.zeros(3))
                    r_l2_bary = earth_pos[i] + r_l2_geo
                    _, _, _, R = build_sem_l2_axes(sun_geocentric[i], np.zeros(3),
                                                    earth_vel[i], 
                                                    np.array([3.16e-05, -0.398, 0.918]))  # Fixed ecliptic normal
                    dr_earth = earth_pos[i] - r_l2_bary
                    earth_trajectory_sem_l2[i] = R @ dr_earth
                
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
        plt.show()
        print(f"\nSaved plot as: {output_path}")

        print(f"\n✓ Successfully processed {len(trajectories_sem_l2)} trajectories")
    else:
        print("\n✗ No trajectories were successfully processed")
    
    print("\n=== Complete! ===")


if __name__ == "__main__":
    main()
