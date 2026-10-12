"""
Test SEM-L2 coordinate transformation.
Phase 4: Validation
"""
from stk_helpers import connect_to_stk, get_sat_positions, get_sat_positions_sem_l2
import numpy as np
import matplotlib.pyplot as plt

print("Testing SEM-L2 coordinate transformation...")

root, scenario = connect_to_stk(version=13)

sat_name = "Webb-no-correction"
timestep_seconds = 86400  # 1 day for faster testing

print(f"\nGetting positions for {sat_name}...")

# Get positions in both frames
times_icrf, pos_icrf = get_sat_positions(root, scenario, sat_name, timestep_seconds, frame="ICRF")
times_sem, pos_sem_l2 = get_sat_positions_sem_l2(root, scenario, sat_name, timestep_seconds)

print(f"\nRetrieved {len(times_icrf)} data points")

# Display position ranges
print(f"\n=== ICRF Frame ===")
print(f"X: [{np.min(pos_icrf[:,0]):.1f}, {np.max(pos_icrf[:,0]):.1f}] km")
print(f"Y: [{np.min(pos_icrf[:,1]):.1f}, {np.max(pos_icrf[:,1]):.1f}] km")
print(f"Z: [{np.min(pos_icrf[:,2]):.1f}, {np.max(pos_icrf[:,2]):.1f}] km")
print(f"Distance from origin: [{np.min(np.linalg.norm(pos_icrf, axis=1)):.1f}, {np.max(np.linalg.norm(pos_icrf, axis=1)):.1f}] km")

print(f"\n=== SEM-L2 Frame ===")
print(f"X: [{np.min(pos_sem_l2[:,0]):.1f}, {np.max(pos_sem_l2[:,0]):.1f}] km")
print(f"Y: [{np.min(pos_sem_l2[:,1]):.1f}, {np.max(pos_sem_l2[:,1]):.1f}] km")
print(f"Z: [{np.min(pos_sem_l2[:,2]):.1f}, {np.max(pos_sem_l2[:,2]):.1f}] km")
print(f"Distance from L2: [{np.min(np.linalg.norm(pos_sem_l2, axis=1)):.1f}, {np.max(np.linalg.norm(pos_sem_l2, axis=1)):.1f}] km")

# Create visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# ICRF X-Y plane
axes[0, 0].plot(pos_icrf[:,0], pos_icrf[:,1], 'b-', linewidth=0.5)
axes[0, 0].plot(0, 0, 'yo', markersize=8, label='Origin')
axes[0, 0].set_xlabel('X (km)')
axes[0, 0].set_ylabel('Y (km)')
axes[0, 0].set_title('ICRF Frame - XY Plane')
axes[0, 0].grid(True)
axes[0, 0].legend()
axes[0, 0].axis('equal')

# ICRF X-Z plane
axes[0, 1].plot(pos_icrf[:,0], pos_icrf[:,2], 'b-', linewidth=0.5)
axes[0, 1].plot(0, 0, 'yo', markersize=8, label='Origin')
axes[0, 1].set_xlabel('X (km)')
axes[0, 1].set_ylabel('Z (km)')
axes[0, 1].set_title('ICRF Frame - XZ Plane')
axes[0, 1].grid(True)
axes[0, 1].legend()
axes[0, 1].axis('equal')

# SEM-L2 X-Y plane
axes[1, 0].plot(pos_sem_l2[:,0], pos_sem_l2[:,1], 'r-', linewidth=0.5)
axes[1, 0].plot(0, 0, 'go', markersize=8, label='L2')
axes[1, 0].set_xlabel('X (km, anti-sunward)')
axes[1, 0].set_ylabel('Y (km)')
axes[1, 0].set_title('SEM-L2 Frame - XY Plane')
axes[1, 0].grid(True)
axes[1, 0].legend()
axes[1, 0].axis('equal')

# SEM-L2 X-Z plane
axes[1, 1].plot(pos_sem_l2[:,0], pos_sem_l2[:,2], 'r-', linewidth=0.5)
axes[1, 1].plot(0, 0, 'go', markersize=8, label='L2')
axes[1, 1].set_xlabel('X (km, anti-sunward)')
axes[1, 1].set_ylabel('Z (km, ecliptic north)')
axes[1, 1].set_title('SEM-L2 Frame - XZ Plane')
axes[1, 1].grid(True)
axes[1, 1].legend()
axes[1, 1].axis('equal')

plt.tight_layout()
plt.savefig('plots/sem_l2_transformation_test.png', dpi=300, bbox_inches='tight')
print(f"\nPlot saved to plots/sem_l2_transformation_test.png")
plt.show()

print("\n✓ SEM-L2 transformation complete!")
