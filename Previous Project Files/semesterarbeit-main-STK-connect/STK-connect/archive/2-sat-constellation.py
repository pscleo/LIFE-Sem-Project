"""
Create satellite constellation with offset positions in SEM-L2 frame.

This script:
1. Connects to STK and retrieves an existing L2 Halo orbit satellite
2. Creates new satellites with position offsets in the SEM-L2 frame
3. Propagates trajectories using Cislunar propagator
4. Computes relative distances between satellites over time
5. Plots trajectories and drift analysis

The satellites are organized in a "2-Sat-constellation" folder in STK.
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pathlib import Path

# Add Scripts folder to path to find pywin32 modules
scripts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'SA-venv', 'Scripts'))
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

import win32com.client
from mpl_toolkits.mplot3d import Axes3D

# ============================================================================
# USER SETTINGS - Modify these to customize the analysis
# ============================================================================

# Reference satellite (must exist in STK scenario)
REFERENCE_SATELLITE = "JWST"  # The L2 Halo orbit satellite

# Satellite configurations: list of (name, offset_x, offset_y, offset_z) in meters
# Offsets are in SEM-L2 frame
SATELLITE_CONFIGS = [
    ("Offset-X-100m", 100, 0, 0),  # 100m in +X direction
    # Add more satellites here later:
    # ("Offset-Y-100m", 0, 100, 0),
    # ("Offset-Z-100m", 0, 0, 100),
]

# Time range settings
START_DATE_YEAR = 2022 #2022
START_DATE_MONTH = 10 #10
START_DATE_DAY = 7 #7
DURATION_DAYS = 360  # 12 months

# STK connection settings
TIMESTEP_SECONDS = 3600  # Data sampling interval (1 hour)

# Plot settings
PLOT_SETTINGS = {
    'figsize': (16, 10),
    'dpi': 300,
    'linewidth': 1.5,
    'alpha': 0.7,
    'title_fontsize': 16,
    'label_fontsize': 12,
    'legend_fontsize': 10,
    'tick_fontsize': 10,
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


def get_satellite_initial_state(root, scenario, sat_name):
    """
    Get initial state vector (position and velocity) of a satellite at scenario start time.
    Returns position (km) and velocity (km/s) in ICRF frame.
    """
    print(f"Getting initial state for {sat_name}...")
    
    sat = root.GetObjectFromPath(f"Satellite/{sat_name}")
    
    # Query for entire trajectory and take first point
    # This is more robust than querying a single point
    pos_dp = sat.DataProviders.Item("Cartesian Position").Group.Item("ICRF")
    pos_result = pos_dp.Exec(scenario.StartTime, scenario.StopTime, TIMESTEP_SECONDS)
    
    # Get data arrays
    times = np.array(pos_result.DataSets.GetDataSetByName("Time").GetValues())
    x = np.array(pos_result.DataSets.GetDataSetByName("x").GetValues())
    y = np.array(pos_result.DataSets.GetDataSetByName("y").GetValues())
    z = np.array(pos_result.DataSets.GetDataSetByName("z").GetValues())
    
    # Take first available point
    position_icrf = np.array([x[0], y[0], z[0]])
    
    # Get velocity - query entire trajectory and take first point
    vel_dp = sat.DataProviders.Item("Cartesian Velocity").Group.Item("ICRF")
    vel_result = vel_dp.Exec(scenario.StartTime, scenario.StopTime, TIMESTEP_SECONDS)
    
    vx = np.array(vel_result.DataSets.GetDataSetByName("x").GetValues())
    vy = np.array(vel_result.DataSets.GetDataSetByName("y").GetValues())
    vz = np.array(vel_result.DataSets.GetDataSetByName("z").GetValues())
    
    velocity_icrf = np.array([vx[0], vy[0], vz[0]])
    
    print(f"  Position: {position_icrf} km")
    print(f"  Velocity: {velocity_icrf} km/s")
    
    return position_icrf, velocity_icrf


def get_body_state_at_epoch(root, scenario, body_name):
    """
    Get state vectors for a celestial body at scenario start time.
    Returns geocentric position (km) and velocity (km/s) in ICRF frame.
    """
    print(f"Getting state for {body_name} at epoch...")
    
    try:
        planet = root.GetObjectFromPath(f"Planet/{body_name}")
    except:
        planet = root.GetObjectFromPath(f"Star/{body_name}")
    
    # Query for entire trajectory and take first point
    pos_dp = planet.DataProviders.Item("Cartesian Position").Group.Item("ICRF")
    pos_result = pos_dp.Exec(scenario.StartTime, scenario.StopTime, TIMESTEP_SECONDS)
    
    times = np.array(pos_result.DataSets.GetDataSetByName("Time").GetValues())
    x = np.array(pos_result.DataSets.GetDataSetByName("x").GetValues())
    y = np.array(pos_result.DataSets.GetDataSetByName("y").GetValues())
    z = np.array(pos_result.DataSets.GetDataSetByName("z").GetValues())
    position = np.array([x[0], y[0], z[0]])
    
    # Get velocity
    vel_dp = planet.DataProviders.Item("Cartesian Velocity").Group.Item("ICRF")
    vel_result = vel_dp.Exec(scenario.StartTime, scenario.StopTime, TIMESTEP_SECONDS)
    
    vx = np.array(vel_result.DataSets.GetDataSetByName("x").GetValues())
    vy = np.array(vel_result.DataSets.GetDataSetByName("y").GetValues())
    vz = np.array(vel_result.DataSets.GetDataSetByName("z").GetValues())
    velocity = np.array([vx[0], vy[0], vz[0]])
    
    return position, velocity


def compute_l2_position_approximate(r_sun, r_earth):
    """Compute approximate L2 position using simplified formula"""
    r_se = r_earth - r_sun
    r_se_norm = np.linalg.norm(r_se)
    r_se_hat = r_se / r_se_norm
    
    # L2 distance from Earth (simplified)
    mu = M_EARTH / (M_SUN + M_EARTH)
    r_l2 = r_se_norm * (mu / 3)**(1/3)
    
    return r_earth + r_l2 * r_se_hat


def build_sem_l2_axes(r_sun, r_earth, v_earth, fixed_ecliptic_normal=None):
    """
    Build SEM-L2 rotating frame axes at a given instant.
    
    Returns rotation matrix R where:
    - x_sem_l2 points from Earth to Sun
    - z_sem_l2 perpendicular to Earth's orbital plane
    - y_sem_l2 completes right-handed system
    """
    # X-axis: Earth to Sun direction
    r_se = r_sun - r_earth
    x_axis = r_se / np.linalg.norm(r_se)
    
    # Z-axis: perpendicular to orbital plane
    if fixed_ecliptic_normal is not None:
        z_axis = fixed_ecliptic_normal
    else:
        h = np.cross(r_earth, v_earth)
        z_axis = h / np.linalg.norm(h)
    
    # Y-axis: complete right-handed system
    y_axis = np.cross(z_axis, x_axis)
    y_axis = y_axis / np.linalg.norm(y_axis)
    
    # Re-orthogonalize Z to ensure perfect orthogonality
    z_axis = np.cross(x_axis, y_axis)
    z_axis = z_axis / np.linalg.norm(z_axis)
    
    # Build rotation matrix (columns are the axes)
    R = np.column_stack([x_axis, y_axis, z_axis])
    
    return R


def offset_position_in_sem_l2(position_icrf, offset_sem_l2, R_sem_l2):
    """
    Apply position offset in SEM-L2 frame.
    
    Args:
        position_icrf: Original position in ICRF frame (km)
        offset_sem_l2: Offset in SEM-L2 frame [dx, dy, dz] (km)
        R_sem_l2: Rotation matrix from ICRF to SEM-L2
    
    Returns:
        New position in ICRF frame (km)
    """
    # Convert offset from SEM-L2 to ICRF
    offset_icrf = R_sem_l2 @ offset_sem_l2
    
    # Apply offset
    new_position = position_icrf + offset_icrf
    
    return new_position


def create_or_update_satellite(root, scenario, sat_name, position_icrf, velocity_icrf):
    """
    Create a new satellite or update existing one with given state vector.
    Preferred: Use Astrogator (Initial State + Propagate), assign ICRF Cartesian state at scenario start, then run MCS.
    Fallback: Use J4 propagator with ICRF Cartesian state if Astrogator is unavailable.
    """
    full_path = f"Satellite/{sat_name}"

    # Remove existing (do not use the object after Unload)
    try:
        sat_existing = root.GetObjectFromPath(full_path)
        print(f"  Satellite {sat_name} already exists, removing and recreating...")
        sat_existing.Unload()
        scenario.Children.Remove(sat_existing.InstanceName)
    except:
        pass

    # Constants with numeric fallbacks
    try:
        const = win32com.client.constants
        eSatellite = getattr(const, 'eSatellite', 18)
        ePropAstrogator = getattr(const, 'ePropagatorAstrogator', 12)
        ePropJ4 = getattr(const, 'ePropagatorJ4Perturbation', 2)
    except Exception:
        const = None
        eSatellite = 18
        ePropAstrogator = 12
        ePropJ4 = 2

    print(f"  Creating new satellite {sat_name}...")
    sat = scenario.Children.New(eSatellite, sat_name)
    print(f"  ✓ Satellite object created")

    # Ensure units are km (your inputs are km/km/s)
    root.ExecuteCommand('SetUnits / km')

    # Try Astrogator first
    try:
        print("  Switching propagator to Astrogator...")
        sat.SetPropagatorType(ePropAstrogator)
        driver = sat.Propagator  # IAgVADriverMCS

        print("  Building Astrogator MCS: Initial State + Propagate...")
        mcs = driver.MainSequence
        mcs.RemoveAll()

        # Insert Initial State segment
        init = mcs.Insert(0, "Initial State", "Initial")
        # Set epoch
        try:
            init.OrbitEpoch = scenario.StartTime
        except Exception:
            pass

        # Assign Cartesian state in ICRF to Initial State representation
        try:
            rep = init.OrbitState.Representation
            # Many installs support AssignCartesian with an ICRF enum; fall back to 11 (ICRF) if constant missing
            eCoordICRF = getattr(const, 'eCoordinateSystemICRF', 11) if const else 11
            rep.AssignCartesian(
                eCoordICRF,
                float(position_icrf[0]), float(position_icrf[1]), float(position_icrf[2]),
                float(velocity_icrf[0]), float(velocity_icrf[1]), float(velocity_icrf[2])
            )
        except Exception as e:
            print(f"    Note: AssignCartesian on Astrogator Initial failed ({e}), attempting alternative...")
            try:
                # Alternative: convert to Cartesian then set components
                elem = init.OrbitState.Representation.ConvertTo(1)  # 1 ~ Cartesian
                elem.X = float(position_icrf[0]); elem.Y = float(position_icrf[1]); elem.Z = float(position_icrf[2])
                elem.XDot = float(velocity_icrf[0]); elem.YDot = float(velocity_icrf[1]); elem.ZDot = float(velocity_icrf[2])
                init.OrbitState.Representation.Assign(elem)
            except Exception as e2:
                print(f"    Alt assign failed: {e2}")
                raise

        # Insert Propagate segment and set stop condition to scenario duration
        prop = mcs.Insert(1, "Propagate", "Propagate")
        try:
            # Use Duration stop condition (seconds)
            stopConds = prop.StoppingConditions
            # Clear existing and set Duration
            for i in range(stopConds.Count-1, -1, -1):
                stopConds.Remove(i)
            dur = stopConds.Add("Duration")
            # Estimate duration from scenario (fallback to DURATION_DAYS)
            try:
                # Convert scenario times to EpSec
                start_ep = float(root.ConversionUtility.ConvertDate('UTCG','EpSec', str(scenario.StartTime)))
                stop_ep = float(root.ConversionUtility.ConvertDate('UTCG','EpSec', str(scenario.StopTime)))
                duration_sec = max(0.0, stop_ep - start_ep)
            except Exception:
                duration_sec = float(DURATION_DAYS) * 86400.0
            dur.Properties.Trip = duration_sec
        except Exception:
            pass

        # Run MCS
        print("  Running Astrogator MCS...")
        driver.RunMCS()
        print("  ✓ Astrogator MCS completed")
        return sat

    except Exception as astro_err:
        print(f"  ✗ Astrogator setup failed: {astro_err}")
        print("  → Falling back to J4 propagator with ICRF Cartesian state...")

    # Fallback: J4 perturbation with ICRF state, then propagate
    try:
        sat.SetPropagatorType(ePropJ4)
        propagator = sat.Propagator
        # Assign ICRF Cartesian (use 11 as ICRF fallback per STK examples)
        eCoordICRF = getattr(const, 'eCoordinateSystemICRF', 11) if const else 11
        propagator.InitialState.Representation.AssignCartesian(
            eCoordICRF,
            float(position_icrf[0]), float(position_icrf[1]), float(position_icrf[2]),
            float(velocity_icrf[0]), float(velocity_icrf[1]), float(velocity_icrf[2])
        )
        # Propagate
        propagator.Propagate()
        print("  ✓ Fallback J4 propagation completed")
        return sat
    except Exception as e:
        print(f"  ✗ Fallback J4 also failed: {e}")
        raise


def get_satellite_trajectory(root, scenario, sat_name, timestep_seconds):
    """
    Get full trajectory of a satellite.
    
    Returns:
        times, positions, velocities (all in ICRF frame)
    """
    full_path = f"Satellite/{sat_name}"
    
    print(f"Getting trajectory for {full_path}...")
    
    sat = root.GetObjectFromPath(full_path)
    
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
    
    print(f"  Retrieved {len(times)} data points")
    return times, positions, velocities


def get_body_trajectory(root, scenario, body_name, timestep_seconds):
    """Get trajectory for celestial body (Sun, Earth)"""
    print(f"Getting trajectory for {body_name}...")
    
    try:
        planet = root.GetObjectFromPath(f"Planet/{body_name}")
    except:
        planet = root.GetObjectFromPath(f"Star/{body_name}")
    
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
    
    print(f"  Retrieved {len(times)} data points")
    return times, positions, velocities


def transform_to_sem_l2_frame(positions_icrf, sun_positions, earth_positions, earth_velocities):
    """
    Transform positions from ICRF to SEM-L2 rotating frame.
    """
    N = len(positions_icrf)
    positions_sem_l2 = np.zeros_like(positions_icrf)

    # Use first epoch to define fixed ecliptic normal using Sun-based Earth orbit vectors
    earth_orbit_pos0 = -sun_positions[0]    # Earth wrt Sun (from geocentric Sun)
    # Approximate Earth orbital velocity from finite difference on Sun position
    if N > 1:
        dt = 3600.0  # 1 hour
        earth_orbit_vel0 = -(sun_positions[1] - sun_positions[0]) / dt
    else:
        earth_orbit_vel0 = np.array([0.0, 0.0, 1.0])  # fallback

    h0 = np.cross(earth_orbit_pos0, earth_orbit_vel0)
    if np.linalg.norm(h0) < 1e-12:
        raise ValueError("Cannot compute ecliptic normal (degenerate Sun/Earth orbit vectors)")
    ecliptic_normal = h0 / np.linalg.norm(h0)

    for i in range(N):
        # Build SEM-L2 axes using Sun position; earth_vel is not geocentric here, so reuse normal
        R = build_sem_l2_axes(sun_positions[i], earth_positions[i], earth_orbit_vel0, ecliptic_normal)
        # L2 position (approx)
        r_l2 = compute_l2_position_approximate(sun_positions[i], earth_positions[i])

        r_rel_icrf = positions_icrf[i] - r_l2
        positions_sem_l2[i] = R.T @ r_rel_icrf

    return positions_sem_l2


def compute_relative_distances(ref_positions, other_positions_dict):
    """
    Compute distances between reference satellite and others.
    
    Args:
        ref_positions: Nx3 array of reference satellite positions
        other_positions_dict: Dict of {sat_name: Nx3 positions}
    
    Returns:
        Dict of {sat_name: distances in km}
    """
    distances = {}
    
    for sat_name, positions in other_positions_dict.items():
        diff = positions - ref_positions
        dist = np.linalg.norm(diff, axis=1)
        distances[sat_name] = dist
    
    return distances


def plot_results(times, ref_positions_sem_l2, other_positions_sem_l2, distances, save_dir):
    """
    Create comprehensive plots:
    1. 3D trajectories in SEM-L2 frame
    2. Distance vs time
    3. X, Y, Z components vs time
    """
    # Convert times to days since start
    times_days = (times - times[0]) / 86400.0  # Convert seconds to days
    
    fig = plt.figure(figsize=PLOT_SETTINGS['figsize'], dpi=PLOT_SETTINGS['dpi'])
    
    # 1. 3D trajectory plot
    ax1 = fig.add_subplot(2, 2, 1, projection='3d')
    
    # Plot reference satellite
    ax1.plot(ref_positions_sem_l2[:, 0], ref_positions_sem_l2[:, 1], 
             ref_positions_sem_l2[:, 2], 'k-', linewidth=2, alpha=0.8, 
             label='Reference (JWST)')
    
    # Plot other satellites
    colors = plt.get_cmap('tab10')(np.linspace(0, 1, len(other_positions_sem_l2)))
    for (sat_name, positions), color in zip(other_positions_sem_l2.items(), colors):
        ax1.plot(positions[:, 0], positions[:, 1], positions[:, 2], 
                linewidth=PLOT_SETTINGS['linewidth'], alpha=PLOT_SETTINGS['alpha'],
                label=sat_name, color=color)
    
    # L2 point at origin
    ax1.scatter(0, 0, 0, c='red', s=100, marker='x', label='L2')
    
    ax1.set_xlabel('X (km)', fontsize=PLOT_SETTINGS['label_fontsize'])
    ax1.set_ylabel('Y (km)', fontsize=PLOT_SETTINGS['label_fontsize'])
    ax1.set_zlabel('Z (km)', fontsize=PLOT_SETTINGS['label_fontsize'])
    ax1.set_title('Trajectories in SEM-L2 Frame', fontsize=PLOT_SETTINGS['title_fontsize'])
    ax1.legend(fontsize=PLOT_SETTINGS['legend_fontsize'])
    ax1.grid(True, alpha=0.3)
    
    # 2. Distance vs time
    ax2 = fig.add_subplot(2, 2, 2)
    
    for (sat_name, dist), color in zip(distances.items(), colors):
        ax2.plot(times_days, dist, linewidth=PLOT_SETTINGS['linewidth'], 
                label=sat_name, color=color)
    
    ax2.set_xlabel('Time (days)', fontsize=PLOT_SETTINGS['label_fontsize'])
    ax2.set_ylabel('Distance from Reference (km)', fontsize=PLOT_SETTINGS['label_fontsize'])
    ax2.set_title('Relative Distance Over Time', fontsize=PLOT_SETTINGS['title_fontsize'])
    ax2.legend(fontsize=PLOT_SETTINGS['legend_fontsize'])
    ax2.grid(True, alpha=0.3)
    
    # 3. X component vs time
    ax3 = fig.add_subplot(2, 2, 3)
    
    for (sat_name, positions), color in zip(other_positions_sem_l2.items(), colors):
        dx = positions[:, 0] - ref_positions_sem_l2[:, 0]
        ax3.plot(times_days, dx, linewidth=PLOT_SETTINGS['linewidth'], 
                label=sat_name, color=color)
    
    ax3.set_xlabel('Time (days)', fontsize=PLOT_SETTINGS['label_fontsize'])
    ax3.set_ylabel('ΔX (km)', fontsize=PLOT_SETTINGS['label_fontsize'])
    ax3.set_title('X-Direction Separation', fontsize=PLOT_SETTINGS['title_fontsize'])
    ax3.legend(fontsize=PLOT_SETTINGS['legend_fontsize'])
    ax3.grid(True, alpha=0.3)
    ax3.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    
    # 4. Y and Z components
    ax4 = fig.add_subplot(2, 2, 4)
    
    for (sat_name, positions), color in zip(other_positions_sem_l2.items(), colors):
        dy = positions[:, 1] - ref_positions_sem_l2[:, 1]
        dz = positions[:, 2] - ref_positions_sem_l2[:, 2]
        ax4.plot(times_days, dy, linewidth=PLOT_SETTINGS['linewidth'], 
                label=f'{sat_name} (Y)', color=color, linestyle='-')
        ax4.plot(times_days, dz, linewidth=PLOT_SETTINGS['linewidth'], 
                label=f'{sat_name} (Z)', color=color, linestyle='--', alpha=0.7)
    
    ax4.set_xlabel('Time (days)', fontsize=PLOT_SETTINGS['label_fontsize'])
    ax4.set_ylabel('ΔY, ΔZ (km)', fontsize=PLOT_SETTINGS['label_fontsize'])
    ax4.set_title('Y & Z Direction Separation', fontsize=PLOT_SETTINGS['title_fontsize'])
    ax4.legend(fontsize=PLOT_SETTINGS['legend_fontsize'] - 1)
    ax4.grid(True, alpha=0.3)
    ax4.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot
    save_path = Path(save_dir) / "constellation_analysis.png"
    plt.savefig(save_path, dpi=PLOT_SETTINGS['dpi'], bbox_inches='tight')
    print(f"\nPlot saved to: {save_path}")
    
    plt.show()


def main():
    """Main execution function"""
    print("="*80)
    print("2-Satellite Constellation Analysis")
    print("="*80)
    
    # Connect to STK
    root, scenario = connect_to_stk()
    
    # Get reference satellite initial state
    print(f"\n--- Getting reference satellite: {REFERENCE_SATELLITE} ---")
    ref_pos_icrf, ref_vel_icrf = get_satellite_initial_state(
        root, scenario, REFERENCE_SATELLITE)
    
    # Get Sun and Earth states at epoch (needed for SEM-L2 transformation)
    print("\n--- Getting celestial body states at epoch ---")
    sun_pos_epoch, sun_vel_epoch = get_body_state_at_epoch(root, scenario, "Sun")
    earth_pos_epoch, earth_vel_epoch = get_body_state_at_epoch(root, scenario, "Earth")
    
    print(f"  Sun position: {sun_pos_epoch} km")
    print(f"  Sun velocity: {sun_vel_epoch} km/s")
    print(f"  Earth position: {earth_pos_epoch} km")
    print(f"  Earth velocity: {earth_vel_epoch} km/s")
    
    # Build SEM-L2 frame at epoch
    # IMPORTANT: Use Sun's position (negative) and velocity (negative) as Earth's orbital motion
    # since ICRF is geocentric (Earth at origin)
    print("\n--- Computing SEM-L2 frame at epoch ---")
    
    # In ICRF (geocentric), Sun position is -Earth position in heliocentric frame
    # So we use -sun_pos for Earth's position relative to Sun
    earth_orbit_pos = -sun_pos_epoch  # Earth's position relative to Sun
    earth_orbit_vel = -sun_vel_epoch  # Earth's velocity relative to Sun
    
    h0 = np.cross(earth_orbit_pos, earth_orbit_vel)
    
    if np.linalg.norm(h0) < 1e-10:
        print(f"  ERROR: Angular momentum near zero!")
        print(f"  earth_orbit_pos: {earth_orbit_pos}")
        print(f"  earth_orbit_vel: {earth_orbit_vel}")
        raise ValueError("Cannot compute ecliptic normal - vectors are parallel")
    
    ecliptic_normal = h0 / np.linalg.norm(h0)
    
    # Build SEM-L2 frame (using Sun position in geocentric frame)
    R_sem_l2 = build_sem_l2_axes(sun_pos_epoch, earth_pos_epoch, 
                                  earth_orbit_vel, ecliptic_normal)
    print(f"SEM-L2 rotation matrix computed")
    print(f"  Ecliptic normal: {ecliptic_normal}")
    
    # Create constellation satellites
    print(f"\n--- Creating constellation satellites ---")
    
    for sat_name, offset_x, offset_y, offset_z in SATELLITE_CONFIGS:
        print(f"\nProcessing {sat_name}:")
        print(f"  Offset in SEM-L2: [{offset_x}, {offset_y}, {offset_z}] meters")
        
        # Convert offset from meters to km
        offset_sem_l2 = np.array([offset_x, offset_y, offset_z]) / 1000.0
        
        # Apply offset in SEM-L2 frame
        new_pos_icrf = offset_position_in_sem_l2(ref_pos_icrf, offset_sem_l2, R_sem_l2)
        
        # Check for NaN
        if np.any(np.isnan(new_pos_icrf)):
            print(f"  ERROR: Position contains NaN values!")
            print(f"  ref_pos_icrf: {ref_pos_icrf}")
            print(f"  offset_sem_l2: {offset_sem_l2}")
            print(f"  R_sem_l2:\n{R_sem_l2}")
            raise ValueError("Cannot create satellite with NaN position")
        
        # Keep velocity same as reference
        new_vel_icrf = ref_vel_icrf.copy()
        
        print(f"  New position (ICRF): {new_pos_icrf} km")
        print(f"  New velocity (ICRF): {new_vel_icrf} km/s")
        
        # Create or update satellite
        create_or_update_satellite(root, scenario, sat_name, 
                                   new_pos_icrf, new_vel_icrf)
    
    # Get trajectories
    print("\n--- Retrieving trajectories ---")
    
    # Reference satellite
    ref_times, ref_positions, ref_velocities = get_satellite_trajectory(
        root, scenario, REFERENCE_SATELLITE, TIMESTEP_SECONDS)
    
    # Other satellites
    other_trajectories = {}
    for sat_name, _, _, _ in SATELLITE_CONFIGS:
        times, positions, velocities = get_satellite_trajectory(
            root, scenario, sat_name, TIMESTEP_SECONDS)
        other_trajectories[sat_name] = {
            'times': times,
            'positions': positions,
            'velocities': velocities
        }
    
    # Get Sun and Earth trajectories
    sun_times, sun_positions, sun_velocities = get_body_trajectory(
        root, scenario, "Sun", TIMESTEP_SECONDS)
    earth_times, earth_positions, earth_velocities = get_body_trajectory(
        root, scenario, "Earth", TIMESTEP_SECONDS)
    
    # Transform to SEM-L2 frame
    print("\n--- Transforming to SEM-L2 frame ---")
    
    ref_positions_sem_l2 = transform_to_sem_l2_frame(
        ref_positions, sun_positions, earth_positions, earth_velocities)
    
    other_positions_sem_l2 = {}
    for sat_name, traj in other_trajectories.items():
        positions_sem_l2 = transform_to_sem_l2_frame(
            traj['positions'], sun_positions, earth_positions, earth_velocities)
        other_positions_sem_l2[sat_name] = positions_sem_l2
    
    # Compute relative distances
    print("\n--- Computing relative distances ---")
    distances = compute_relative_distances(ref_positions_sem_l2, other_positions_sem_l2)
    
    for sat_name, dist in distances.items():
        print(f"{sat_name}:")
        print(f"  Initial distance: {dist[0]:.6f} km = {dist[0]*1000:.2f} m")
        print(f"  Final distance: {dist[-1]:.6f} km = {dist[-1]*1000:.2f} m")
        print(f"  Max distance: {np.max(dist):.6f} km = {np.max(dist)*1000:.2f} m")
        print(f"  Drift: {(dist[-1] - dist[0])*1000:.2f} m")
    
    # Create plots
    print("\n--- Creating plots ---")
    save_dir = Path(__file__).parent / "plots" / "constellation"
    save_dir.mkdir(parents=True, exist_ok=True)
    
    plot_results(ref_times, ref_positions_sem_l2, other_positions_sem_l2, 
                distances, save_dir)
    
    print("\n" + "="*80)
    print("Analysis complete!")
    print("="*80)


if __name__ == "__main__":
    main()
