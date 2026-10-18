"""
List all available coordinate systems for Earth in STK.
"""
import sys
sys.path.insert(0, r'D:\Max\Uni\03-SpaceSystems\03-3. Semester\Semesterarbeit\code\STK-connect')
from transform_to_sem_l2_v2 import connect_to_stk

print("Connecting to STK...")
root, scenario = connect_to_stk()

# Get Earth as Planet
print("\nGetting Earth object...")
earth = root.GetObjectFromPath("Planet/Earth")
print(f"Got Earth object: {earth.InstanceName}")

# List coordinate systems for Cartesian Position
print("\n" + "="*70)
print("AVAILABLE COORDINATE SYSTEMS FOR EARTH CARTESIAN POSITION")
print("="*70)

cart_pos = earth.DataProviders.Item("Cartesian Position")
coord_group = cart_pos.Group
count = coord_group.Count

print(f"Total count: {count}")
print("-"*70)

for i in range(count):
    coord_system = coord_group.Item(i)
    print(f"{i+1}. {coord_system.Name}")

print("="*70)

# Try to get Earth position in different frames
print("\n" + "="*70)
print("TESTING EARTH POSITION IN DIFFERENT FRAMES")
print("="*70)

test_frames = ["ICRF", "J2000", "Inertial", "Fixed"]

for frame_name in test_frames:
    try:
        print(f"\nTrying frame: {frame_name}")
        pos_dp = earth.DataProviders.Item("Cartesian Position").Group.Item(frame_name)
        pos_result = pos_dp.Exec(scenario.StartTime, scenario.StopTime, 3600)
        
        import numpy as np
        x = np.array(pos_result.DataSets.GetDataSetByName("x").GetValues())
        y = np.array(pos_result.DataSets.GetDataSetByName("y").GetValues())
        z = np.array(pos_result.DataSets.GetDataSetByName("z").GetValues())
        
        print(f"  SUCCESS! Points: {len(x)}")
        print(f"  First position: [{x[0]:.2f}, {y[0]:.2f}, {z[0]:.2f}] km")
        print(f"  Position norm: {np.sqrt(x[0]**2 + y[0]**2 + z[0]**2):.2f} km")
        
    except Exception as e:
        print(f"  FAILED: {e}")

print("\n" + "="*70)
