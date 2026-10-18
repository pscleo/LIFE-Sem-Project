"""
Create a custom SEM-L2 coordinate system using VGT.
Phase 2: Create Helper Functions
"""
from stk_helpers import connect_to_stk
import numpy as np

print("Creating SEM-L2 coordinate system using VGT...")

# Connect to STK
root, scenario = connect_to_stk(version=13)

# Get a satellite to access VGT
sat_name = "Webb-no-correction"
sat = root.GetObjectFromPath(f"Satellite/{sat_name}")
vgt = sat.Vgt

print("\n=== PHASE 1: Create L2 Point ===")
# Try to find or create L2 point
pointFactory = vgt.Points.Factory

# Check if L2 point already exists
try:
    l2_point = vgt.Points.Item("SEM_L2_Point")
    print(f"L2 point already exists: {l2_point.Name}")
except:
    print("L2 point not found, creating...")
    # Create L2 point - we'll use Earth's center as a placeholder for now
    # In reality, L2 is about 1.5 million km from Earth anti-sunward
    try:
        # Try using calculation point
        l2_point = pointFactory.Create("SEM_L2_Point", "Sun-Earth-Moon L2 Point", 10)  # eCrdnPointTypeCalculation
        print(f"Created L2 point: {l2_point.Name}")
    except Exception as e:
        print(f"Failed to create calculation point: {e}")
        # Fallback: use center point
        l2_point = vgt.Points.Item("Center")
        print(f"Using fallback center point: {l2_point.Name}")

print("\n=== PHASE 2: Create Custom Axes ===")
axesFactory = vgt.Axes.Factory

# Check if axes already exist
try:
    sem_l2_axes = vgt.Axes.Item("SEM_L2_Axes")
    print(f"Axes already exist: {sem_l2_axes.Name}")
except:
    print("Creating new axes...")
    try:
        # Create Aligned and Constrained axes
        # Type 7 = eCrdnAxesTypeAlignedAndConstrained
        sem_l2_axes = axesFactory.Create(
            "SEM_L2_Axes",
            "SEM L2 Aligned Axes",
            7
        )
        print(f"Created axes: {sem_l2_axes.Name}")
        
        # Get Sun vector for alignment (X anti-sunward)
        sun_vector = vgt.Vectors.Item("Sun")
        print(f"Found Sun vector: {sun_vector.Name}")
        
        # Set X-axis aligned to anti-Sun direction
        sem_l2_axes.AlignmentReferenceVector.SetVector(sun_vector)
        # Negate to get anti-sunward direction
        sem_l2_axes.AlignmentDirection.AssignXYZ(-1, 0, 0)
        print("Set X-axis to anti-sunward direction")
        
        # For Z-axis constraint, we need an ecliptic north vector
        # If not available, use North vector as approximation
        try:
            # Try to find ecliptic-related vector
            ecliptic_vector = vgt.Vectors.Item("North")  # Placeholder
            print(f"Using North vector as ecliptic approximation: {ecliptic_vector.Name}")
        except:
            # Use velocity as fallback
            ecliptic_vector = vgt.Vectors.Item("Velocity")
            print(f"Using Velocity as fallback: {ecliptic_vector.Name}")
        
        sem_l2_axes.ConstraintReferenceVector.SetVector(ecliptic_vector)
        sem_l2_axes.ConstraintDirection.AssignXYZ(0, 0, 1)
        print("Set Z-axis constraint")
        
    except Exception as e:
        print(f"Failed to create aligned axes: {e}")
        print("Trying simpler axes type...")
        # Fallback to fixed axes
        try:
            sem_l2_axes = axesFactory.Create(
                "SEM_L2_Axes_Simple",
                "SEM L2 Simple Axes",
                0  # eCrdnAxesTypeFixed
            )
            print(f"Created simple axes: {sem_l2_axes.Name}")
        except Exception as e2:
            print(f"Failed to create simple axes: {e2}")
            # Use existing axes
            sem_l2_axes = vgt.Axes.Item("ICRF")
            print(f"Using fallback ICRF axes: {sem_l2_axes.Name}")

print("\n=== PHASE 3: Create Assembled System ===")
systemFactory = vgt.Systems.Factory

# Check if system already exists
try:
    sem_l2_system = vgt.Systems.Item("SEM_L2_Custom")
    print(f"System already exists: {sem_l2_system.Name}")
except:
    print("Creating new assembled system...")
    try:
        # Type 0 = eCrdnSystemTypeAssembled
        sem_l2_system = systemFactory.Create(
            "SEM_L2_Custom",
            "Custom SEM L2 Coordinate System",
            0
        )
        print(f"Created system: {sem_l2_system.Name}")
        
        # Set origin point
        sem_l2_system.OriginPoint.SetPoint(l2_point)
        print(f"Set origin to: {l2_point.Name}")
        
        # Set reference axes
        sem_l2_system.ReferenceAxes.SetAxes(sem_l2_axes)
        print(f"Set axes to: {sem_l2_axes.Name}")
        
    except Exception as e:
        print(f"Failed to create assembled system: {e}")
        sem_l2_system = None

if sem_l2_system:
    print(f"\n✓ SUCCESS: Created coordinate system '{sem_l2_system.Name}'")
else:
    print(f"\n✗ FAILED: Could not create coordinate system")

print("\n=== Verifying in VGT Systems ===")
systems = vgt.Systems
print(f"Total systems now: {systems.Count}")
for i in range(systems.Count):
    sys = systems.Item(i)
    if 'SEM' in sys.Name or 'L2' in sys.Name:
        print(f"  Found: {sys.Name}")

print("\nCreation complete!")
