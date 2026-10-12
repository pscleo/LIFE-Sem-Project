"""
Coordinate Transformation to SEM-L2 Frame - Version 2
Following the detailed plan in Coordinate-Transformation-plan.md

SEM-L2 Frame Definition:
- Origin: Sun-Earth L2 point (instantaneous)
- +X axis: Anti-Sun (points away from the Sun)
- +Z axis: Towards ecliptic north
- +Y completes a right-handed system
"""

import win32com.client
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path

# Physical constants
G = 6.67430e-11  # m^3 kg^-1 s^-2
M_SUN = 1.989e30  # kg
M_EARTH = 5.972e24  # kg
AU_KM = 149597870.7  # km
AU_M = AU_KM * 1000  # m


def connect_to_stk(version=13):
    """Connect to running STK instance."""
    print(f"Connecting to STK {version}...")
    uiApp = win32com.client.Dispatch(f"STK{version}.Application")
    root = uiApp.Personality2
    scenario = root.CurrentScenario
    print(f"Connected to scenario: {scenario.InstanceName}")
    
    # Set date format to epoch seconds for easier data handling
    root.UnitPreferences.Item('DateFormat').SetCurrentUnit('EpSec')
    print("Set time format to EpSec")
    
    return root, scenario


def get_body_state_vectors(root, scenario, body_name, timestep_seconds):
    """
    Get state vectors (position and velocity) for a celestial body in ICRF.
    
    Args:
        root: STK root object
        scenario: STK scenario object
        body_name: Name of the body (e.g., 'Sun', 'Earth')
        timestep_seconds: Time step in seconds
    
    Returns:
        times: Array of times (seconds from scenario start)
        positions: Array of positions (km), shape (n, 3)
        velocities: Array of velocities (km/s), shape (n, 3)
    """
    print(f"Getting state vectors for {body_name}...")
    
    # For celestial bodies, we need to use the planet or central body object
    # Try different paths
    obj = None
    tried_paths = []
    
    # Try as a planet first (works for Sun, Moon, etc.)
    try:
        obj = root.GetObjectFromPath(f"Planet/{body_name}")
        print(f"  Found {body_name} as Planet")
    except:
        tried_paths.append(f"Planet/{body_name}")
        
    # Try as a star
    if obj is None:
        try:
            obj = root.GetObjectFromPath(f"Star/{body_name}")
            print(f"  Found {body_name} as Star")
        except:
            tried_paths.append(f"Star/{body_name}")
    
    # Try as central body
    if obj is None:
        try:
            obj = root.GetObjectFromPath(f"CentralBody/{body_name}")
            print(f"  Found {body_name} as CentralBody")
        except:
            tried_paths.append(f"CentralBody/{body_name}")
    
    if obj is None:
        raise ValueError(f"Could not find {body_name} in STK. Tried: {tried_paths}")
    
    # Get position data provider
    pos_dp = obj.DataProviders.Item("Cartesian Position").Group.Item("ICRF")
    pos_result = pos_dp.Exec(scenario.StartTime, scenario.StopTime, timestep_seconds)
    
    times = np.array(pos_result.DataSets.GetDataSetByName("Time").GetValues())
    x = np.array(pos_result.DataSets.GetDataSetByName("x").GetValues())
    y = np.array(pos_result.DataSets.GetDataSetByName("y").GetValues())
    z = np.array(pos_result.DataSets.GetDataSetByName("z").GetValues())
    positions = np.vstack((x, y, z)).T
    
    # Get velocity data provider
    vel_dp = obj.DataProviders.Item("Cartesian Velocity").Group.Item("ICRF")
    vel_result = vel_dp.Exec(scenario.StartTime, scenario.StopTime, timestep_seconds)
    
    vx = np.array(vel_result.DataSets.GetDataSetByName("x").GetValues())
    vy = np.array(vel_result.DataSets.GetDataSetByName("y").GetValues())
    vz = np.array(vel_result.DataSets.GetDataSetByName("z").GetValues())
    velocities = np.vstack((vx, vy, vz)).T
    
    print(f"  Retrieved {len(times)} data points for {body_name}")
    return times, positions, velocities


