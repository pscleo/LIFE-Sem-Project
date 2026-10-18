"""
Check if we can get Earth's position from Sun's perspective
or compute barycentric positions from Sun-Earth system
"""

import sys
import os

# Add Scripts folder to path to find pywin32 modules
scripts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'SA-venv', 'Scripts'))
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

# Now import win32com
import win32com.client

def connect_to_stk():
    """Connect to running STK instance"""
    print("Connecting to STK...")
    try:
        print("Connecting to STK 13...")
        uiApp = win32com.client.Dispatch("STK13.Application")
        uiApp.Visible = True
        root = uiApp.Personality2
        scenario = root.CurrentScenario
        print(f"Connected to scenario: {scenario.InstanceName}")
        return root, scenario
    except Exception as e:
        print(f"Error connecting to STK: {e}")
        raise

def main():
    root, scenario = connect_to_stk()
    
    # Set time format
    root.UnitPreferences.SetCurrentUnit("DateFormat", "EpSec")
    print("Set time format to EpSec")
    
    # Get Sun object
    print("\nGetting Sun object...")
    sun = root.GetObjectFromPath("Planet/Sun")
    print(f"Got Sun object: {sun.InstanceName}")
    
    # Try to get Earth position from Sun's perspective
    print("\n" + "="*80)
    print("CHECKING EARTH POSITION FROM SUN'S PERSPECTIVE")
    print("="*80)
    
    # Get Sun's data provider
    dp_sun = sun.DataProviders.Item("Cartesian Position")
    
    # List available coordinate systems for Sun
    print("\nAvailable coordinate systems for Sun:")
    group = dp_sun.Group
    count = group.Count
    print(f"Total count: {count}")
    for i in range(count):
        print(f"  {i+1}. {group.Item(i)}")
    
    # Try to get Sun position in ICRF (should be near origin in heliocentric)
    print("\n" + "-"*80)
    print("Sun position in ICRF (should be ~0 if Sun-centered, or Earth position if geocentric):")
    print("-"*80)
    
    # Get time array
    import numpy as np
    start_time = scenario.StartTime
    stop_time = scenario.StopTime
    timestep = 3600.0
    
    # Build time array
    time_array = []
    current = start_time
    while current <= stop_time:
        time_array.append(current)
        current += timestep
    
    dp_elements = dp_sun.Group.Item("ICRF").ExecElements(time_array)
    
    times = dp_elements.DataSets.Item("Time").GetValues()
    x = dp_elements.DataSets.Item("x").GetValues()
    y = dp_elements.DataSets.Item("y").GetValues()
    z = dp_elements.DataSets.Item("z").GetValues()
    
    print(f"Points: {len(times)}")
    print(f"First position: [{x[0]:.2e}, {y[0]:.2e}, {z[0]:.2e}] km")
    
    import math
    r0 = math.sqrt(x[0]**2 + y[0]**2 + z[0]**2)
    print(f"Position norm: {r0:.2e} km")
    
    # Now check if there's a "Planet/Earth" position relative to Sun
    print("\n" + "="*80)
    print("CHECKING VECTOR FROM SUN TO EARTH")
    print("="*80)
    
    # Get Earth object
    earth = root.GetObjectFromPath("Planet/Earth")
    
    # Try to get position of Earth relative to Sun using VectorGeometryTool
    print("\nTrying to compute Sun-to-Earth vector using VGT...")
    
    try:
        # Create a vector from Sun to Earth
        vgt = root.VectorGeometryTool
        vgt.VectorToolRoot = scenario
        
        # From Point: Sun (center)
        # To Point: Earth (center)
        from_obj = "CentralBody/Sun Center"
        to_obj = "CentralBody/Earth Center"
        
        print(f"From: {from_obj}")
        print(f"To: {to_obj}")
        
        # Set up the vector
        config = vgt.ConfigureVector(from_obj, to_obj, "Inertial")
        
        print("Vector configured successfully!")
        
    except Exception as e:
        print(f"VGT approach failed: {e}")
        print("\nAlternative: Compute from Sun ICRF position")
        print("If Sun position in ICRF = -Earth position in heliocentric")
        print("Then Earth barycentric ≈ Sun heliocentric position * (M_sun / (M_sun + M_earth))")
    
    # ALTERNATIVE APPROACH: Use Sun position in ICRF as -Earth_heliocentric
    print("\n" + "="*80)
    print("COMPUTING BARYCENTRIC POSITIONS FROM SUN ICRF DATA")
    print("="*80)
    
    print("\nSun ICRF position represents Earth-to-Sun vector in geocentric frame")
    print("Therefore: Sun_heliocentric = -Sun_ICRF")
    print("And: Earth_heliocentric = +Sun_ICRF")
    
    # Get masses
    M_sun = 1.989e30  # kg
    M_earth = 5.972e24  # kg
    M_total = M_sun + M_earth
    
    # Barycenter is at center of mass
    # r_barycenter = (M_sun * r_sun + M_earth * r_earth) / M_total
    # If we set heliocentric frame (Sun at origin):
    # r_sun_helio = 0
    # r_earth_helio = distance between Sun and Earth = Sun_ICRF
    # r_barycenter_helio = (M_earth / M_total) * r_earth_helio
    # 
    # To get barycentric positions:
    # r_sun_bary = r_sun_helio - r_barycenter_helio = -r_barycenter_helio
    # r_earth_bary = r_earth_helio - r_barycenter_helio
    
    barycenter_offset_factor = M_earth / M_total
    print(f"\nBarycenter offset from Sun: {barycenter_offset_factor:.6e} × Sun-Earth distance")
    print(f"This is approximately {barycenter_offset_factor * 149.6e6:.2f} km from Sun toward Earth")
    
    print("\nTo get barycentric coordinates:")
    print("  Earth_bary = Sun_ICRF × (1 - M_earth/M_total)")
    print("  Sun_bary = -Sun_ICRF × (M_earth/M_total)")
    
    # Compute example for first point
    sun_icrf = [x[0], y[0], z[0]]  # This is Earth-to-Sun in geocentric ICRF
    
    # Earth barycentric position
    earth_bary = [coord * (1 - barycenter_offset_factor) for coord in sun_icrf]
    # Sun barycentric position  
    sun_bary = [-coord * barycenter_offset_factor for coord in sun_icrf]
    
    print(f"\nExample at first timestep:")
    print(f"Sun ICRF (geocentric): [{sun_icrf[0]:.2e}, {sun_icrf[1]:.2e}, {sun_icrf[2]:.2e}] km")
    print(f"Earth barycentric: [{earth_bary[0]:.2e}, {earth_bary[1]:.2e}, {earth_bary[2]:.2e}] km")
    print(f"Sun barycentric: [{sun_bary[0]:.2e}, {sun_bary[1]:.2e}, {sun_bary[2]:.2e}] km")
    
    # Verify: Earth - Sun should equal Sun_ICRF
    diff = [earth_bary[i] - sun_bary[i] for i in range(3)]
    print(f"Earth - Sun: [{diff[0]:.2e}, {diff[1]:.2e}, {diff[2]:.2e}] km")
    print(f"Should match Sun_ICRF: {sun_icrf[0]:.2e}, {sun_icrf[1]:.2e}, {sun_icrf[2]:.2e}] km")
    
    print("\n" + "="*80)
    print("CONCLUSION:")
    print("We can derive barycentric positions from Sun ICRF data:")
    print("  1. Sun ICRF = Earth-to-Sun vector (geocentric)")
    print("  2. Earth_bary ≈ Sun_ICRF (Earth is ~99.9999% of the way from barycenter)")
    print("  3. Sun_bary ≈ -Sun_ICRF × (M_earth/M_sun) ≈ -Sun_ICRF × 3e-6")
    print("="*80)

if __name__ == "__main__":
    main()
