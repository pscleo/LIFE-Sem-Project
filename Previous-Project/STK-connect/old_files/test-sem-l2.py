"""
Test using the existing SEM_L2 coordinate system.
"""
from stk_helpers import connect_to_stk, get_sat_positions
import numpy as np

print("Testing SEM_L2 coordinate system...")

# Connect to STK
root, scenario = connect_to_stk(version=13)

# Test satellites
sat_name = "Webb-no-correction"
timestep_seconds = 3600  # 1 hour

print(f"\nAttempting to get positions in SEM_L2 frame...")

try:
    # Try using the existing SEM_L2 system
    times, pos = get_sat_positions(root, scenario, sat_name, timestep_seconds, frame="Sat_Syst_SEM_L2")
    
    print(f"\nSUCCESS! Retrieved {len(times)} data points")
    print(f"Position shape: {pos.shape}")
    print(f"\nFirst 3 positions (km):")
    print(pos[:3])
    print(f"\nPosition range:")
    print(f"  X: [{np.min(pos[:,0]):.1f}, {np.max(pos[:,0]):.1f}] km")
    print(f"  Y: [{np.min(pos[:,1]):.1f}, {np.max(pos[:,1]):.1f}] km")
    print(f"  Z: [{np.min(pos[:,2]):.1f}, {np.max(pos[:,2]):.1f}] km")
    
    # Compare with ICRF
    print(f"\n\nComparing with ICRF frame...")
    times_icrf, pos_icrf = get_sat_positions(root, scenario, sat_name, timestep_seconds, frame="ICRF")
    
    print(f"\nICRF Position range:")
    print(f"  X: [{np.min(pos_icrf[:,0]):.1f}, {np.max(pos_icrf[:,0]):.1f}] km")
    print(f"  Y: [{np.min(pos_icrf[:,1]):.1f}, {np.max(pos_icrf[:,1]):.1f}] km")
    print(f"  Z: [{np.min(pos_icrf[:,2]):.1f}, {np.max(pos_icrf[:,2]):.1f}] km")
    
    diff = pos - pos_icrf
    print(f"\nDifference (SEM_L2 - ICRF):")
    print(f"  Mean: [{np.mean(diff[:,0]):.1f}, {np.mean(diff[:,1]):.1f}, {np.mean(diff[:,2]):.1f}] km")
    print(f"  Max abs: {np.max(np.abs(diff)):.1f} km")
    
except Exception as e:
    print(f"\nFAILED: {e}")
    print("\nThe Sat_Syst_SEM_L2 system exists but may not be accessible via data providers.")

print("\nTest complete!")