def get_satellite_state_vectors(root, scenario, sat_name, timestep_seconds):
    """
    Get satellite state vectors in ICRF.
    
    Returns:
        times, positions (km), velocities (km/s)
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
    """
    Compute approximate L2 position using the cubic approximation.
    
    Args:
        r_sun: Sun position in ICRF (km)
        r_earth: Earth position in ICRF (km)
    
    Returns:
        r_l2: L2 position in ICRF (km)
    """
    # Earth-Sun vector
    r_es = r_earth - r_sun
    a = np.linalg.norm(r_es)  # Sun-Earth distance
    
    # Mass parameter
    mu = M_EARTH / (M_SUN + M_EARTH)
    
    # Approximate Earth->L2 distance
    d = a * (mu / 3) ** (1/3)
    
    # L2 position: from Earth along anti-Sun direction
    r_l2 = r_earth + d * (r_es / a)
    
    return r_l2


def compute_l2_position_refined(r_sun, r_earth, max_iter=10, tol=1e-6):
    """
    Compute refined L2 position using Newton-Raphson iteration.
    
    This solves the collinear equilibrium equation for L2.
    
    Args:
        r_sun: Sun position in ICRF (km)
        r_earth: Earth position in ICRF (km)
        max_iter: Maximum iterations
        tol: Convergence tolerance (km)
    
    Returns:
        r_l2: L2 position in ICRF (km)
    """
    # Start with approximate solution
    r_es = r_earth - r_sun
    a_km = np.linalg.norm(r_es)
    a = a_km * 1000  # Convert to meters for calculation
    
    mu = M_EARTH / (M_SUN + M_EARTH)
    
    # Initial guess for x (distance from Sun) in meters
    d_approx = a * (mu / 3) ** (1/3)
    x = a + d_approx
    
    # Newton-Raphson iteration
    omega_sq = G * (M_SUN + M_EARTH) / (a ** 3)
    
    for i in range(max_iter):
        # Function: F(x) = GM_sun/x^2 - GM_earth/(x-a)^2 - omega^2 * x
        f = (G * M_SUN / x**2) - (G * M_EARTH / (x - a)**2) - omega_sq * x
        
        # Derivative: F'(x)
        f_prime = (-2 * G * M_SUN / x**3) + (2 * G * M_EARTH / (x - a)**3) - omega_sq
        
        # Newton step
        x_new = x - f / f_prime
        
        # Check convergence
        if abs(x_new - x) * 1000 < tol:  # Convert to km for tolerance check
            x = x_new
            break
        
        x = x_new
    
    # Convert back to vector form
    x_km = x / 1000  # Convert to km
    r_l2 = r_sun + (x_km / a_km) * r_es
    
    return r_l2


def build_sem_l2_axes(r_sun, r_earth, v_earth, fixed_ecliptic_normal=None):
    """
    Build SEM-L2 orthonormal axes.
    
    Args:
        r_sun: Sun position in ICRF (km)
        r_earth: Earth position in ICRF (km)
        v_earth: Earth velocity in ICRF (km/s)
        fixed_ecliptic_normal: Optional fixed ecliptic normal vector (for consistent rotating frame)
    
    Returns:
        x_hat, y_hat, z_hat: Unit vectors defining SEM-L2 frame
        R: Rotation matrix (3x3) from ICRF to SEM-L2
    """
    # 1. Anti-Sun direction (from Sun to L2)
    r_l2 = compute_l2_position_approximate(r_sun, r_earth)
    u_x = r_l2 - r_sun
    x_hat = u_x / np.linalg.norm(u_x)
    
    # 2. Ecliptic north - use FIXED normal if provided (for proper rotating frame)
    if fixed_ecliptic_normal is not None:
        n_ecl_hat = fixed_ecliptic_normal
    elif np.linalg.norm(r_earth) < 1.0:  # Earth at origin
        # Use ICRF Z-axis as approximate ecliptic north
        n_ecl_hat = np.array([0, 0, 1])
    else:
        # Use Earth's orbital angular momentum
        n_ecl = np.cross(r_earth, v_earth)
        norm_n_ecl = np.linalg.norm(n_ecl)
        if norm_n_ecl < 1e-6:  # Handle near-zero case
            # Fallback to ICRF Z
            n_ecl_hat = np.array([0, 0, 1])
        else:
            n_ecl_hat = n_ecl / norm_n_ecl
    
    # 3. Make z_hat orthogonal to x_hat
    z_perp = n_ecl_hat - np.dot(n_ecl_hat, x_hat) * x_hat
    norm_z_perp = np.linalg.norm(z_perp)
    if norm_z_perp < 1e-10:  # x_hat and n_ecl are parallel
        # Use a perpendicular vector
        if abs(x_hat[2]) < 0.9:
            z_perp = np.array([0, 0, 1]) - np.dot([0, 0, 1], x_hat) * x_hat
        else:
            z_perp = np.array([0, 1, 0]) - np.dot([0, 1, 0], x_hat) * x_hat
        norm_z_perp = np.linalg.norm(z_perp)
    z_hat = z_perp / norm_z_perp
    
    # 4. Complete right-handed system
    y_hat = np.cross(z_hat, x_hat)
    
    # 5. Build rotation matrix
    R = np.array([x_hat, y_hat, z_hat])
    
    return x_hat, y_hat, z_hat, R


def compute_l2_velocity(r_sun_t, r_earth_t, r_sun_t_plus_dt, r_earth_t_plus_dt, dt):
    """
    Compute L2 velocity using finite differences.
    
    Args:
        r_sun_t: Sun position at time t (km)
        r_earth_t: Earth position at time t (km)
        r_sun_t_plus_dt: Sun position at time t+dt (km)
        r_earth_t_plus_dt: Earth position at time t+dt (km)
        dt: Time step (seconds)
    
    Returns:
        v_l2: L2 velocity (km/s)
    """
    r_l2_t = compute_l2_position_approximate(r_sun_t, r_earth_t)
    r_l2_t_plus_dt = compute_l2_position_approximate(r_sun_t_plus_dt, r_earth_t_plus_dt)
    
    v_l2 = (r_l2_t_plus_dt - r_l2_t) / dt
    
    return v_l2


def compute_frame_angular_velocity(R_t, R_t_plus_dt, dt):
    """
    Compute frame angular velocity using finite differences.
    
    Args:
        R_t: Rotation matrix at time t
        R_t_plus_dt: Rotation matrix at time t+dt
        dt: Time step (seconds)
    
    Returns:
        omega_vec: Angular velocity vector in SEM-L2 frame (rad/s)
    """
    # Relative rotation
    delta_R = R_t_plus_dt @ R_t.T
    
    # Extract skew-symmetric matrix
    omega_skew = (delta_R - np.eye(3)) / dt
    
    # Extract angular velocity vector from skew matrix
    # [omega]_x = [[0, -wz, wy], [wz, 0, -wx], [-wy, wx, 0]]
    omega_vec = np.array([
        omega_skew[2, 1],  # omega_x
        omega_skew[0, 2],  # omega_y
        omega_skew[1, 0]   # omega_z
    ])
    
    return omega_vec


def transform_position_to_sem_l2(r_icrf, r_sun, r_earth, v_earth):
    """
    Transform a position from ICRF to SEM-L2 frame.
    
    Args:
        r_icrf: Position in ICRF (km)
        r_sun: Sun position in ICRF (km)
        r_earth: Earth position in ICRF (km)
        v_earth: Earth velocity in ICRF (km/s)
    
    Returns:
        r_sem_l2: Position in SEM-L2 frame (km)
    """
    # Compute L2 position
    r_l2 = compute_l2_position_approximate(r_sun, r_earth)
    
    # Build axes and rotation matrix
    x_hat, y_hat, z_hat, R = build_sem_l2_axes(r_sun, r_earth, v_earth)
    
    # Translate to L2-centered
    dr = r_icrf - r_l2
    
    # Rotate to SEM-L2
    r_sem_l2 = R @ dr
    
    return r_sem_l2


def transform_velocity_to_sem_l2(r_icrf, v_icrf, r_sun, r_earth, v_earth,
                                   r_sun_future, r_earth_future, v_earth_future, dt):
    """
    Transform velocity from ICRF to SEM-L2 frame with frame rotation correction.
    
    Args:
        r_icrf: Position in ICRF (km)
        v_icrf: Velocity in ICRF (km/s)
        r_sun: Sun position at time t (km)
        r_earth: Earth position at time t (km)
        v_earth: Earth velocity at time t (km/s)
        r_sun_future: Sun position at time t+dt (km)
        r_earth_future: Earth position at time t+dt (km)
        v_earth_future: Earth velocity at time t+dt (km/s)
        dt: Time step for finite differences (seconds)
    
    Returns:
        v_sem_l2: Velocity in SEM-L2 frame (km/s)
    """
    # Compute L2 position and velocity
    r_l2 = compute_l2_position_approximate(r_sun, r_earth)
    v_l2 = compute_l2_velocity(r_sun, r_earth, r_sun_future, r_earth_future, dt)
    
    # Build rotation matrices at t and t+dt
    x_hat, y_hat, z_hat, R_t = build_sem_l2_axes(r_sun, r_earth, v_earth)
    _, _, _, R_t_plus_dt = build_sem_l2_axes(r_sun_future, r_earth_future, v_earth_future)
    
    # Compute frame angular velocity
    omega_vec = compute_frame_angular_velocity(R_t, R_t_plus_dt, dt)
    
    # Relative velocity
    dv = v_icrf - v_l2
    dr = r_icrf - r_l2
    
    # Rotate to SEM-L2
    r_sem_l2 = R_t @ dr
    v_sem_l2_uncorrected = R_t @ dv
    
    # Apply angular velocity correction
    v_sem_l2 = v_sem_l2_uncorrected - np.cross(omega_vec, r_sem_l2)
    
    return v_sem_l2


def transform_trajectory_to_sem_l2(times, positions_icrf, velocities_icrf,
                                     sun_positions, sun_velocities,
                                     earth_positions, earth_velocities,
                                     sun_geocentric=None, sun_vel_geocentric=None):
    """
    Transform entire trajectory to SEM-L2 frame with FIXED ecliptic normal.
    This creates a proper rotating synodic frame.
    
    Args:
        times: Array of times (seconds)
        positions_icrf: Array of positions in ICRF (km), shape (n, 3)
        velocities_icrf: Array of velocities in ICRF (km/s), shape (n, 3)
        sun_positions: Sun positions in ICRF (km), shape (n, 3) - barycentric
        sun_velocities: Sun velocities in ICRF (km/s), shape (n, 3) - barycentric
        earth_positions: Earth positions in ICRF (km), shape (n, 3) - barycentric
        earth_velocities: Earth velocities in ICRF (km/s), shape (n, 3) - barycentric
        sun_geocentric: OPTIONAL - geocentric Sun positions for frame geometry (km)
        sun_vel_geocentric: OPTIONAL - geocentric Sun velocities for frame geometry (km/s)
    
    Returns:
        positions_sem_l2: Positions in SEM-L2 (km), shape (n, 3)
        velocities_sem_l2: Velocities in SEM-L2 (km/s), shape (n, 3)
    """
    n_points = len(times)
    positions_sem_l2 = np.zeros_like(positions_icrf)
    velocities_sem_l2 = np.zeros_like(velocities_icrf)
    
    # Use geocentric Sun if provided, otherwise use barycentric
    # For frame geometry, we need the actual Sun-Earth vector
    if sun_geocentric is not None:
        # Geocentric Sun IS the Earth-to-Sun vector
        # So "Earth" position in this geometry is at origin
        earth_geo = np.zeros_like(earth_positions)  # Earth at origin in geocentric
        sun_geo = sun_geocentric  # Sun position relative to Earth
        sun_vel_geo = sun_vel_geocentric
        print(f"  Using geocentric Sun for frame geometry (Sun-Earth distance: {np.linalg.norm(sun_geo[0]):.2e} km)")
    else:
        # Use barycentric positions
        earth_geo = earth_positions
        sun_geo = sun_positions
        sun_vel_geo = sun_velocities
        print(f"  Using barycentric positions for frame geometry")
    
    # DEBUG: Check what we're receiving
    print(f"  DEBUG: earth_positions shape: {earth_positions.shape}")
    print(f"  DEBUG: earth_positions[0]: {earth_positions[0]}")
    print(f"  DEBUG: earth_positions norm[0]: {np.linalg.norm(earth_positions[0])}")
    
    # Compute MEAN ecliptic normal (fixed for all time - proper rotating frame!)
    # Use barycentric Earth for this (actual orbital motion)
    print(f"Computing mean ecliptic normal from barycentric Earth orbit...")
    ecliptic_normals = []
    for i in range(min(100, n_points)):  # Sample first 100 points or all if fewer
        r_earth_norm = np.linalg.norm(earth_positions[i])
        if r_earth_norm > 1.0:
            n_ecl = np.cross(earth_positions[i], earth_velocities[i])
            norm_n_ecl = np.linalg.norm(n_ecl)
            if norm_n_ecl > 1e-6:
                ecliptic_normals.append(n_ecl / norm_n_ecl)
            else:
                print(f"  Warning: ecliptic normal at point {i} has near-zero norm: {norm_n_ecl}")
        else:
            print(f"  Warning: Earth position at point {i} too small: {r_earth_norm} km")
    
    if len(ecliptic_normals) > 0:
        mean_ecliptic_normal = np.mean(ecliptic_normals, axis=0)
        mean_ecliptic_normal = mean_ecliptic_normal / np.linalg.norm(mean_ecliptic_normal)
        print(f"Mean ecliptic normal: {mean_ecliptic_normal}")
        print(f"  (computed from {len(ecliptic_normals)} samples)")
    else:
        mean_ecliptic_normal = np.array([0, 0, 1])  # Fallback to ICRF Z
        print(f"Using ICRF Z as ecliptic normal (fallback - no valid samples found)")
    
    print(f"Transforming {n_points} trajectory points to SEM-L2 with FIXED ecliptic...")
    
    for i in range(n_points - 1):  # Stop at n-1 to have future point for velocity
        # Position transformation with fixed ecliptic normal
        # Use geocentric geometry for L2 calculation
        r_l2 = compute_l2_position_approximate(sun_geo[i], earth_geo[i])
        # But add barycentric Earth position to get L2 in barycentric frame
        if sun_geocentric is not None:
            r_l2_bary = earth_positions[i] + r_l2  # L2 offset from geocentric + Earth barycentric
        else:
            r_l2_bary = r_l2
        
        # Build frame using geocentric geometry
        _, _, _, R = build_sem_l2_axes(sun_geo[i], earth_geo[i], 
                                        earth_velocities[i], mean_ecliptic_normal)
        dr = positions_icrf[i] - r_l2_bary
        positions_sem_l2[i] = R @ dr
        
        # Velocity transformation with fixed ecliptic normal
        dt = times[i+1] - times[i]
        v_l2 = compute_l2_velocity(sun_geo[i], earth_geo[i],
                                    sun_geo[i+1], earth_geo[i+1], dt)
        # Add Earth velocity for barycentric reference
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
    velocities_sem_l2[-1] = velocities_sem_l2[-2]  # Approximate
    
    print("Transformation complete.")
    return positions_sem_l2, velocities_sem_l2


def verify_transformation(r_sun, r_earth, v_earth, r_l2=None):
    """
    Verify the coordinate transformation by checking orthonormality and alignment.
    
    Args:
        r_sun: Sun position in ICRF (km)
        r_earth: Earth position in ICRF (km)
        v_earth: Earth velocity in ICRF (km/s)
        r_l2: Optional L2 position (will compute if not provided)
    
    Returns:
        dict: Verification results
    """
    print("\n=== Verification of SEM-L2 Transformation ===")
    
    # Build axes
    x_hat, y_hat, z_hat, R = build_sem_l2_axes(r_sun, r_earth, v_earth)
    
    if r_l2 is None:
        r_l2 = compute_l2_position_approximate(r_sun, r_earth)
    
    results = {}
    
    # Check 1: Orthonormality
    print("\n1. Checking orthonormality of basis vectors:")
    norm_x = np.linalg.norm(x_hat)
    norm_y = np.linalg.norm(y_hat)
    norm_z = np.linalg.norm(z_hat)
    print(f"   |x_hat| = {norm_x:.10f} (should be 1.0)")
    print(f"   |y_hat| = {norm_y:.10f} (should be 1.0)")
    print(f"   |z_hat| = {norm_z:.10f} (should be 1.0)")
    results['norms_ok'] = np.allclose([norm_x, norm_y, norm_z], 1.0, atol=1e-9)
    
    dot_xy = np.dot(x_hat, y_hat)
    dot_xz = np.dot(x_hat, z_hat)
    dot_yz = np.dot(y_hat, z_hat)
    print(f"   x·y = {dot_xy:.10e} (should be ~0)")
    print(f"   x·z = {dot_xz:.10e} (should be ~0)")
    print(f"   y·z = {dot_yz:.10e} (should be ~0)")
    results['orthogonal_ok'] = np.allclose([dot_xy, dot_xz, dot_yz], 0.0, atol=1e-9)
    
    # Check 2: X-axis alignment with anti-Sun direction
    print("\n2. Checking X-axis alignment with Sun→L2 direction:")
    sun_to_l2 = r_l2 - r_sun
    sun_to_l2_hat = sun_to_l2 / np.linalg.norm(sun_to_l2)
    alignment = np.dot(x_hat, sun_to_l2_hat)
    print(f"   x_hat · (L2-Sun)_hat = {alignment:.10f} (should be ~1.0)")
    results['x_alignment_ok'] = np.isclose(alignment, 1.0, atol=1e-6)
    
    # Check 3: Z-axis alignment with ecliptic north
    print("\n3. Checking Z-axis alignment with ecliptic north:")
    # For Earth-centered frame, use ICRF Z as ecliptic north approximation
    if np.linalg.norm(r_earth) < 1.0:
        n_ecl_hat = np.array([0, 0, 1])
    else:
        n_ecl = np.cross(r_earth, v_earth)
        norm_n_ecl = np.linalg.norm(n_ecl)
        if norm_n_ecl < 1e-6:
            n_ecl_hat = np.array([0, 0, 1])
        else:
            n_ecl_hat = n_ecl / norm_n_ecl
    z_alignment = np.dot(z_hat, n_ecl_hat)
    print(f"   z_hat · n_ecl_hat = {z_alignment:.10f} (should be > 0)")
    results['z_alignment_ok'] = z_alignment > 0
    
    # Check 4: Transform Sun position
    print("\n4. Transforming Sun position to SEM-L2:")
    r_sun_sem = transform_position_to_sem_l2(r_sun, r_sun, r_earth, v_earth)
    print(f"   Sun in SEM-L2: [{r_sun_sem[0]:.2f}, {r_sun_sem[1]:.2f}, {r_sun_sem[2]:.2f}] km")
    sun_earth_dist = np.linalg.norm(r_earth - r_sun)
    print(f"   (Should be roughly [-{sun_earth_dist:.0f}, 0, 0] km)")
    results['sun_x_negative'] = r_sun_sem[0] < 0
    results['sun_yz_small'] = np.abs(r_sun_sem[1]) < 1000 and np.abs(r_sun_sem[2]) < 1000
    
    # Check 5: Transform Earth position
    print("\n5. Transforming Earth position to SEM-L2:")
    r_earth_sem = transform_position_to_sem_l2(r_earth, r_sun, r_earth, v_earth)
    print(f"   Earth in SEM-L2: [{r_earth_sem[0]:.2f}, {r_earth_sem[1]:.2f}, {r_earth_sem[2]:.2f}] km")
    l2_earth_dist = np.linalg.norm(r_l2 - r_earth)
    print(f"   (Should be roughly [-{l2_earth_dist:.0f}, 0, 0] km)")
    results['earth_x_negative'] = r_earth_sem[0] < 0
    results['earth_yz_small'] = np.abs(r_earth_sem[1]) < 1000 and np.abs(r_earth_sem[2]) < 1000
    
    # Summary
    print("\n=== Verification Summary ===")
    all_ok = all(results.values())
    if all_ok:
        print("✓ All checks passed!")
    else:
        print("✗ Some checks failed:")
        for key, value in results.items():
            if not value:
                print(f"  - {key}: FAILED")
    
    return results


# ============================================================================
# NEW: TRUE L2-CENTERED FRAME (using actual L2 position from Horizon)
# ============================================================================

def build_true_l2_axes(r_l2_actual, r_earth, v_earth):
    """
    Build coordinate frame centered on actual L2 position (from Horizon ephemeris).
    +X: Anti-Earth direction (from Earth to L2)
    +Z: Ecliptic north (from Earth's orbital angular momentum)
    +Y: Completes right-handed system
    
    Args:
        r_l2_actual: Actual L2 position in ICRF (km) from Horizon ephemeris
        r_earth: Earth position in ICRF (km)
        v_earth: Earth velocity in ICRF (km/s)
    
    Returns:
        x_hat, y_hat, z_hat: Unit vectors defining true L2 frame
        R: Rotation matrix (3x3) from ICRF to true L2 frame
    """
    # 1. Anti-Earth direction (from Earth to L2)
    u_x = r_l2_actual - r_earth
    x_hat = u_x / np.linalg.norm(u_x)
    
    # 2. Ecliptic north from Earth's orbital angular momentum
    if np.linalg.norm(r_earth) < 1.0:  # Earth at origin (shouldn't happen but handle it)
        n_ecl_hat = np.array([0, 0, 1])
    else:
        n_ecl = np.cross(r_earth, v_earth)
        norm_n_ecl = np.linalg.norm(n_ecl)
        if norm_n_ecl < 1e-6:
            n_ecl_hat = np.array([0, 0, 1])
        else:
            n_ecl_hat = n_ecl / norm_n_ecl
    
    # 3. Make z_hat orthogonal to x_hat
    z_perp = n_ecl_hat - np.dot(n_ecl_hat, x_hat) * x_hat
    norm_z_perp = np.linalg.norm(z_perp)
    if norm_z_perp < 1e-10:
        if abs(x_hat[2]) < 0.9:
            z_perp = np.array([0, 0, 1]) - np.dot([0, 0, 1], x_hat) * x_hat
        else:
            z_perp = np.array([0, 1, 0]) - np.dot([0, 1, 0], x_hat) * x_hat
        norm_z_perp = np.linalg.norm(z_perp)
    z_hat = z_perp / norm_z_perp
    
    # 4. Complete right-handed system
    y_hat = np.cross(z_hat, x_hat)
    
    # 5. Build rotation matrix
    R = np.array([x_hat, y_hat, z_hat])
    
    return x_hat, y_hat, z_hat, R


def transform_to_true_l2_frame(r_icrf, r_l2_actual, r_earth, v_earth):
    """
    Transform position from ICRF to true L2-centered frame.
    
    Args:
        r_icrf: Position in ICRF (km)
        r_l2_actual: Actual L2 position in ICRF (km) from Horizon
        r_earth: Earth position in ICRF (km)
        v_earth: Earth velocity in ICRF (km/s)
    
    Returns:
        r_l2_frame: Position in true L2 frame (km)
    """
    # Build frame
    _, _, _, R = build_true_l2_axes(r_l2_actual, r_earth, v_earth)
    
    # Transform: relative position then rotate
    r_rel = r_icrf - r_l2_actual
    r_l2_frame = R @ r_rel
    
    return r_l2_frame


def transform_trajectory_to_true_l2(times, positions_icrf, velocities_icrf,
                                    l2_positions, l2_velocities,
                                    earth_positions, earth_velocities):
    """
    Transform entire trajectory to true L2-centered frame.
    
    Args:
        times: Time array (seconds)
        positions_icrf: Satellite positions in ICRF (km), shape (n, 3)
        velocities_icrf: Satellite velocities in ICRF (km/s), shape (n, 3)
        l2_positions: Actual L2 positions from Horizon (km), shape (n, 3)
        l2_velocities: Actual L2 velocities from Horizon (km/s), shape (n, 3)
        earth_positions: Earth positions in ICRF (km), shape (n, 3)
        earth_velocities: Earth velocities in ICRF (km/s), shape (n, 3)
    
    Returns:
        positions_l2: Transformed positions in true L2 frame (km)
        velocities_l2: Transformed velocities in true L2 frame (km/s)
    """
    n = len(times)
    positions_l2 = np.zeros((n, 3))
    velocities_l2 = np.zeros((n, 3))
    
    print(f"Transforming {n} trajectory points to true L2 frame...")
    
    # Transform each point
    for i in range(n - 1):
        # Current frame
        _, _, _, R = build_true_l2_axes(
            l2_positions[i], earth_positions[i], earth_velocities[i]
        )
        
        # Next frame (for angular velocity)
        _, _, _, R_next = build_true_l2_axes(
            l2_positions[i + 1], earth_positions[i + 1], earth_velocities[i + 1]
        )
        
        # Position transformation
        r_rel = positions_icrf[i] - l2_positions[i]
        positions_l2[i] = R @ r_rel
        
        # Velocity transformation
        dt = times[i + 1] - times[i]
        omega_vec = compute_frame_angular_velocity(R, R_next, dt)
        
        v_rel = velocities_icrf[i] - l2_velocities[i]
        v_rot = R @ v_rel
        velocities_l2[i] = v_rot - np.cross(omega_vec, positions_l2[i])
    
    # Handle last point
    positions_l2[-1] = transform_to_true_l2_frame(
        positions_icrf[-1], l2_positions[-1],
        earth_positions[-1], earth_velocities[-1]
    )
    velocities_l2[-1] = velocities_l2[-2]  # Approximate
    
    print("True L2 frame transformation complete.")
    return positions_l2, velocities_l2


def plot_3d_trajectory(positions_sem_l2, title="Trajectory in SEM-L2 Frame", 
                       sun_pos=None, earth_traj=None, l2_sat_pos=None, save_path=None):
    """
    Plot trajectory in 3D.
    
    Args:
        positions_sem_l2: Array of positions (km), shape (n, 3)
        title: Plot title
        sun_pos: Sun position in SEM-L2 (optional, single point or array)
        earth_traj: Earth trajectory in SEM-L2 (optional, array)
        l2_sat_pos: L2 satellite position trajectory in SEM-L2 (optional)
        save_path: Path to save figure (optional)
    """
    fig = plt.figure(figsize=(14, 11))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot JWST trajectory
    ax.plot(positions_sem_l2[:, 0], positions_sem_l2[:, 1], positions_sem_l2[:, 2],
            'b-', linewidth=1.5, label='JWST Trajectory', alpha=0.8)
    
    # Plot L2 satellite trajectory if provided (should be stationary in proper frame)
    if l2_sat_pos is not None:
        ax.plot(l2_sat_pos[:, 0], l2_sat_pos[:, 1], l2_sat_pos[:, 2],
                'm-', linewidth=2, label='L2 Position (Horizon)', alpha=0.9)
        # Mark start/end of L2 trajectory to see if it moves
        ax.scatter(l2_sat_pos[0, 0], l2_sat_pos[0, 1], l2_sat_pos[0, 2],
                   c='magenta', s=150, marker='s', edgecolors='black', 
                   label='L2 Start', zorder=6)
        ax.scatter(l2_sat_pos[-1, 0], l2_sat_pos[-1, 1], l2_sat_pos[-1, 2],
                   c='purple', s=150, marker='D', edgecolors='black',
                   label='L2 End', zorder=6)
    
    # Plot Earth trajectory if provided (should be stationary in proper frame)
    if earth_traj is not None:
        if len(earth_traj.shape) == 1:  # Single point
            ax.scatter([earth_traj[0]], [earth_traj[1]], [earth_traj[2]], 
                       c='blue', s=200, marker='o', edgecolors='cyan',
                       label='Earth', zorder=5)
        else:  # Full trajectory
            ax.plot(earth_traj[:, 0], earth_traj[:, 1], earth_traj[:, 2],
                    'c-', linewidth=2, label='Earth Trajectory', alpha=0.9)
            # Mark start/end of Earth trajectory
            ax.scatter(earth_traj[0, 0], earth_traj[0, 1], earth_traj[0, 2],
                       c='cyan', s=150, marker='o', edgecolors='black',
                       label='Earth Start', zorder=6)
            ax.scatter(earth_traj[-1, 0], earth_traj[-1, 1], earth_traj[-1, 2],
                       c='blue', s=150, marker='o', edgecolors='black',
                       label='Earth End', zorder=6)
    
    # Plot start and end points for JWST
    ax.scatter(positions_sem_l2[0, 0], positions_sem_l2[0, 1], positions_sem_l2[0, 2],
               c='g', s=100, marker='o', label='JWST Start', zorder=5)
    ax.scatter(positions_sem_l2[-1, 0], positions_sem_l2[-1, 1], positions_sem_l2[-1, 2],
               c='r', s=100, marker='x', label='JWST End', zorder=5)
    
    # Plot theoretical L2 point at origin
    ax.scatter([0], [0], [0], c='gold', s=300, marker='*', 
               edgecolors='orange', linewidths=2,
               label='Origin (Frame Center)', zorder=7)
    
    # Plot Sun if provided
    if sun_pos is not None:
        if len(sun_pos.shape) == 1 or sun_pos.shape[0] == 1:  # Single point
            sun_pt = sun_pos if len(sun_pos.shape) == 1 else sun_pos[0]
            ax.scatter([sun_pt[0]], [sun_pt[1]], [sun_pt[2]], 
                       c='yellow', s=400, marker='o', edgecolors='orange',
                       linewidths=2, label='Sun', zorder=5)
    
    # Draw coordinate axes
    max_range = np.max(np.abs(positions_sem_l2)) * 0.3
    ax.quiver(0, 0, 0, max_range, 0, 0, color='r', arrow_length_ratio=0.1, label='+X (Anti-Sun)')
    ax.quiver(0, 0, 0, 0, max_range, 0, color='g', arrow_length_ratio=0.1, label='+Y')
    ax.quiver(0, 0, 0, 0, 0, max_range, color='b', arrow_length_ratio=0.1, label='+Z (Ecliptic North)')
    
    ax.set_xlabel('X (km) - Anti-Sun')
    ax.set_ylabel('Y (km)')
    ax.set_zlabel('Z (km) - Ecliptic North')
    ax.set_title(title)
    ax.legend()
    ax.grid(True)
    
    # Equal aspect ratio
    max_range = np.max(np.abs(positions_sem_l2))
    ax.set_xlim([-max_range, max_range])
    ax.set_ylim([-max_range, max_range])
    ax.set_zlim([-max_range, max_range])
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to {save_path}")
    
    plt.show()


def main():
    """Main execution function."""
    
    # Connect to STK
    root, scenario = connect_to_stk()
    
    # Set time step
    timestep_seconds = 3600  # 1 hour
    
    # Get Sun state vectors from STK
    print("\n=== Getting celestial body data from STK ===")
    print("Getting actual Sun ephemeris from STK...")
    
    try:
        sun_times, sun_pos_icrf, sun_vel_icrf = get_body_state_vectors(
            root, scenario, "Sun", timestep_seconds
        )
        print("✓ Successfully retrieved Sun ephemeris from STK")
    except Exception as e:
        print(f"✗ Failed to get Sun from STK: {e}")
        print("  Falling back to approximation (NOT RECOMMENDED)")
        
        # Fallback to approximation
        sat_name = "JWST"
        times_temp, _, _ = get_satellite_state_vectors(root, scenario, sat_name, timestep_seconds)
        n_points = len(times_temp)
        
        times_array = np.array(times_temp, dtype=float)
        days = times_array / 86400.0
        year_days = 365.25
        angles = 2 * np.pi * days / year_days
        
        sun_pos_icrf = np.zeros((n_points, 3))
        sun_pos_icrf[:, 0] = -AU_KM * np.cos(angles)
        sun_pos_icrf[:, 1] = -AU_KM * np.sin(angles)
        sun_pos_icrf[:, 2] = 0
        
        omega = 2 * np.pi / (year_days * 86400)
        sun_vel_icrf = np.zeros((n_points, 3))
        sun_vel_icrf[:, 0] = AU_KM * omega * np.sin(angles)
        sun_vel_icrf[:, 1] = -AU_KM * omega * np.cos(angles)
        sun_vel_icrf[:, 2] = 0
        
        sun_times = times_temp
    
    # Convert from geocentric to barycentric coordinates
    # In STK's geocentric ICRF:
    #   - Earth is at origin [0, 0, 0]
    #   - Sun position is Earth-to-Sun vector
    # In barycentric frame (solar system center of mass):
    #   - Barycenter is ~449 km from Sun's center toward Earth (M_earth / M_sun ≈ 3e-6)
    #   - Earth is at Sun_geocentric position (almost the full distance)
    #   - Sun is at tiny offset from origin
    print("\nConverting from geocentric ICRF to barycentric frame...")
    
    M_sun = 1.989e30  # kg
    M_earth = 5.972e24  # kg
    M_total = M_sun + M_earth
    
    # Mass fractions
    f_earth = M_earth / M_total  # ≈ 3.00e-6
    f_sun = M_sun / M_total      # ≈ 0.999997
    
    print(f"  Mass fraction Earth: {f_earth:.6e}")
    print(f"  Mass fraction Sun: {f_sun:.9f}")
    
    # Save original geocentric Sun position (this is the Earth-to-Sun vector)
    sun_geocentric = sun_pos_icrf.copy()
    sun_vel_geocentric = sun_vel_icrf.copy()
    
    # Sun_geocentric is the Earth-to-Sun vector (what STK gives us)
    # In barycentric frame:
    #   - Earth is at position ≈ +Sun_geocentric × (M_sun / M_total)
    #   - Sun is at position ≈ -Sun_geocentric × (M_earth / M_total)
    # But since M_sun >> M_earth:
    #   - Earth_bary ≈ Sun_geocentric × (1 - f_earth) ≈ Sun_geocentric
    #   - Sun_bary ≈ -Sun_geocentric × f_earth ≈ 0 (very small offset)
    
    earth_pos_icrf = sun_geocentric * f_sun  # Earth is almost at full geocentric Sun distance
    earth_vel_icrf = sun_vel_geocentric * f_sun
    
    # Update Sun to barycentric (tiny offset from origin)
    sun_pos_bary = -sun_geocentric * f_earth
    sun_vel_bary = -sun_vel_geocentric * f_earth
    
    earth_times = sun_times
    
    print(f"✓ Converted to barycentric frame")
    print(f"  Original geocentric Sun (Earth-to-Sun): {sun_geocentric[0]} km")
    print(f"    Norm: {np.linalg.norm(sun_geocentric[0]):.6e} km")
    print(f"  Earth barycentric: {earth_pos_icrf[0]} km")
    print(f"    Norm: {np.linalg.norm(earth_pos_icrf[0]):.6e} km")
    print(f"  Sun barycentric: {sun_pos_bary[0]} km")
    print(f"    Norm: {np.linalg.norm(sun_pos_bary[0]):.6e} km")
    
    # Verify: Earth - Sun should equal original Sun_geocentric
    verify_dist = np.linalg.norm(sun_geocentric[0])
    actual_dist = np.linalg.norm(earth_pos_icrf[0] - sun_pos_bary[0])
    print(f"  Earth-Sun distance check:")
    print(f"    Original geocentric: {verify_dist:.6e} km")
    print(f"    Barycentric (Earth-Sun): {actual_dist:.6e} km")
    print(f"    Difference: {abs(verify_dist - actual_dist):.6e} km (should be ~0)")
    
    # Use barycentric Sun position for transformations
    sun_pos_icrf = sun_pos_bary
    sun_vel_icrf = sun_vel_bary
    verify_dist = np.linalg.norm(sun_pos_icrf[0])
    actual_dist = np.linalg.norm(earth_pos_icrf[0] - sun_pos_bary[0])
    print(f"  Original geocentric Sun distance: {verify_dist:.2e} km")
    print(f"  Barycentric Earth-Sun distance: {actual_dist:.2e} km")
    print(f"  Difference: {abs(verify_dist - actual_dist):.6e} km (should be tiny)")
    
    # Use barycentric Sun position for transformations
    sun_pos_icrf = sun_pos_bary
    sun_vel_icrf = sun_vel_bary
    
    # Get satellite data
    sat_name = "JWST"  # Change this to your satellite name
    sat_times, sat_pos_icrf, sat_vel_icrf = get_satellite_state_vectors(
        root, scenario, sat_name, timestep_seconds
    )
    
    # Ensure Sun and satellite have same time points (Earth is derived from Sun)
    if len(sun_times) != len(sat_times):
        print(f"\n⚠ Warning: Objects have different time points!")
        print(f"  Sun: {len(sun_times)}, Satellite: {len(sat_times)}")
        print(f"  Using satellite time points and interpolating...")
        
        # Interpolate geocentric Sun (NOT the barycentric version) to match satellite times
        sat_times_array = np.array(sat_times, dtype=float)
        sun_times_array = np.array(sun_times, dtype=float)
        
        # Interpolate original geocentric Sun positions
        sun_geo_interp = np.zeros((len(sat_times), 3))
        sun_vel_geo_interp = np.zeros((len(sat_times), 3))
        for i in range(3):
            sun_geo_interp[:, i] = np.interp(sat_times_array, sun_times_array, sun_geocentric[:, i])
            sun_vel_geo_interp[:, i] = np.interp(sat_times_array, sun_times_array, sun_vel_geocentric[:, i])
        
        # Recompute barycentric positions from interpolated geocentric
        earth_pos_icrf = sun_geo_interp * f_sun
        earth_vel_icrf = sun_vel_geo_interp * f_sun
        
        sun_pos_icrf = -sun_geo_interp * f_earth  # Barycentric Sun
        sun_vel_icrf = -sun_vel_geo_interp * f_earth
        
        # Keep geocentric Sun for frame calculations
        sun_geocentric = sun_geo_interp
        sun_vel_geocentric = sun_vel_geo_interp
        
        times = sat_times
        print(f"✓ Interpolation complete")
        print(f"  Geocentric Sun[0] after interp: {sun_geocentric[0]} km (norm: {np.linalg.norm(sun_geocentric[0]):.2e})")
        print(f"  Earth barycentric[0] after interp: {earth_pos_icrf[0]} km (norm: {np.linalg.norm(earth_pos_icrf[0]):.2e})")
        print(f"  Sun barycentric[0] after interp: {sun_pos_icrf[0]} km (norm: {np.linalg.norm(sun_pos_icrf[0]):.2e})")
    else:
        times = sat_times
        print(f"✓ Time points match, no interpolation needed")
    
    print(f"\nSample Sun position (first point): {sun_pos_icrf[0]} km")
    print(f"Sample Sun velocity (first point): {sun_vel_icrf[0]} km/s")
    
    # Verify transformation at first time point
    print("\n=== Step-by-step verification at first time point ===")
    verify_transformation(sun_pos_icrf[0], earth_pos_icrf[0], earth_vel_icrf[0])
    
    # Convert JWST from geocentric to barycentric
    print("\n=== Converting JWST from geocentric to barycentric ===")
    print(f"  JWST geocentric[0]: {sat_pos_icrf[0]} km (norm: {np.linalg.norm(sat_pos_icrf[0]):.2e})")
    sat_pos_bary = sat_pos_icrf + earth_pos_icrf  # Add Earth's barycentric position
    sat_vel_bary = sat_vel_icrf + earth_vel_icrf
    print(f"  JWST barycentric[0]: {sat_pos_bary[0]} km (norm: {np.linalg.norm(sat_pos_bary[0]):.2e})")
    
    # Transform entire JWST trajectory
    print("\n=== Transforming JWST trajectory ===")
    print(f"  DEBUG BEFORE CALL: earth_pos_icrf shape: {earth_pos_icrf.shape}")
    print(f"  DEBUG BEFORE CALL: earth_pos_icrf[0]: {earth_pos_icrf[0]}")
    sat_pos_sem_l2, sat_vel_sem_l2 = transform_trajectory_to_sem_l2(
        times, sat_pos_bary, sat_vel_bary,  # Use barycentric JWST positions
        sun_pos_icrf, sun_vel_icrf,
        earth_pos_icrf, earth_vel_icrf,
        sun_geocentric, sun_vel_geocentric  # Pass geocentric for frame geometry
    )
    
    # Get L2 satellite data (SEMB-L2-horizon)
    print("\n=== Getting L2 satellite position from STK ===")
    l2_sat_pos_sem_l2 = None
    l2_sat_pos_icrf = None
    l2_sat_vel_icrf = None
    try:
        l2_sat_name = "SEMB-L2-horizon"
        l2_sat_times, l2_sat_pos_icrf, l2_sat_vel_icrf = get_satellite_state_vectors(
            root, scenario, l2_sat_name, timestep_seconds
        )
        print(f"Retrieved {len(l2_sat_times)} data points for {l2_sat_name}")
        
        # Interpolate if needed
        if len(l2_sat_times) != len(times):
            print(f"  Interpolating L2 satellite to match JWST time points...")
            times_array = np.array(times, dtype=float)
            l2_times_array = np.array(l2_sat_times, dtype=float)
            
            l2_pos_interp = np.zeros((len(times), 3))
            l2_vel_interp = np.zeros((len(times), 3))
            for i in range(3):
                l2_pos_interp[:, i] = np.interp(times_array, l2_times_array, l2_sat_pos_icrf[:, i])
                l2_vel_interp[:, i] = np.interp(times_array, l2_times_array, l2_sat_vel_icrf[:, i])
            
            l2_sat_pos_icrf = l2_pos_interp
            l2_sat_vel_icrf = l2_vel_interp
        
        # Convert L2 satellite from geocentric to barycentric
        # (STK's ICRF is geocentric, so L2 positions are relative to Earth)
        print(f"  Converting L2 satellite from geocentric to barycentric...")
        print(f"    L2 geocentric[0]: {l2_sat_pos_icrf[0]} km (norm: {np.linalg.norm(l2_sat_pos_icrf[0]):.2e})")
        l2_sat_pos_bary = l2_sat_pos_icrf + earth_pos_icrf  # Add Earth's barycentric position
        l2_sat_vel_bary = l2_sat_vel_icrf + earth_vel_icrf
        print(f"    L2 barycentric[0]: {l2_sat_pos_bary[0]} km (norm: {np.linalg.norm(l2_sat_pos_bary[0]):.2e})")
        
        # Transform L2 satellite trajectory to SEM-L2
        print("  Transforming L2 satellite trajectory to SEM-L2...")
        l2_sat_pos_sem_l2, l2_sat_vel_sem_l2 = transform_trajectory_to_sem_l2(
            times, l2_sat_pos_bary, l2_sat_vel_bary,  # Use barycentric positions
            sun_pos_icrf, sun_vel_icrf,
            earth_pos_icrf, earth_vel_icrf,
            sun_geocentric, sun_vel_geocentric  # Pass geocentric for frame geometry
        )
        print("✓ L2 satellite transformation complete")
    except Exception as e:
        print(f"✗ Could not retrieve L2 satellite: {e}")
        print("  Continuing without L2 satellite plot")
    
    # Print statistics
    print("\n=== JWST Trajectory Statistics in SEM-L2 ===")
    print(f"Position range:")
    print(f"  X: [{np.min(sat_pos_sem_l2[:, 0]):.2f}, {np.max(sat_pos_sem_l2[:, 0]):.2f}] km")
    print(f"  Y: [{np.min(sat_pos_sem_l2[:, 1]):.2f}, {np.max(sat_pos_sem_l2[:, 1]):.2f}] km")
    print(f"  Z: [{np.min(sat_pos_sem_l2[:, 2]):.2f}, {np.max(sat_pos_sem_l2[:, 2]):.2f}] km")
    
    print(f"\nVelocity range:")
    print(f"  VX: [{np.min(sat_vel_sem_l2[:, 0]):.6f}, {np.max(sat_vel_sem_l2[:, 0]):.6f}] km/s")
    print(f"  VY: [{np.min(sat_vel_sem_l2[:, 1]):.6f}, {np.max(sat_vel_sem_l2[:, 1]):.6f}] km/s")
    print(f"  VZ: [{np.min(sat_vel_sem_l2[:, 2]):.6f}, {np.max(sat_vel_sem_l2[:, 2]):.6f}] km/s")
    
    if l2_sat_pos_sem_l2 is not None:
        print("\n=== L2 Satellite (Horizon) Statistics in SEM-L2 ===")
        print(f"Position range:")
        print(f"  X: [{np.min(l2_sat_pos_sem_l2[:, 0]):.2f}, {np.max(l2_sat_pos_sem_l2[:, 0]):.2f}] km")
        print(f"  Y: [{np.min(l2_sat_pos_sem_l2[:, 1]):.2f}, {np.max(l2_sat_pos_sem_l2[:, 1]):.2f}] km")
        print(f"  Z: [{np.min(l2_sat_pos_sem_l2[:, 2]):.2f}, {np.max(l2_sat_pos_sem_l2[:, 2]):.2f}] km")
        
        # Calculate mean distance from origin (theoretical L2)
        distances = np.linalg.norm(l2_sat_pos_sem_l2, axis=1)
        print(f"\nDistance from origin (computed L2):")
        print(f"  Mean: {np.mean(distances):.2f} km")
        print(f"  Min: {np.min(distances):.2f} km")
        print(f"  Max: {np.max(distances):.2f} km")
        print(f"  Std: {np.std(distances):.2f} km")
    
    # ========================================================================
    # NEW: Transform to TRUE L2-centered frame (using actual L2 from Horizon)
    # ========================================================================
    if l2_sat_pos_icrf is not None:
        print("\n" + "="*70)
        print("=== Transforming to TRUE L2-CENTERED FRAME ===")
        print("="*70)
        
        # Transform JWST trajectory to true L2 frame
        jwst_pos_true_l2, jwst_vel_true_l2 = transform_trajectory_to_true_l2(
            times, sat_pos_icrf, sat_vel_icrf,
            l2_sat_pos_icrf, l2_sat_vel_icrf,
            earth_pos_icrf, earth_vel_icrf
        )
        
        # Transform Earth position to true L2 frame for reference
        print("  Transforming Earth trajectory to true L2 frame...")
        earth_pos_true_l2 = np.zeros((len(times), 3))
        for i in range(len(times)):
            earth_pos_true_l2[i] = transform_to_true_l2_frame(
                earth_pos_icrf[i], l2_sat_pos_icrf[i],
                earth_pos_icrf[i], earth_vel_icrf[i]
            )
        
        print("\n=== JWST Statistics in TRUE L2 Frame ===")
        print(f"Position range:")
        print(f"  X: [{np.min(jwst_pos_true_l2[:, 0]):.2f}, {np.max(jwst_pos_true_l2[:, 0]):.2f}] km")
        print(f"  Y: [{np.min(jwst_pos_true_l2[:, 1]):.2f}, {np.max(jwst_pos_true_l2[:, 1]):.2f}] km")
        print(f"  Z: [{np.min(jwst_pos_true_l2[:, 2]):.2f}, {np.max(jwst_pos_true_l2[:, 2]):.2f}] km")
        
        print(f"\nVelocity range:")
        print(f"  VX: [{np.min(jwst_vel_true_l2[:, 0]):.6f}, {np.max(jwst_vel_true_l2[:, 0]):.6f}] km/s")
        print(f"  VY: [{np.min(jwst_vel_true_l2[:, 1]):.6f}, {np.max(jwst_vel_true_l2[:, 1]):.6f}] km/s")
        print(f"  VZ: [{np.min(jwst_vel_true_l2[:, 2]):.6f}, {np.max(jwst_vel_true_l2[:, 2]):.6f}] km/s")
        
        print(f"\n=== Earth Trajectory in TRUE L2 Frame ===")
        print(f"Position range:")
        print(f"  X: [{np.min(earth_pos_true_l2[:, 0]):.2f}, {np.max(earth_pos_true_l2[:, 0]):.2f}] km")
        print(f"  Y: [{np.min(earth_pos_true_l2[:, 1]):.2f}, {np.max(earth_pos_true_l2[:, 1]):.2f}] km")
        print(f"  Z: [{np.min(earth_pos_true_l2[:, 2]):.2f}, {np.max(earth_pos_true_l2[:, 2]):.2f}] km")
        
        earth_distances = np.linalg.norm(earth_pos_true_l2, axis=1)
        print(f"\nEarth distance from true L2:")
        print(f"  Mean: {np.mean(earth_distances):.2f} km")
        print(f"  Min: {np.min(earth_distances):.2f} km")
        print(f"  Max: {np.max(earth_distances):.2f} km")
        print(f"  Std: {np.std(earth_distances):.2f} km")
        
        # L2 point itself should be at origin - verify
        print("\n=== Verifying L2 position in its own frame ===")
        l2_in_own_frame = transform_to_true_l2_frame(
            l2_sat_pos_icrf[0], l2_sat_pos_icrf[0],
            earth_pos_icrf[0], earth_vel_icrf[0]
        )
        print(f"L2 in its own frame (first point): {l2_in_own_frame} km (should be ~[0, 0, 0])")
    else:
        jwst_pos_true_l2 = None
        earth_pos_true_l2 = None
    
    # Compute Earth trajectory in SEM-L2 frame (for plotting)
    print("\n=== Computing Earth trajectory in SEM-L2 frame ===")
    earth_traj_sem_l2 = np.zeros((len(times), 3))
    for i in range(len(times)):
        earth_traj_sem_l2[i] = transform_position_to_sem_l2(
            earth_pos_icrf[i], sun_pos_icrf[i], earth_pos_icrf[i], earth_vel_icrf[i]
        )
    
    print(f"Earth trajectory in SEM-L2:")
    print(f"  X: [{np.min(earth_traj_sem_l2[:, 0]):.2f}, {np.max(earth_traj_sem_l2[:, 0]):.2f}] km")
    print(f"  Y: [{np.min(earth_traj_sem_l2[:, 1]):.2f}, {np.max(earth_traj_sem_l2[:, 1]):.2f}] km")
    print(f"  Z: [{np.min(earth_traj_sem_l2[:, 2]):.2f}, {np.max(earth_traj_sem_l2[:, 2]):.2f}] km")
    
    # Compute Sun position in SEM-L2 for first point (for plotting)
    sun_pos_sem = transform_position_to_sem_l2(
        sun_pos_icrf[0], sun_pos_icrf[0], earth_pos_icrf[0], earth_vel_icrf[0]
    )
    
    # Create plots directory
    plots_dir = Path(__file__).parent / "plots"
    plots_dir.mkdir(exist_ok=True)
    
    # Plot 3D trajectory in computed SEM-L2 frame
    print("\n=== Creating 3D visualization (Computed SEM-L2) ===")
    plot_3d_trajectory(
        sat_pos_sem_l2,
        title=f"{sat_name} vs L2-Horizon in SEM-L2 Frame (Computed)",
        sun_pos=sun_pos_sem,
        earth_traj=earth_traj_sem_l2,
        l2_sat_pos=l2_sat_pos_sem_l2,
        save_path=plots_dir / "trajectory_sem_l2_3d_real_sun.png"
    )
    
    # Plot in true L2 frame if available
    if jwst_pos_true_l2 is not None:
        print("\n=== Creating 3D visualization (True L2-Centered) ===")
        plot_3d_trajectory(
            jwst_pos_true_l2,
            title=f"{sat_name} in TRUE L2-Centered Frame (Anti-Earth X-axis)",
            sun_pos=None,  # Don't plot Sun in this frame
            earth_traj=earth_pos_true_l2,
            l2_sat_pos=None,  # L2 is at origin by definition
            save_path=plots_dir / "trajectory_true_l2_frame.png"
        )
    
    # ========================================================================
    # Analyze orbital period
    # ========================================================================
    print("\n" + "="*70)
    print("=== ORBITAL PERIOD ANALYSIS ===")
    print("="*70)
    
    # Use Y component for period analysis (should oscillate with halo orbit)
    y_positions = sat_pos_sem_l2[:, 1]
    times_array = np.array(times)
    times_days = (times_array - times_array[0]) / 86400  # Convert to days from start
    
    # Find zero crossings of Y position
    zero_crossings = []
    for i in range(len(y_positions) - 1):
        if y_positions[i] * y_positions[i+1] < 0:  # Sign change
            # Linear interpolation for more accurate crossing time
            t1, t2 = times_days[i], times_days[i+1]
            y1, y2 = y_positions[i], y_positions[i+1]
            t_cross = t1 - y1 * (t2 - t1) / (y2 - y1)
            zero_crossings.append(t_cross)
    
    print(f"Found {len(zero_crossings)} zero crossings in Y position")
    
    if len(zero_crossings) >= 2:
        # Period is 2× the time between consecutive crossings (full cycle)
        periods = []
        for i in range(len(zero_crossings) - 1):
            half_period = zero_crossings[i+1] - zero_crossings[i]
            periods.append(half_period * 2)
        
        mean_period = np.mean(periods)
        std_period = np.std(periods)
        
        print(f"\nOrbital period (from Y zero-crossings):")
        print(f"  Mean: {mean_period:.2f} days")
        print(f"  Std: {std_period:.2f} days")
        print(f"  Expected (for halo orbit in rotating frame): ~180 days")
        
        # Check if period is closer to 180 or 360 days
        if abs(mean_period - 180) < abs(mean_period - 360):
            print(f"  ✓ Period is close to 180 days (rotating frame working correctly)")
        else:
            print(f"  ⚠ Period is closer to {mean_period:.0f} days than 180 days")
            print(f"     This suggests the frame may not be rotating correctly")
    else:
        print("Not enough zero crossings found for period analysis")
    
    # Save trajectory data for further analysis
    export_dir = Path(__file__).parent / "exported_data"
    export_dir.mkdir(exist_ok=True)
    
    print(f"\n=== Saving trajectory data ===")
    np.savez(
        export_dir / "jwst_sem_l2_trajectory.npz",
        times=times_array,
        times_days=times_days,
        position=sat_pos_sem_l2,
        velocity=sat_vel_sem_l2,
        earth_position=earth_traj_sem_l2
    )
    print(f"Saved to: {export_dir / 'jwst_sem_l2_trajectory.npz'}")
    
    print("\n=== Complete! ===")


if __name__ == "__main__":
    main()

