"""
Test accessing position data using custom VGT coordinate system.
Phase 3: Data Extraction with Custom System
"""
from stk_helpers import connect_to_stk
import numpy as np

print("Testing data extraction with custom SEM_L2 system...")

# Connect to STK
root, scenario = connect_to_stk(version=13)

# Get satellite
sat_name = "Webb-no-correction"
sat = root.GetObjectFromPath(f"Satellite/{sat_name}")
timestep_seconds = 3600

print(f"\nTesting satellite: {sat_name}")

# Method 1: Try Cartesian Position data provider with custom system
print("\n=== Method 1: Standard Data Provider ===")
try:
    dp = sat.DataProviders.Item("Cartesian Position").Group.Item("SEM_L2_Custom")
    result = dp.Exec(scenario.StartTime, scenario.StopTime, timestep_seconds)
    times = np.array(result.DataSets.GetDataSetByName("Time").GetValues())
    print(f"SUCCESS with standard data provider! {len(times)} points")
except Exception as e:
    print(f"Standard data provider failed: {e}")

# Method 2: Try using VGT-based data provider
print("\n=== Method 2: VGT Data Provider ===")
try:
    # Access VGT
    vgt = sat.Vgt
    sem_l2_system = vgt.Systems.Item("SEM_L2_Custom")
    
    # Try getting position through VGT
    # Check if there's a data provider for this system
    print(f"System found in VGT: {sem_l2_system.Name}")
    
    # Try to use Cartesian Position with VGT system reference
    cart_pos = sat.DataProviders.Item("Cartesian Position")
    print(f"Data provider: {cart_pos.Name}")
    
    # Check available groups
    group = cart_pos.Group
    print(f"Available systems in group: {group.Count}")
    
except Exception as e:
    print(f"VGT data provider failed: {e}")

# Method 3: Try Position in System data provider  
print("\n=== Method 3: Position In System Data Provider ===")
try:
    dp_providers = sat.DataProviders
    print(f"Total data providers: {dp_providers.Count}")
    
    # List some data providers
    for i in range(min(dp_providers.Count, 30)):
        provider = dp_providers.Item(i)
        if 'position' in provider.Name.lower() or 'cartesian' in provider.Name.lower():
            print(f"  {provider.Name}")
    
    # Try "Position Velocity" data provider
    try:
        pos_vel = sat.DataProviders.Item("Position Velocity")
        print(f"\nFound Position Velocity provider")
        
        # Check if it has groups
        if hasattr(pos_vel, 'Group'):
            pv_group = pos_vel.Group
            print(f"Position Velocity has {pv_group.Count} coordinate systems")
    except:
        pass
        
except Exception as e:
    print(f"Position In System method failed: {e}")

# Method 4: Calculate position manually using coordinate transformation
print("\n=== Method 4: Manual Coordinate Transformation ===")
try:
    # Get position in ICRF
    dp_icrf = sat.DataProviders.Item("Cartesian Position").Group.Item("ICRF")
    result = dp_icrf.Exec(scenario.StartTime, scenario.StopTime, timestep_seconds)
    
    times = np.array(result.DataSets.GetDataSetByName("Time").GetValues())
    x_icrf = np.array(result.DataSets.GetDataSetByName("x").GetValues())
    y_icrf = np.array(result.DataSets.GetDataSetByName("y").GetValues())
    z_icrf = np.array(result.DataSets.GetDataSetByName("z").GetValues())
    
    print(f"Retrieved {len(times)} points in ICRF")
    print(f"ICRF position range:")
    print(f"  X: [{np.min(x_icrf):.1f}, {np.max(x_icrf):.1f}] km")
    print(f"  Y: [{np.min(y_icrf):.1f}, {np.max(y_icrf):.1f}] km")
    print(f"  Z: [{np.min(z_icrf):.1f}, {np.max(z_icrf):.1f}] km")
    
    print("\nNote: Manual transformation from ICRF to SEM-L2 would require:")
    print("  1. Sun position in ICRF at each time")
    print("  2. Earth position in ICRF at each time")
    print("  3. Calculate L2 position (Sun-Earth line, ~1.5M km from Earth)")
    print("  4. Define rotation matrix for anti-sunward X, ecliptic north Z")
    print("  5. Transform satellite position to L2-centered, rotated frame")
    
except Exception as e:
    print(f"Manual transformation setup failed: {e}")

print("\nTest complete!")
