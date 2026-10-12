"""
Explore VGT (Vector Geometry Tool) objects available in STK.
Phase 1: Research & Verification
"""
from stk_helpers import connect_to_stk

print("Starting VGT exploration...")

# Connect to STK
root, scenario = connect_to_stk(version=13)

# Get a satellite object
sat_name = "Webb-no-correction"
sat = root.GetObjectFromPath(f"Satellite/{sat_name}")
print(f"\nUsing satellite: {sat_name}")

# Access VGT interface
vgt = sat.Vgt
print("VGT interface accessed")

# Explore available Points
print("\n" + "="*60)
print("AVAILABLE POINTS")
print("="*60)
points = vgt.Points
print(f"Total points: {points.Count}")
for i in range(min(points.Count, 20)):  # Show first 20
    point = points.Item(i)
    print(f"{i+1}. {point.Name}")

# Explore available Vectors
print("\n" + "="*60)
print("AVAILABLE VECTORS")
print("="*60)
vectors = vgt.Vectors
print(f"Total vectors: {vectors.Count}")
for i in range(min(vectors.Count, 20)):  # Show first 20
    vector = vectors.Item(i)
    print(f"{i+1}. {vector.Name}")

# Explore available Axes
print("\n" + "="*60)
print("AVAILABLE AXES")
print("="*60)
axes = vgt.Axes
print(f"Total axes: {axes.Count}")
for i in range(min(axes.Count, 20)):  # Show first 20
    ax = axes.Item(i)
    print(f"{i+1}. {ax.Name}")

# Explore available Systems
print("\n" + "="*60)
print("AVAILABLE SYSTEMS")
print("="*60)
systems = vgt.Systems
print(f"Total systems: {systems.Count}")
for i in range(min(systems.Count, 20)):  # Show first 20
    sys = systems.Item(i)
    print(f"{i+1}. {sys.Name}")

# Check for Sun-related vectors
print("\n" + "="*60)
print("SEARCHING FOR SUN-RELATED VECTORS")
print("="*60)
for i in range(vectors.Count):
    vector = vectors.Item(i)
    if 'sun' in vector.Name.lower():
        print(f"Found: {vector.Name}")

# Check for ecliptic-related vectors
print("\n" + "="*60)
print("SEARCHING FOR ECLIPTIC-RELATED VECTORS")
print("="*60)
for i in range(vectors.Count):
    vector = vectors.Item(i)
    if 'ecliptic' in vector.Name.lower():
        print(f"Found: {vector.Name}")

# Check for L2-related points
print("\n" + "="*60)
print("SEARCHING FOR L2-RELATED POINTS")
print("="*60)
for i in range(points.Count):
    point = points.Item(i)
    if 'l2' in point.Name.lower() or 'libration' in point.Name.lower():
        print(f"Found: {point.Name}")

print("\nExploration complete!")
