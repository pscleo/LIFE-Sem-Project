"""
Quick diagnostic: Check JWST position vs Sun direction at a few time points.
"""

import numpy as np
import transform_to_sem_l2_v2 as trans

def quick_check():
    """Quick check of JWST vs Sun alignment."""
    
    print("="*80)
    print("QUICK JWST vs SUN ALIGNMENT CHECK")
    print("="*80)
    
    # Connect to STK
    root, scenario = trans.connect_to_stk()
    
    # Get just the first few points
    sat_name = "JWST"
    timestep = 86400 * 30  # 30 days
    
    print(f"\nGetting JWST data (30-day timesteps)...")
    times, jwst_pos, jwst_vel = trans.get_satellite_state_vectors(
        root, scenario, sat_name, timestep
    )
    
    print(f"Retrieved {len(times)} points")
    
    # Generate Sun positions
    times_array = np.array(times, dtype=float)
    days = times_array / 86400.0
    angles = 2 * np.pi * days / 365.25
    
    sun_pos = np.zeros((len(times), 3))
    sun_pos[:, 0] = -trans.AU_KM * np.cos(angles)
    sun_pos[:, 1] = -trans.AU_KM * np.sin(angles)
    sun_pos[:, 2] = 0
    
    print("\n" + "="*80)
    print("CHECKING FIRST POINT")
    print("="*80)
    
    # First point analysis
    print(f"\nSun position (ICRF): [{sun_pos[0, 0]/1e6:.2f}, {sun_pos[0, 1]/1e6:.2f}, {sun_pos[0, 2]/1e6:.2f}] million km")
    print(f"JWST position (ICRF): [{jwst_pos[0, 0]/1e6:.2f}, {jwst_pos[0, 1]/1e6:.2f}, {jwst_pos[0, 2]/1e6:.2f}] million km")
    
    # Directions
    sun_dir = sun_pos[0] / np.linalg.norm(sun_pos[0])
    jwst_dir = jwst_pos[0] / np.linalg.norm(jwst_pos[0])
    anti_sun_dir = -sun_dir
    
    print(f"\nSun direction from Earth: [{sun_dir[0]:.6f}, {sun_dir[1]:.6f}, {sun_dir[2]:.6f}]")
    print(f"JWST direction from Earth: [{jwst_dir[0]:.6f}, {jwst_dir[1]:.6f}, {jwst_dir[2]:.6f}]")
    print(f"Anti-Sun direction: [{anti_sun_dir[0]:.6f}, {anti_sun_dir[1]:.6f}, {anti_sun_dir[2]:.6f}]")
    
    # Alignment
    alignment_anti_sun = np.dot(jwst_dir, anti_sun_dir)
    alignment_sun = np.dot(jwst_dir, sun_dir)
    
    print(f"\nJWST · Anti-Sun: {alignment_anti_sun:.6f}")
    print(f"JWST · Sun: {alignment_sun:.6f}")
    
    angle_deg = np.arccos(np.clip(alignment_anti_sun, -1, 1)) * 180/np.pi
    print(f"Angle from anti-Sun direction: {angle_deg:.2f}°")
    
    if alignment_anti_sun > 0.9:
        print("✓ JWST IS in anti-Sun direction")
    elif abs(alignment_anti_sun) < 0.1:
        print("⚠ JWST is PERPENDICULAR to Sun-Earth line!")
    elif alignment_sun > 0.9:
        print("✗ JWST is TOWARDS the Sun (wrong!)")
    else:
        print(f"⚠ JWST is at an angle to the Sun-Earth line")
    
    # Check if JWST X component has same sign as anti-Sun X
    print(f"\nSign check:")
    print(f"  Anti-Sun X > 0: {anti_sun_dir[0] > 0} (X = {anti_sun_dir[0]:.6f})")
    print(f"  JWST X > 0: {jwst_dir[0] > 0} (X = {jwst_dir[0]:.6f})")
    
    if (anti_sun_dir[0] > 0) == (jwst_dir[0] > 0):
        print("  ✓ Same sign on X")
    else:
        print("  ✗ OPPOSITE sign on X!")
    
    # Distance check
    jwst_dist = np.linalg.norm(jwst_pos[0])
    print(f"\nJWST distance from Earth: {jwst_dist/1e6:.3f} million km")
    print(f"Expected L2 distance: ~1.5 million km")
    
    # Now check what transform produces
    print("\n" + "="*80)
    print("TRANSFORMATION CHECK")
    print("="*80)
    
    r_l2 = trans.compute_l2_position_approximate(sun_pos[0], np.zeros(3))
    print(f"\nComputed L2 position: [{r_l2[0]/1e6:.2f}, {r_l2[1]/1e6:.2f}, {r_l2[2]/1e6:.2f}] million km")
    
    jwst_sem = trans.transform_position_to_sem_l2(jwst_pos[0], sun_pos[0], np.zeros(3), np.zeros(3))
    print(f"JWST in SEM-L2: [{jwst_sem[0]/1e6:.2f}, {jwst_sem[1]/1e6:.2f}, {jwst_sem[2]/1e6:.2f}] million km")
    
    print(f"\nIn SEM-L2 frame:")
    print(f"  X component (anti-Sun axis): {jwst_sem[0]/1e6:.3f} million km")
    print(f"  Y component: {jwst_sem[1]/1e6:.3f} million km")
    print(f"  Z component (ecliptic N): {jwst_sem[2]/1e6:.3f} million km")
    
    # The key insight
    print("\n" + "="*80)
    print("KEY INSIGHT")
    print("="*80)
    
    # What does a halo orbit look like?
    print("\nExpected JWST halo orbit in SEM-L2:")
    print("  - Should oscillate around L2 point (origin)")
    print("  - Typical shape: elongated ellipse or 'flattened circle'")
    print("  - X component: oscillates ± hundreds of thousands of km")
    print("  - Y component: oscillates ± hundreds of thousands to millions of km")
    print("  - Z component: oscillates ± hundreds of thousands of km")
    
    print(f"\nWhat we're seeing:")
    print(f"  - If orbit looks like 'figure-8' instead of ellipse")
    print(f"  - If orbit appears rotated 90° from expected")
    print(f"  - Then likely issue: SUN EPHEMERIS DIRECTION IS WRONG")
    
    print("\nMost likely issue:")
    print("  Our simplified Sun model assumes Sun moves in XY plane")
    print("  But STK's ICRF may have different orientation")
    print("  → Sun direction in ICRF doesn't match our assumption!")
    
    return sun_pos, jwst_pos


if __name__ == "__main__":
    sun_pos, jwst_pos = quick_check()
