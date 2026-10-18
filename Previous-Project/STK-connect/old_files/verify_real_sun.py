"""
Verify the transformation with real Sun data works correctly.
"""

import numpy as np
import transform_to_sem_l2_v2 as trans

def verify_real_sun_transformation():
    """Verify transformation using real Sun data."""
    
    print("="*80)
    print("VERIFICATION WITH REAL SUN DATA")
    print("="*80)
    
    # Connect to STK
    root, scenario = trans.connect_to_stk()
    
    # Get Sun and JWST data (just first few points)
    timestep = 86400  # 1 day
    
    print("\nGetting Sun ephemeris from STK...")
    sun_times, sun_pos, sun_vel = trans.get_body_state_vectors(
        root, scenario, "Sun", timestep
    )
    
    print("Getting JWST ephemeris from STK...")
    jwst_times, jwst_pos, jwst_vel = trans.get_satellite_state_vectors(
        root, scenario, "JWST", timestep
    )
    
    # Check first point
    print("\n" + "="*80)
    print("FIRST TIME POINT ANALYSIS")
    print("="*80)
    
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
    angle_deg = np.arccos(np.clip(alignment_anti_sun, -1, 1)) * 180/np.pi
    
    print(f"\nJWST · Anti-Sun: {alignment_anti_sun:.6f}")
    print(f"Angle from anti-Sun direction: {angle_deg:.2f}°")
    
    if alignment_anti_sun > 0.9:
        print("✓ JWST IS in anti-Sun direction")
    elif abs(alignment_anti_sun) < 0.1:
        print("⚠ JWST is PERPENDICULAR to Sun-Earth line")
    else:
        print(f"⚠ JWST is at {angle_deg:.1f}° from anti-Sun direction")
    
    # Distance check
    jwst_dist = np.linalg.norm(jwst_pos[0])
    print(f"\nJWST distance from Earth: {jwst_dist/1e6:.3f} million km")
    print(f"Expected L2 distance: ~1.5 million km")
    
    if abs(jwst_dist/1e6 - 1.5) < 0.5:
        print("✓ JWST is approximately at L2 distance")
    else:
        print("⚠ JWST distance doesn't match L2")
    
    # Transform to SEM-L2
    print("\n" + "="*80)
    print("SEM-L2 TRANSFORMATION")
    print("="*80)
    
    r_l2 = trans.compute_l2_position_approximate(sun_pos[0], np.zeros(3))
    print(f"\nComputed L2 position: [{r_l2[0]/1e6:.2f}, {r_l2[1]/1e6:.2f}, {r_l2[2]/1e6:.2f}] million km")
    
    # L2 distance from Earth
    l2_dist = np.linalg.norm(r_l2)
    print(f"L2 distance from Earth: {l2_dist/1e6:.3f} million km")
    
    # L2 direction
    l2_dir = r_l2 / l2_dist
    l2_alignment = np.dot(l2_dir, anti_sun_dir)
    print(f"L2 alignment with anti-Sun: {l2_alignment:.6f}")
    
    if l2_alignment > 0.99:
        print("✓ L2 is in anti-Sun direction")
    
    # Transform JWST
    jwst_sem = trans.transform_position_to_sem_l2(jwst_pos[0], sun_pos[0], np.zeros(3), np.zeros(3))
    print(f"\nJWST in SEM-L2: [{jwst_sem[0]/1e6:.2f}, {jwst_sem[1]/1e6:.2f}, {jwst_sem[2]/1e6:.2f}] million km")
    
    # Distance from L2
    jwst_from_l2 = np.linalg.norm(jwst_sem)
    print(f"JWST distance from L2: {jwst_from_l2/1e6:.3f} million km")
    
    # Check if reasonable for halo orbit
    if jwst_from_l2 < 1.0e6:  # Less than 1 million km from L2
        print("✓ JWST is within reasonable halo orbit distance from L2")
    else:
        print("⚠ JWST seems far from L2 for a halo orbit")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    print(f"\n1. Sun position: Real ephemeris from STK ✓")
    print(f"2. JWST at L2 distance: {abs(jwst_dist/1e6 - 1.5) < 0.5}")
    print(f"3. JWST in anti-Sun direction: {alignment_anti_sun > 0.8}")
    print(f"4. L2 computed correctly: {abs(l2_dist/1e6 - 1.5) < 0.1}")
    print(f"5. Transformation working: {jwst_from_l2 < 1.0e6}")
    
    if all([
        abs(jwst_dist/1e6 - 1.5) < 0.5,
        alignment_anti_sun > 0.8,
        abs(l2_dist/1e6 - 1.5) < 0.1,
        jwst_from_l2 < 1.0e6
    ]):
        print("\n✓✓✓ ALL CHECKS PASSED - TRANSFORMATION IS WORKING CORRECTLY! ✓✓✓")
    else:
        print("\n⚠ Some checks failed - review above")
    
    print("="*80)


if __name__ == "__main__":
    verify_real_sun_transformation()
