"""
Plot offset trajectories of satellite constellation relative to base satellite in SEM-L2 frame.

This script analyzes the relative motion of satellites with small initial position offsets:
- Base: Reference satellite
- X100, X-100: ±100m offset in X direction
- Y100, Y-100: ±100m offset in Y direction
- Z100, Z-100: ±100m offset in Z direction

All offsets are computed in the SEM-L2 rotating synodic frame.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import win32com.client
from datetime import datetime, timedelta

# Add Scripts folder to path to find pywin32 modules
scripts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'SA-venv', 'Scripts'))
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

from mpl_toolkits.mplot3d import Axes3D

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
DURATION_DAYS = 30

# STK connection settings
TIMESTEP_SECONDS = 3600  # Data sampling interval (1 hour)

# Add a user-configurable plot title and output filename
PLOT_TITLE = "satellite_constellation_1000m-offsets_30d"
# Toggle: show/hide the plot title (filename still uses PLOT_TITLE)
PLOT_SHOW_TITLE = False

# Satellite names to analyze
BASE_SATELLITE = "Base"  # Reference satellite
SATELLITE_NAMES = [
    "Base",
    "X1000",
    "X-1000",
    "Y1000",
    "Y-1000",
    "Z1000",
    "Z-1000"
]

# Plot settings - Time series plots
TIME_PLOT_SETTINGS = {
    'figsize': (16, 12),
    'dpi': 300,
    'linewidth': 2.0,
    'alpha': 0.8,
    
    # Font sizes
    'title_fontsize': 16,
    'subtitle_fontsize': 14,
    'label_fontsize': 14,
    'legend_fontsize': 11,
    'tick_fontsize': 12,
    
    # Subplot spacing
    'left': 0.08,
    'bottom': 0.08,
    'right': 0.98,
    'top': 0.93,
    'hspace': 0.30,
    'wspace': 0.25,
    
    # Axis labels
    'xlabel': 'Time (days)',
    'ylabel_offset': 'Offset (km)',
}

# Plot settings - 3D trajectory plots
TRAJECTORY_PLOT_SETTINGS = {
    'figsize': (16, 12),
    'dpi': 300,
    'linewidth': 1.5,
    'alpha': 0.7,
    
    # Font sizes (2D plots)
    'title_fontsize': 16,
    'subtitle_fontsize': 14,
    'label_fontsize': 14,
    'legend_fontsize': 11,
    'tick_fontsize': 12,
    
    # Font sizes (3D plot)
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
    'base_marker_size': 150,      # Base satellite marker (2D)
    'base_marker_size_3d': 200,   # Base satellite marker (3D)
}

# Color scheme for satellite pairs
SATELLITE_COLORS = {
    'Base': "#FF00FF",        # Magenta
    'X1000': '#00ff00',        # Green
    'X-1000': '#008000',       # Dark green
    'Y1000': '#ff0000',        # Red
    'Y-1000': '#800000',       # Dark red
    'Z1000': '#0000ff',        # Blue
    'Z-1000': '#000080',       # Dark blue
}

# Custom labels for satellites (for legend)
SATELLITE_LABELS = {
    'Base': "Base",
    'X1000': "X +1000m",
    'X-1000': "X -1000m",
    'Y1000': "Y +1000m",
    'Y-1000': "Y -1000m",
    'Z1000': "Z +1000m",
    'Z-1000': "Z -1000m",
}

# ============================================================================
# END USER SETTINGS
# ============================================================================

# Physical constants
M_SUN = 1.989e30  # kg
M_EARTH = 5.972e24  # kg
AU_KM = 149597870.7  # km


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
    
    print(f"  Retrieved {len(times)} data points for {sat_name}")
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
            ecliptic_normals.append(n_ecl / np.linalg.norm(n_ecl))
    
    if len(ecliptic_normals) > 0:
        mean_ecliptic_normal = np.mean(ecliptic_normals, axis=0)
        mean_ecliptic_normal = mean_ecliptic_normal / np.linalg.norm(mean_ecliptic_normal)
    else:
        mean_ecliptic_normal = np.array([0, 0, 1])
    
    # Transform each point
    for i in range(n_points - 1):
        r_l2 = compute_l2_position_approximate(sun_geo[i], earth_geo[i])
        
        if sun_geocentric is not None:
            r_l2_bary = r_l2 + earth_positions[i]
        else:
            r_l2_bary = r_l2
        
        _, _, _, R = build_sem_l2_axes(sun_geo[i], earth_geo[i],
                                        earth_velocities[i], mean_ecliptic_normal)
        
        dr = positions_icrf[i] - r_l2_bary
        positions_sem_l2[i] = R @ dr
        
        v_l2 = compute_l2_velocity(sun_geo[i], earth_geo[i],
                                    sun_geo[i+1], earth_geo[i+1],
                                    times[i+1] - times[i])
        
        if sun_geocentric is not None:
            v_l2_bary = v_l2 + earth_velocities[i]
        else:
            v_l2_bary = v_l2
        
        dv = velocities_icrf[i] - v_l2_bary
        
        R_next = build_sem_l2_axes(sun_geo[i+1], earth_geo[i+1],
                                    earth_velocities[i+1], mean_ecliptic_normal)[3]
        omega = compute_frame_angular_velocity(R, R_next, times[i+1] - times[i])
        
        velocities_sem_l2[i] = R @ dv - np.cross(omega, positions_sem_l2[i])
    
    # Handle last point
    r_l2 = compute_l2_position_approximate(sun_geo[-1], earth_geo[-1])
    if sun_geocentric is not None:
        r_l2_bary = r_l2 + earth_positions[-1]
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
    # JWST launched on Dec 25, 2021
    launch_date = datetime(2021, 12, 25, 12, 19, 0)
    days_since_launch = (start_date - launch_date).total_seconds() / 86400
    
    # Convert to seconds since first data point
    start_offset_seconds = days_since_launch * 86400
    end_offset_seconds = start_offset_seconds + (duration_days * 86400)
    
    # Find time range relative to first data point
    time_relative = times - times[0]
    
    # Find indices within range
    mask = (time_relative >= start_offset_seconds) & (time_relative <= end_offset_seconds)
    
    if np.sum(mask) == 0:
        print(f"  WARNING: No data in specified time range!")
        print(f"    Requested: {start_offset_seconds/86400:.1f} to {end_offset_seconds/86400:.1f} days")
        print(f"    Available: 0 to {time_relative[-1]/86400:.1f} days")
        return times, positions, velocities
    
    times_filtered = times[mask]
    positions_filtered = positions[mask]
    velocities_filtered = velocities[mask]
    
    n_filtered = len(times_filtered)
    n_total = len(times)
    print(f"  Filtered to {n_filtered}/{n_total} points ({n_filtered/n_total*100:.1f}%)")
    print(f"    Time range: {(times_filtered[0]-times[0])/86400:.1f} to {(times_filtered[-1]-times[0])/86400:.1f} days after start")
    
    return times_filtered, positions_filtered, velocities_filtered


def compute_relative_positions(trajectories_dict, base_name="Base"):
    """
    Compute position offsets relative to base satellite.
    
    Args:
        trajectories_dict: Dict of {sat_name: positions_sem_l2}
        base_name: Name of reference satellite
    
    Returns:
        offsets_dict: Dict of {sat_name: offset_positions} (excludes base)
    """
    print(f"\nComputing offsets relative to {base_name}...")
    
    if base_name not in trajectories_dict:
        raise ValueError(f"Base satellite '{base_name}' not found in trajectories")
    
    base_positions = trajectories_dict[base_name]
    offsets_dict = {}
    
    for sat_name, positions in trajectories_dict.items():
        if sat_name == base_name:
            continue
        
        offsets = positions - base_positions
        offsets_dict[sat_name] = offsets
        
        # Print statistics
        offset_magnitudes = np.linalg.norm(offsets, axis=1)
        initial_offset = offset_magnitudes[0]
        final_offset = offset_magnitudes[-1]
        max_offset = np.max(offset_magnitudes)
        mean_offset = np.mean(offset_magnitudes)
        
        print(f"  {sat_name:10s}: Initial={initial_offset*1000:6.1f}m, "
              f"Final={final_offset:7.2f}km, Max={max_offset:7.2f}km, Mean={mean_offset:7.2f}km")
    
    return offsets_dict


def plot_offsets_vs_time(times, offsets_dict, save_path=None, 
                         colors=None, labels=None, plot_settings=None, log_scale=True,
                         title=None):
    """
    Create 2×2 time series plots showing offset components and magnitude.
    
    Args:
        times: Time array (epoch seconds)
        offsets_dict: Dict of {sat_name: offset_positions (N, 3)}
        save_path: Path to save figure
        colors: Dict of {sat_name: color}
        labels: Dict of {sat_name: display_label}
        plot_settings: Dict with plot customization settings
        log_scale: If True, use logarithmic y-axis
        title: Optional custom plot title (None to hide title)
    """
    if colors is None:
        colors = SATELLITE_COLORS
    if labels is None:
        labels = SATELLITE_LABELS
    if plot_settings is None:
        plot_settings = TIME_PLOT_SETTINGS
    
    # Convert times to days since start
    times_days = (times - times[0]) / 86400
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=plot_settings['figsize'])
    
    # Plot each satellite's offsets
    for sat_name, offsets in offsets_dict.items():
        color = colors.get(sat_name, 'black')
        label = labels.get(sat_name, sat_name)
        
        if log_scale:
            # X offset (use absolute values for log scale)
            ax1.plot(times_days, np.abs(offsets[:, 0]), 
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], label=label)
            
            # Y offset (use absolute values for log scale)
            ax2.plot(times_days, np.abs(offsets[:, 1]),
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], label=label)
            
            # Z offset (use absolute values for log scale)
            ax3.plot(times_days, np.abs(offsets[:, 2]),
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], label=label)
        else:
            # X offset (linear scale - can show negative values)
            ax1.plot(times_days, offsets[:, 0], 
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], label=label)
            
            # Y offset (linear scale)
            ax2.plot(times_days, offsets[:, 1],
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], label=label)
            
            # Z offset (linear scale)
            ax3.plot(times_days, offsets[:, 2],
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], label=label)
        
        # Total magnitude (always positive)
        magnitude = np.linalg.norm(offsets, axis=1)
        ax4.plot(times_days, magnitude,
                color=color, linewidth=plot_settings['linewidth'],
                alpha=plot_settings['alpha'], label=label)
    
    # Y-axis label prefix
    ylabel_prefix = '|X|' if log_scale else 'X'
    
    # Format X offset subplot
    ax1.set_xlabel(plot_settings['xlabel'], fontsize=plot_settings['label_fontsize'])
    ax1.set_ylabel(f'{ylabel_prefix} ' + plot_settings['ylabel_offset'], fontsize=plot_settings['label_fontsize'])
    ax1.set_title('X-Component (Toward Sun)', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax1.legend(fontsize=plot_settings['legend_fontsize'])
    ax1.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax1.grid(True, alpha=0.3, which='both' if log_scale else 'major')
    if log_scale:
        ax1.set_yscale('log')
    else:
        ax1.axhline(y=0, color='k', linewidth=0.5, alpha=0.5)
    
    # Format Y offset subplot
    ylabel_prefix_y = '|Y|' if log_scale else 'Y'
    ax2.set_xlabel(plot_settings['xlabel'], fontsize=plot_settings['label_fontsize'])
    ax2.set_ylabel(f'{ylabel_prefix_y} ' + plot_settings['ylabel_offset'], fontsize=plot_settings['label_fontsize'])
    ax2.set_title('Y-Component', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax2.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax2.grid(True, alpha=0.3, which='both' if log_scale else 'major')
    if log_scale:
        ax2.set_yscale('log')
    else:
        ax2.axhline(y=0, color='k', linewidth=0.5, alpha=0.5)
    
    # Format Z offset subplot
    ylabel_prefix_z = '|Z|' if log_scale else 'Z'
    ax3.set_xlabel(plot_settings['xlabel'], fontsize=plot_settings['label_fontsize'])
    ax3.set_ylabel(f'{ylabel_prefix_z} ' + plot_settings['ylabel_offset'], fontsize=plot_settings['label_fontsize'])
    ax3.set_title('Z-Component (Ecliptic North)', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax3.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax3.grid(True, alpha=0.3, which='both' if log_scale else 'major')
    if log_scale:
        ax3.set_yscale('log')
    else:
        ax3.axhline(y=0, color='k', linewidth=0.5, alpha=0.5)
    
    # Format magnitude subplot
    ax4.set_xlabel(plot_settings['xlabel'], fontsize=plot_settings['label_fontsize'])
    ax4.set_ylabel('Magnitude ' + plot_settings['ylabel_offset'], fontsize=plot_settings['label_fontsize'])
    ax4.set_title('Total Offset Magnitude', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax4.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax4.grid(True, alpha=0.3, which='both' if log_scale else 'major')
    if log_scale:
        ax4.set_yscale('log')
    
    # Update title to indicate scale type
    scale_text = "(Log Scale)" if log_scale else "(Linear Scale)"
    if title:
        plt.suptitle(f'{title} {scale_text}', 
                     fontsize=plot_settings['title_fontsize'], fontweight='bold', y=0.98)
    else:
        plt.suptitle(f'Satellite Offsets Relative to Base (SEM-L2 Frame) {scale_text}', 
                     fontsize=plot_settings['title_fontsize'], fontweight='bold', y=0.98)
    
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
        print(f"Saved time series plot to: {save_path}")
    
    return fig


def plot_relative_trajectories_3d(offsets_dict, save_path=None,
                                   colors=None, labels=None, plot_settings=None, log_scale=False,
                                   title=None):
    """
    Plot 3D offset trajectories with projections.
    Origin (0,0,0) represents Base satellite position.
    
    Args:
        offsets_dict: Dict of {sat_name: offset_positions (N, 3)}
        save_path: Path to save figure
        colors: Dict of {sat_name: color}
        labels: Dict of {sat_name: display_label}
        plot_settings: Dict with plot customization settings
        log_scale: If True, use logarithmic axes for 2D projections
        title: Optional custom plot title (None to hide title)
    """
    if colors is None:
        colors = SATELLITE_COLORS
    if labels is None:
        labels = SATELLITE_LABELS
    if plot_settings is None:
        plot_settings = TRAJECTORY_PLOT_SETTINGS
    
    fig = plt.figure(figsize=plot_settings['figsize'])
    
    # Create 4 subplots: 3D, XY, XZ, YZ
    ax1 = fig.add_subplot(221, projection='3d')
    ax2 = fig.add_subplot(222)  # XY plane
    ax3 = fig.add_subplot(223)  # XZ plane
    ax4 = fig.add_subplot(224)  # YZ plane
    
    # Plot each satellite's offset trajectory
    for sat_name, offsets in offsets_dict.items():
        color = colors.get(sat_name, 'black')
        label = labels.get(sat_name, sat_name)
        
        # 3D plot (always linear - log scale not well supported in 3D)
        ax1.plot(offsets[:, 0], offsets[:, 1], offsets[:, 2],
                color=color, linewidth=plot_settings['linewidth'],
                alpha=plot_settings['alpha'], zorder=2)
        
        if log_scale:
            # Use absolute values for log scale projections
            # XY projection (labeled)
            ax2.plot(np.abs(offsets[:, 0]), np.abs(offsets[:, 1]),
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], label=label, zorder=2)
            
            # XZ projection
            ax3.plot(np.abs(offsets[:, 0]), np.abs(offsets[:, 2]),
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], zorder=2)
            
            # YZ projection
            ax4.plot(np.abs(offsets[:, 1]), np.abs(offsets[:, 2]),
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], zorder=2)
        else:
            # XY projection (labeled)
            ax2.plot(offsets[:, 0], offsets[:, 1],
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], label=label, zorder=2)
            
            # XZ projection
            ax3.plot(offsets[:, 0], offsets[:, 2],
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], zorder=2)
            
            # YZ projection
            ax4.plot(offsets[:, 1], offsets[:, 2],
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], zorder=2)
    
    # Base satellite at origin (only labeled in XY plot)
    ax1.scatter([0], [0], [0], c=SATELLITE_COLORS['Base'], 
               s=plot_settings['base_marker_size_3d'],
               marker='o', edgecolors='black', linewidths=2, zorder=1000)
    
    if not log_scale:
        # Only show origin marker in linear scale (doesn't make sense at 0 in log scale)
        ax2.scatter([0], [0], c=SATELLITE_COLORS['Base'],
                   s=plot_settings['base_marker_size'], marker='o',
                   label=SATELLITE_LABELS['Base'], edgecolors='black', linewidths=2, zorder=1000)
        ax3.scatter([0], [0], c=SATELLITE_COLORS['Base'],
                   s=plot_settings['base_marker_size'], marker='o',
                   edgecolors='black', linewidths=2, zorder=1000)
        ax4.scatter([0], [0], c=SATELLITE_COLORS['Base'],
                   s=plot_settings['base_marker_size'], marker='o',
                   edgecolors='black', linewidths=2, zorder=1000)
    
    # Format 3D plot
    ax1.set_xlabel('X Offset (km)\n← Toward Sun', fontsize=plot_settings['label_fontsize_3d'])
    ax1.set_ylabel('Y Offset (km)', fontsize=plot_settings['label_fontsize_3d'])
    ax1.set_zlabel('Z Offset (km)\nEcliptic North →', fontsize=plot_settings['label_fontsize_3d'])
    ax1.set_title('3D View', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax1.tick_params(labelsize=plot_settings['tick_fontsize_3d'])
    ax1.grid(True, alpha=0.3)
    
    # Set equal aspect ratio for 3D
    all_offsets = np.vstack(list(offsets_dict.values()))
    max_range = max(
        np.ptp(all_offsets[:, 0]),
        np.ptp(all_offsets[:, 1]),
        np.ptp(all_offsets[:, 2])
    ) / 2
    mid_x = np.mean([all_offsets[:, 0].min(), all_offsets[:, 0].max()])
    mid_y = np.mean([all_offsets[:, 1].min(), all_offsets[:, 1].max()])
    mid_z = np.mean([all_offsets[:, 2].min(), all_offsets[:, 2].max()])
    ax1.set_xlim(mid_x - max_range, mid_x + max_range)
    ax1.set_ylim(mid_y - max_range, mid_y + max_range)
    ax1.set_zlim(mid_z - max_range, mid_z + max_range)
    
    # Axis label prefixes for log/linear scale
    x_prefix = '|X|' if log_scale else 'X'
    y_prefix = '|Y|' if log_scale else 'Y'
    z_prefix = '|Z|' if log_scale else 'Z'
    
    # Format XY plot
    ax2.set_xlabel(f'{x_prefix} Offset (km) ← Toward Sun', fontsize=plot_settings['label_fontsize'])
    ax2.set_ylabel(f'{y_prefix} Offset (km)', fontsize=plot_settings['label_fontsize'])
    ax2.set_title('XY Plane (Ecliptic)', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax2.legend(fontsize=plot_settings['legend_fontsize'])
    ax2.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax2.grid(True, alpha=0.3, which='both' if log_scale else 'major')
    if log_scale:
        ax2.set_xscale('log')
        ax2.set_yscale('log')
    else:
        ax2.axis('equal')
        ax2.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
        ax2.axvline(x=0, color='k', linewidth=0.5, alpha=0.3)
    
    # Format XZ plot
    ax3.set_xlabel(f'{x_prefix} Offset (km) ← Toward Sun', fontsize=plot_settings['label_fontsize'])
    ax3.set_ylabel(f'{z_prefix} Offset (km) Ecliptic North →', fontsize=plot_settings['label_fontsize'])
    ax3.set_title('XZ Plane', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax3.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax3.grid(True, alpha=0.3, which='both' if log_scale else 'major')
    if log_scale:
        ax3.set_xscale('log')
        ax3.set_yscale('log')
    else:
        ax3.axis('equal')
        ax3.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
        ax3.axvline(x=0, color='k', linewidth=0.5, alpha=0.3)
    
    # Format YZ plot
    ax4.set_xlabel(f'{y_prefix} Offset (km)', fontsize=plot_settings['label_fontsize'])
    ax4.set_ylabel(f'{z_prefix} Offset (km) Ecliptic North →', fontsize=plot_settings['label_fontsize'])
    ax4.set_title('YZ Plane', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax4.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax4.grid(True, alpha=0.3, which='both' if log_scale else 'major')
    if log_scale:
        ax4.set_xscale('log')
        ax4.set_yscale('log')
    else:
        ax4.axis('equal')
        ax4.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
        ax4.axvline(x=0, color='k', linewidth=0.5, alpha=0.3)
    
    # Update title to indicate scale type
    scale_text = "(2D Projections: Log Scale)" if log_scale else "(Linear Scale)"
    if title:
        plt.suptitle(f'{title} {scale_text}', 
                     fontsize=plot_settings['title_fontsize'], fontweight='bold', y=0.98)
    else:
        plt.suptitle(f'Relative Trajectories (SEM-L2 Frame, Base at Origin) {scale_text}', 
                     fontsize=plot_settings['title_fontsize'], fontweight='bold', y=0.98)
    
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
        print(f"Saved 3D trajectory plot to: {save_path}")
    
    return fig


def print_drift_analysis(times, offsets_dict):
    """
    Analyze and print drift rates for each satellite.
    
    Args:
        times: Time array (epoch seconds)
        offsets_dict: Dict of {sat_name: offset_positions (N, 3)}
    """
    print(f"\n{'='*70}")
    print("DRIFT RATE ANALYSIS")
    print(f"{'='*70}")
    
    times_days = (times - times[0]) / 86400
    duration = times_days[-1] - times_days[0]
    
    print(f"Analysis duration: {duration:.1f} days\n")
    print(f"{'Satellite':<12} {'X (km/day)':<12} {'Y (km/day)':<12} {'Z (km/day)':<12} {'|Δr| (km/day)':<15}")
    print("-" * 70)
    
    for sat_name, offsets in offsets_dict.items():
        # Compute linear drift rates using first and last points
        drift_x = (offsets[-1, 0] - offsets[0, 0]) / duration
        drift_y = (offsets[-1, 1] - offsets[0, 1]) / duration
        drift_z = (offsets[-1, 2] - offsets[0, 2]) / duration
        
        # Magnitude drift
        mag_initial = np.linalg.norm(offsets[0])
        mag_final = np.linalg.norm(offsets[-1])
        drift_mag = (mag_final - mag_initial) / duration
        
        print(f"{sat_name:<12} {drift_x:>11.4f}  {drift_y:>11.4f}  {drift_z:>11.4f}  {drift_mag:>14.4f}")
    
    print("="*70)


# Utility: turn a title into a safe Windows filename
def title_to_filename(title: str, ext: str = "png") -> str:
    """Convert a plot title string to a valid Windows filename."""
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
    M_total = M_SUN + M_EARTH
    f_earth = M_EARTH / M_total
    f_sun = M_SUN / M_total
    
    earth_pos_bary = sun_pos_geocentric * f_sun
    earth_vel_bary = sun_vel_geocentric * f_sun
    sun_pos_bary = -sun_pos_geocentric * f_earth
    sun_vel_bary = -sun_vel_geocentric * f_earth
    
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
        pos_bary = pos_icrf + earth_pos_bary
        vel_bary = vel_icrf + earth_vel_bary
        
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
    
    time_series_linear_path = plots_dir / time_series_linear_filename
    time_series_log_path = plots_dir / time_series_log_filename
    trajectory_3d_linear_path = plots_dir / trajectory_3d_linear_filename
    trajectory_3d_log_path = plots_dir / trajectory_3d_log_filename
    
    # Determine custom title (None if PLOT_SHOW_TITLE is False)
    custom_title = PLOT_TITLE if PLOT_SHOW_TITLE else None
    
    print("Generating linear scale time series plot...")
    plot_offsets_vs_time(sat_times, offsets_dict, save_path=time_series_linear_path, 
                         log_scale=False, title=custom_title)
    
    print("Generating log scale time series plot...")
    plot_offsets_vs_time(sat_times, offsets_dict, save_path=time_series_log_path, 
                         log_scale=True, title=custom_title)
    
    print("Generating linear scale 3D trajectory plot...")
    plot_relative_trajectories_3d(offsets_dict, save_path=trajectory_3d_linear_path, 
                                   log_scale=False, title=custom_title)
    
    print("Generating log scale 3D trajectory plot...")
    plot_relative_trajectories_3d(offsets_dict, save_path=trajectory_3d_log_path, 
                                   log_scale=True, title=custom_title)
    
    print("\n=== Complete! ===")
    print(f"Generated plots in: {plots_dir}")


if __name__ == "__main__":
    main()