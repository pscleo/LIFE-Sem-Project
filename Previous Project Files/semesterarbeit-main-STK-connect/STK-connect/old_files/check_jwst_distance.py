"""
Check JWST distance from Earth over time to find when it's at L2.
"""

import numpy as np
import matplotlib.pyplot as plt
import transform_to_sem_l2_v2 as trans
from pathlib import Path

def check_jwst_distance_over_time():
    """Check when JWST is at L2 distance."""
    
    print("="*80)
    print("JWST DISTANCE FROM EARTH OVER TIME")
    print("="*80)
    
    # Connect to STK
    root, scenario = trans.connect_to_stk()
    
    # Get JWST data with daily timesteps
    timestep = 86400  # 1 day
    
    print("\nGetting JWST orbit...")
    times, jwst_pos, jwst_vel = trans.get_satellite_state_vectors(
        root, scenario, "JWST", timestep
    )
    
    # Calculate distance from Earth
    distances = np.linalg.norm(jwst_pos, axis=1)
    
    # Convert times to days
    days = np.array(times, dtype=float) / 86400.0
    
    print(f"\nScenario duration: {days[-1]:.1f} days")
    print(f"Number of points: {len(distances)}")
    
    print(f"\nDistance statistics:")
    print(f"  Min: {np.min(distances)/1e6:.3f} million km")
    print(f"  Max: {np.max(distances)/1e6:.3f} million km")
    print(f"  Mean: {np.mean(distances)/1e6:.3f} million km")
    
    # Find when closest to L2 distance (1.5 million km)
    l2_distance = 1.5e6  # km
    distance_from_l2 = np.abs(distances - l2_distance)
    closest_idx = np.argmin(distance_from_l2)
    
    print(f"\nClosest to L2 distance:")
    print(f"  Day: {days[closest_idx]:.1f}")
    print(f"  Distance: {distances[closest_idx]/1e6:.3f} million km")
    print(f"  Diff from L2: {distance_from_l2[closest_idx]/1e3:.1f} thousand km")
    
    # Check if JWST ever reaches L2 distance
    at_l2 = distance_from_l2 < 0.1e6  # Within 100,000 km of L2
    if np.any(at_l2):
        l2_days = days[at_l2]
        print(f"\nJWST is at L2 distance (±100k km) for:")
        print(f"  Days {l2_days[0]:.1f} to {l2_days[-1]:.1f}")
        print(f"  Duration: {l2_days[-1] - l2_days[0]:.1f} days")
    else:
        print(f"\n⚠ JWST never reaches L2 distance in this scenario!")
        print(f"  This might be a close-up view or different mission phase")
    
    # Plot distance over time
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(days, distances/1e6, 'b-', linewidth=1, label='JWST distance from Earth')
    ax.axhline(y=1.5, color='r', linestyle='--', linewidth=2, label='L2 distance (~1.5 million km)', alpha=0.7)
    
    ax.set_xlabel('Time (days since scenario start)', fontsize=11)
    ax.set_ylabel('Distance from Earth (million km)', fontsize=11)
    ax.set_title('JWST Distance from Earth Over Time', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plots_dir = Path(__file__).parent / "plots"
    plots_dir.mkdir(exist_ok=True)
    save_path = plots_dir / "jwst_distance_from_earth.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\nPlot saved to: {save_path}")
    
    plt.show()
    
    return days, distances


if __name__ == "__main__":
    days, distances = check_jwst_distance_over_time()
