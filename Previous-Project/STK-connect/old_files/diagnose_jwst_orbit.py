"""
Compare JWST orbit in ICRF vs SEM-L2 to identify the issue.
This will help us see if the problem is in the Sun ephemeris or the orbit itself.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import transform_to_sem_l2_v2 as trans
from pathlib import Path

def get_jwst_orbit_from_stk():
    """Get JWST orbit from STK in ICRF."""
    
    print("Connecting to STK and retrieving JWST orbit...")
    root, scenario = trans.connect_to_stk()
    
    # Get JWST data
    sat_name = "JWST"
    timestep_seconds = 3600 * 24  # 24 hours for faster processing
    
    times, pos_icrf, vel_icrf = trans.get_satellite_state_vectors(
        root, scenario, sat_name, timestep_seconds
    )
    
    print(f"Retrieved {len(times)} data points")
    return times, pos_icrf, vel_icrf


def analyze_jwst_orbit_icrf(times, positions):
    """Analyze JWST orbit in ICRF coordinates."""
    
    print("\n" + "=" * 80)
    print("JWST ORBIT ANALYSIS IN ICRF")
    print("=" * 80)
    
    print(f"\nPosition statistics:")
    print(f"  X: [{np.min(positions[:, 0]):.2f}, {np.max(positions[:, 0]):.2f}] km")
    print(f"  Y: [{np.min(positions[:, 1]):.2f}, {np.max(positions[:, 1]):.2f}] km")
    print(f"  Z: [{np.min(positions[:, 2]):.2f}, {np.max(positions[:, 2]):.2f}] km")
    
    # Distance from Earth
    distances = np.linalg.norm(positions, axis=1)
    print(f"\nDistance from Earth:")
    print(f"  Min: {np.min(distances):.2f} km ({np.min(distances)/1e6:.3f} million km)")
    print(f"  Max: {np.max(distances):.2f} km ({np.max(distances)/1e6:.3f} million km)")
    print(f"  Mean: {np.mean(distances):.2f} km ({np.mean(distances)/1e6:.3f} million km)")
    
    # Check if orbit is roughly at L2 distance
    expected_l2_distance = 1.5e6  # km
    print(f"\nExpected L2 distance: ~{expected_l2_distance/1e6:.1f} million km")
    if np.abs(np.mean(distances) - expected_l2_distance) < 0.5e6:
        print("✓ JWST is approximately at L2 distance")
    else:
        print("⚠ JWST distance doesn't match L2 expectation")
    
    # Dominant axis
    x_range = np.max(positions[:, 0]) - np.min(positions[:, 0])
    y_range = np.max(positions[:, 1]) - np.min(positions[:, 1])
    z_range = np.max(positions[:, 2]) - np.min(positions[:, 2])
    
    print(f"\nOrbital extent:")
    print(f"  X range: {x_range:.2f} km")
    print(f"  Y range: {y_range:.2f} km")
    print(f"  Z range: {z_range:.2f} km")
    
    # Check orbit shape
    print(f"\nOrbit shape indicators:")
    print(f"  Y/X ratio: {y_range/x_range:.3f}")
    print(f"  Z/X ratio: {z_range/x_range:.3f}")


def compare_sun_directions(times, jwst_pos):
    """Compare the direction to Sun from various reference points."""
    
    print("\n" + "=" * 80)
    print("SUN DIRECTION ANALYSIS")
    print("=" * 80)
    
    # Generate our approximate Sun ephemeris
    times_array = np.array(times, dtype=float)
    days = times_array / 86400.0
    year_days = 365.25
    angles = 2 * np.pi * days / year_days
    
    sun_dist = trans.AU_KM
    sun_pos = np.zeros((len(times), 3))
    sun_pos[:, 0] = -sun_dist * np.cos(angles)
    sun_pos[:, 1] = -sun_dist * np.sin(angles)
    sun_pos[:, 2] = 0
    
    # First point
    print(f"\nAt first time point (t=0):")
    print(f"  Sun position (our approx): {sun_pos[0]}")
    print(f"  JWST position: {jwst_pos[0]}")
    
    # Sun direction from Earth
    sun_from_earth = sun_pos[0] / np.linalg.norm(sun_pos[0])
    print(f"  Sun direction from Earth: {sun_from_earth}")
    
    # L2 should be anti-sunward from Earth
    expected_l2_dir = -sun_from_earth
    print(f"  Expected L2 direction (anti-Sun): {expected_l2_dir}")
    
    # Actual JWST direction from Earth
    jwst_from_earth = jwst_pos[0] / np.linalg.norm(jwst_pos[0])
    print(f"  JWST direction from Earth: {jwst_from_earth}")
    
    # Alignment check
    alignment = np.dot(jwst_from_earth, expected_l2_dir)
    print(f"  Alignment (JWST dir · expected L2 dir): {alignment:.6f}")
    
    if alignment > 0.9:
        print("  ✓ JWST is roughly in anti-Sun direction")
    else:
        print(f"  ✗ JWST is NOT in anti-Sun direction!")
        print(f"     Angle off: {np.arccos(alignment)*180/np.pi:.2f}°")
        
    # Check several time points
    print(f"\nChecking alignment over time:")
    for i in [0, len(times)//4, len(times)//2, 3*len(times)//4]:
        sun_dir = sun_pos[i] / np.linalg.norm(sun_pos[i])
        jwst_dir = jwst_pos[i] / np.linalg.norm(jwst_pos[i])
        expected_l2 = -sun_dir
        align = np.dot(jwst_dir, expected_l2)
        print(f"  t={i}: JWST·(-Sun) = {align:.6f}, angle = {np.arccos(np.clip(align,-1,1))*180/np.pi:.2f}°")


def plot_orbit_comparison(times, jwst_pos_icrf):
    """Plot JWST orbit in ICRF to see the actual shape."""
    
    print("\n" + "=" * 80)
    print("CREATING ORBIT VISUALIZATIONS")
    print("=" * 80)
    
    plots_dir = Path(__file__).parent / "plots"
    plots_dir.mkdir(exist_ok=True)
    
    # Generate Sun positions
    times_array = np.array(times, dtype=float)
    days = times_array / 86400.0
    year_days = 365.25
    angles = 2 * np.pi * days / year_days
    
    sun_dist = trans.AU_KM
    sun_pos = np.zeros((len(times), 3))
    sun_pos[:, 0] = -sun_dist * np.cos(angles)
    sun_pos[:, 1] = -sun_dist * np.sin(angles)
    sun_pos[:, 2] = 0
    
    # 3D plot in ICRF
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot JWST orbit
    ax.plot(jwst_pos_icrf[:, 0]/1e6, jwst_pos_icrf[:, 1]/1e6, jwst_pos_icrf[:, 2]/1e6,
            'b-', linewidth=1, label='JWST Orbit')
    
    # Plot Earth
    ax.scatter([0], [0], [0], c='blue', s=200, marker='o', label='Earth')
    
    # Plot sample Sun positions
    sample_indices = [0, len(sun_pos)//4, len(sun_pos)//2, 3*len(sun_pos)//4]
    for idx in sample_indices:
        ax.scatter([sun_pos[idx, 0]/1e6], [sun_pos[idx, 1]/1e6], [sun_pos[idx, 2]/1e6],
                   c='yellow', s=100, marker='o', alpha=0.5, edgecolors='orange')
    
    # Draw Sun-Earth line for first point
    ax.plot([0, sun_pos[0, 0]/1e6], [0, sun_pos[0, 1]/1e6], [0, sun_pos[0, 2]/1e6],
            'y--', linewidth=1, alpha=0.5, label='Earth-Sun line (t=0)')
    
    ax.set_xlabel('X (million km)')
    ax.set_ylabel('Y (million km)')
    ax.set_zlabel('Z (million km)')
    ax.set_title('JWST Orbit in ICRF (Earth-centered)', fontsize=14, fontweight='bold')
    ax.legend()
    
    save_path = plots_dir / "jwst_orbit_icrf_diagnostic.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"ICRF orbit plot saved to: {save_path}")
    
    # XY projection
    fig2, ax2 = plt.subplots(figsize=(10, 10))
    
    ax2.plot(jwst_pos_icrf[:, 0]/1e6, jwst_pos_icrf[:, 1]/1e6, 'b-', linewidth=1, label='JWST')
    ax2.scatter([0], [0], c='blue', s=200, marker='o', label='Earth', zorder=5)
    ax2.scatter([sun_pos[0, 0]/1e6], [sun_pos[0, 1]/1e6], c='yellow', s=300, 
                marker='o', edgecolors='orange', linewidths=2, label='Sun (t=0)', zorder=5)
    
    # Draw anti-Sun direction
    anti_sun = -sun_pos[0] / np.linalg.norm(sun_pos[0]) * 2  # 2 million km
    ax2.arrow(0, 0, anti_sun[0], anti_sun[1], head_width=0.1, head_length=0.15,
              fc='red', ec='red', linewidth=2, label='Anti-Sun direction', zorder=4)
    
    ax2.set_xlabel('X (million km)')
    ax2.set_ylabel('Y (million km)')
    ax2.set_title('JWST Orbit - XY Projection in ICRF', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    ax2.axis('equal')
    
    save_path2 = plots_dir / "jwst_orbit_icrf_xy_diagnostic.png"
    plt.savefig(save_path2, dpi=300, bbox_inches='tight')
    print(f"XY projection plot saved to: {save_path2}")
    
    plt.show()


def main():
    """Run diagnostic analysis."""
    
    # Get JWST orbit
    times, jwst_pos, jwst_vel = get_jwst_orbit_from_stk()
    
    # Analyze in ICRF
    analyze_jwst_orbit_icrf(times, jwst_pos)
    
    # Check Sun directions
    compare_sun_directions(times, jwst_pos)
    
    # Plot
    plot_orbit_comparison(times, jwst_pos)
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)
    print("\nKey questions to answer:")
    print("1. Does JWST orbit look correct in ICRF?")
    print("2. Is JWST actually in the anti-Sun direction from Earth?")
    print("3. Does our Sun ephemeris match the actual Sun direction?")
    print("4. Is the orbit oriented correctly relative to the Sun-Earth line?")
    print("=" * 80)


if __name__ == "__main__":
    main()
