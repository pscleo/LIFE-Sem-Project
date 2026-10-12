"""
Data filtering and analysis utilities.

This module provides functions for:
- Filtering trajectories by time range
- Computing relative positions between satellites
- Analyzing drift rates
"""

import numpy as np
from datetime import datetime, timedelta


def filter_time_range(times, positions, velocities, start_date, duration_days):
    """
    Filter data to only include specified time range.
    
    Args:
        times: Array of epoch seconds
        positions: Position array (N, 3) in km
        velocities: Velocity array (N, 3) in km/s
        start_date: datetime object for start
        duration_days: Duration in days
    
    Returns:
        tuple: (times_filtered, positions_filtered, velocities_filtered)
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


def compute_relative_positions(trajectories_dict, base_name="Base"):
    """
    Compute position offsets relative to base satellite.
    
    Args:
        trajectories_dict: Dict of {sat_name: positions_sem_l2}
        base_name: Name of reference satellite
    
    Returns:
        dict: {sat_name: offset_positions} (excludes base satellite)
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
