"""
Coordinate transformation utilities for SEM-L2 frame.

This module provides functions for transforming positions and velocities
from ICRF/barycentric frames to the SEM-L2 rotating synodic frame.

The SEM-L2 frame is defined as:
- Origin at L2 Lagrange point
- X-axis: from Sun to L2 (approximately Sun-Earth line)
- Z-axis: perpendicular to Earth's orbital plane (ecliptic north)
- Y-axis: completes right-handed system
"""

import numpy as np

# Physical constants
M_SUN = 1.989e30  # kg
M_EARTH = 5.972e24  # kg
AU_KM = 149597870.7  # km


def compute_l2_position_approximate(r_sun, r_earth):
    """
    Compute approximate L2 position using cubic approximation.
    
    Uses the simplified formula: r_L2 ≈ r_Earth + d * (r_Earth - r_Sun) / |r_Earth - r_Sun|
    where d = a * (μ/3)^(1/3), μ = M_Earth / (M_Sun + M_EARTH), a = |r_Earth - r_Sun|
    
    Args:
        r_sun: Sun position vector (geocentric or barycentric) in km
        r_earth: Earth position vector (geocentric or barycentric) in km
    
    Returns:
        np.ndarray: L2 position vector in same frame as inputs (km)
    """
    r_es = r_earth - r_sun
    a = np.linalg.norm(r_es)
    mu = M_EARTH / (M_SUN + M_EARTH)
    d = a * (mu / 3) ** (1/3)
    r_l2 = r_earth + d * (r_es / a)
    return r_l2


def build_sem_l2_axes(r_sun, r_earth, v_earth, fixed_ecliptic_normal=None):
    """
    Build SEM-L2 coordinate frame axes at a given instant.
    
    Args:
        r_sun: Sun position vector (geocentric) in km
        r_earth: Earth position vector (geocentric, typically [0,0,0]) in km
        v_earth: Earth velocity vector for computing ecliptic normal (km/s)
        fixed_ecliptic_normal: Optional fixed ecliptic normal vector to use
    
    Returns:
        tuple: (x_hat, y_hat, z_hat, R)
            - x_hat: X-axis unit vector (Sun to L2 direction)
            - y_hat: Y-axis unit vector
            - z_hat: Z-axis unit vector (ecliptic north)
            - R: Rotation matrix from ICRF to SEM-L2 (3x3 array)
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


def build_sem_l2_axes_from_true_l2(r_l2_bary, v_l2_bary, r_sun_bary):
    """
    Build SEM-L2 coordinate frame axes using actual L2 satellite position and velocity.
    
    Frame definition:
    - Origin at L2 Lagrange point
    - X-axis: away from Sun (anti-sunward direction, POSITIVE X away from Sun)
    - Z-axis: L2's orbital angular momentum (perpendicular to L2's orbit)
    - Y-axis: completes right-handed system
    
    Args:
        r_l2_bary: L2 position vector (barycentric) in km
        v_l2_bary: L2 velocity vector (barycentric) in km/s
        r_sun_bary: Sun position vector (barycentric) in km
    
    Returns:
        tuple: (x_hat, y_hat, z_hat, R)
            - x_hat: X-axis unit vector (anti-sunward direction)
            - y_hat: Y-axis unit vector
            - z_hat: Z-axis unit vector (L2 orbital angular momentum)
            - R: Rotation matrix from ICRF to SEM-L2 (3x3 array)
    """
    # X-axis: from Sun to L2 (anti-sunward direction, POSITIVE X away from Sun)
    # This means Earth (which is between L2 and Sun) will be at NEGATIVE X
    r_sun_to_l2 = r_l2_bary - r_sun_bary
    x_hat = r_sun_to_l2 / np.linalg.norm(r_sun_to_l2)
    
    # Z-axis: L2's orbital angular momentum (perpendicular to L2's orbit around barycenter)
    # This is the natural rotation axis of the synodic frame
    L_l2 = np.cross(r_l2_bary, v_l2_bary)
    z_hat_raw = L_l2 / np.linalg.norm(L_l2)
    
    # IMPORTANT: Ensure Z points northward (positive Z component in ICRF)
    # If the angular momentum points south, flip it
    if z_hat_raw[2] < 0:
        z_hat = -z_hat_raw
    else:
        z_hat = z_hat_raw
    
    # Ensure z_hat is perpendicular to x_hat (Gram-Schmidt orthogonalization)
    z_hat = z_hat - np.dot(z_hat, x_hat) * x_hat
    z_hat_norm = np.linalg.norm(z_hat)
    if z_hat_norm < 1e-10:
        # Fallback if L2 orbit is nearly aligned with Sun-L2 line
        z_hat = np.array([0, 0, 1])
        z_hat = z_hat - np.dot(z_hat, x_hat) * x_hat
        z_hat = z_hat / np.linalg.norm(z_hat)
    else:
        z_hat = z_hat / z_hat_norm
    
    # Y-axis: completes right-handed system (Y = Z × X)
    y_hat = np.cross(z_hat, x_hat)
    y_hat = y_hat / np.linalg.norm(y_hat)
    
    # Rotation matrix (from ICRF to SEM-L2)
    R = np.vstack([x_hat, y_hat, z_hat])
    
    return x_hat, y_hat, z_hat, R


def compute_l2_velocity(r_sun_1, r_earth_1, r_sun_2, r_earth_2, dt):
    """
    Compute L2 velocity using finite differences.
    
    Args:
        r_sun_1: Sun position at time t1 (geocentric) in km
        r_earth_1: Earth position at time t1 (geocentric) in km
        r_sun_2: Sun position at time t2 (geocentric) in km
        r_earth_2: Earth position at time t2 (geocentric) in km
        dt: Time difference t2 - t1 (seconds)
    
    Returns:
        np.ndarray: L2 velocity vector (geocentric) in km/s
    """
    r_l2_1 = compute_l2_position_approximate(r_sun_1, r_earth_1)
    r_l2_2 = compute_l2_position_approximate(r_sun_2, r_earth_2)
    v_l2 = (r_l2_2 - r_l2_1) / dt
    return v_l2


def compute_frame_angular_velocity(R1, R2, dt):
    """
    Compute frame angular velocity from two rotation matrices.
    
    Args:
        R1: Rotation matrix at time t1 (3x3)
        R2: Rotation matrix at time t2 (3x3)
        dt: Time difference t2 - t1 (seconds)
    
    Returns:
        np.ndarray: Angular velocity vector (rad/s)
    """
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
    Transform trajectory from barycentric frame to SEM-L2 rotating frame.
    
    This function performs a complete transformation including:
    1. Computing L2 position at each time step
    2. Building SEM-L2 frame with fixed ecliptic normal
    3. Transforming position relative to L2
    4. Transforming velocity accounting for frame rotation
    
    Args:
        times: Time array (epoch seconds), shape (N,)
        positions_icrf: Satellite positions in barycentric ICRF (km), shape (N, 3)
        velocities_icrf: Satellite velocities in barycentric ICRF (km/s), shape (N, 3)
        sun_positions: Sun positions in barycentric ICRF (km), shape (N, 3)
        sun_velocities: Sun velocities in barycentric ICRF (km/s), shape (N, 3)
        earth_positions: Earth positions in barycentric ICRF (km), shape (N, 3)
        earth_velocities: Earth velocities in barycentric ICRF (km/s), shape (N, 3)
        sun_geocentric: Optional geocentric Sun positions for frame geometry (km)
        sun_vel_geocentric: Optional geocentric Sun velocities for frame geometry (km/s)
    
    Returns:
        tuple: (positions_sem_l2, velocities_sem_l2)
            - positions_sem_l2: Positions in SEM-L2 frame (km), shape (N, 3)
            - velocities_sem_l2: Velocities in SEM-L2 frame (km/s), shape (N, 3)
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
            r_l2_bary = r_l2 + earth_positions[i]
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
            v_l2_bary = v_l2 + earth_velocities[i]
        else:
            v_l2_bary = v_l2
        
        dv = velocities_icrf[i] - v_l2_bary
        
        R_next = build_sem_l2_axes(sun_geo[i+1], earth_geo[i+1],
                                    earth_velocities[i+1], mean_ecliptic_normal)[3]
        omega = compute_frame_angular_velocity(R, R_next, dt)
        
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


def transform_trajectory_to_sem_l2_true(times, positions_icrf, velocities_icrf,
                                         l2_positions_bary, l2_velocities_bary,
                                         sun_positions_bary):
    """
    Transform trajectory from barycentric frame to SEM-L2 rotating frame using true L2.
    
    This function uses the actual L2 satellite position (e.g., SEMB-L2-horizon from JPL)
    instead of approximations, providing the most accurate transformation. The frame's
    Z-axis is defined by L2's orbital angular momentum.
    
    Args:
        times: Time array (epoch seconds), shape (N,)
        positions_icrf: Satellite positions in barycentric ICRF (km), shape (N, 3)
        velocities_icrf: Satellite velocities in barycentric ICRF (km/s), shape (N, 3)
        l2_positions_bary: True L2 positions in barycentric ICRF (km), shape (N, 3)
        l2_velocities_bary: True L2 velocities in barycentric ICRF (km/s), shape (N, 3)
        sun_positions_bary: Sun positions in barycentric ICRF (km), shape (N, 3)
    
    Returns:
        tuple: (positions_sem_l2, velocities_sem_l2)
            - positions_sem_l2: Positions in SEM-L2 frame (km), shape (N, 3)
            - velocities_sem_l2: Velocities in SEM-L2 frame (km/s), shape (N, 3)
    """
    n_points = len(times)
    positions_sem_l2 = np.zeros_like(positions_icrf)
    velocities_sem_l2 = np.zeros_like(velocities_icrf)
    
    # Transform each point
    for i in range(n_points - 1):
        # Build SEM-L2 frame using true L2 position and velocity
        _, _, _, R = build_sem_l2_axes_from_true_l2(
            l2_positions_bary[i], 
            l2_velocities_bary[i],
            sun_positions_bary[i]
        )
        
        # Position transformation: express satellite position relative to L2
        dr = positions_icrf[i] - l2_positions_bary[i]
        positions_sem_l2[i] = R @ dr
        
        # Velocity transformation with frame rotation correction
        dt = times[i+1] - times[i]
        
        # Satellite velocity relative to L2 in inertial frame
        dv = velocities_icrf[i] - l2_velocities_bary[i]
        
        # Compute frame angular velocity
        R_next = build_sem_l2_axes_from_true_l2(
            l2_positions_bary[i+1],
            l2_velocities_bary[i+1],
            sun_positions_bary[i+1]
        )[3]
        omega = compute_frame_angular_velocity(R, R_next, dt)
        
        # Transform velocity: rotate to SEM-L2 frame and subtract rotation effect
        velocities_sem_l2[i] = R @ dv - np.cross(omega, positions_sem_l2[i])
    
    # Handle last point (copy rotation from previous step)
    _, _, _, R = build_sem_l2_axes_from_true_l2(
        l2_positions_bary[-1],
        l2_velocities_bary[-1],
        sun_positions_bary[-1]
    )
    dr = positions_icrf[-1] - l2_positions_bary[-1]
    positions_sem_l2[-1] = R @ dr
    velocities_sem_l2[-1] = velocities_sem_l2[-2]  # Copy previous velocity
    
    return positions_sem_l2, velocities_sem_l2


def convert_to_barycentric(geocentric_positions, geocentric_velocities,
                           sun_positions_geo, sun_velocities_geo):
    """
    Convert geocentric positions/velocities to barycentric frame.
    
    Args:
        geocentric_positions: Positions in geocentric ICRF (km), shape (N, 3)
        geocentric_velocities: Velocities in geocentric ICRF (km/s), shape (N, 3)
        sun_positions_geo: Sun positions in geocentric ICRF (km), shape (N, 3)
        sun_velocities_geo: Sun velocities in geocentric ICRF (km/s), shape (N, 3)
    
    Returns:
        tuple: (positions_bary, velocities_bary, earth_pos_bary, earth_vel_bary,
                sun_pos_bary, sun_vel_bary)
            All in barycentric ICRF frame
    """
    M_total = M_SUN + M_EARTH
    f_earth = M_EARTH / M_total
    f_sun = M_SUN / M_total
    
    # Earth position/velocity in barycentric frame
    # Correct barycentric positions/velocities (with proper signs)
    # Given r_sun_geo is the geocentric vector from Earth to Sun (Earth->Sun = r_ES):
    #   r_earth_bary = - (M_sun / (M_sun + M_earth)) * r_ES = -f_sun * r_ES
    #   r_sun_bary   = + (M_earth / (M_sun + M_earth)) * r_ES = +f_earth * r_ES
    earth_pos_bary = -sun_positions_geo * f_sun
    earth_vel_bary = -sun_velocities_geo * f_sun
    
    # Sun position/velocity in barycentric frame
    sun_pos_bary = sun_positions_geo * f_earth
    sun_vel_bary = sun_velocities_geo * f_earth
    
    # Satellite position/velocity in barycentric frame
    positions_bary = geocentric_positions + earth_pos_bary
    velocities_bary = geocentric_velocities + earth_vel_bary
    
    return (positions_bary, velocities_bary, 
            earth_pos_bary, earth_vel_bary,
            sun_pos_bary, sun_vel_bary)

