"""
Demonstrate SEM-L2 frame with 3D visualization of two satellites.
"""
from stk_helpers import connect_to_stk, get_sat_positions_sem_l2
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

print("3D Visualization in SEM-L2 Frame")
print("="*60)

root, scenario = connect_to_stk(version=13)

sat1_name = "JWST-from-start"
sat2_name = "Webb-no-correction"
timestep_seconds = 3600 * 24  # 1 day

print(f"\nGetting positions for {sat1_name}...")
times1, pos1_sem_l2 = get_sat_positions_sem_l2(root, scenario, sat1_name, timestep_seconds)

print(f"Getting positions for {sat2_name}...")
times2, pos2_sem_l2 = get_sat_positions_sem_l2(root, scenario, sat2_name, timestep_seconds)

print(f"\n{sat1_name}: {len(times1)} points")
print(f"{sat2_name}: {len(times2)} points")

# Calculate Earth position in SEM-L2 frame
# Earth is ~1.5M km sunward from L2
au_km = 149597870.7
l2_distance_from_earth = au_km * 0.01  # ~1% of AU
earth_pos_sem_l2 = np.array([-l2_distance_from_earth, 0, 0])  # Sunward direction (negative X)

# L2 is at origin in SEM-L2 frame
l2_pos_sem_l2 = np.array([0, 0, 0])

# Create 3D plot
fig = plt.figure(figsize=(16, 12))
ax = fig.add_subplot(111, projection='3d')

# Plot satellite trajectories
ax.plot(pos1_sem_l2[:,0]/1e3, pos1_sem_l2[:,1]/1e3, pos1_sem_l2[:,2]/1e3, 
        'b-', linewidth=1.5, alpha=0.7, label=sat1_name)
ax.plot(pos2_sem_l2[:,0]/1e3, pos2_sem_l2[:,1]/1e3, pos2_sem_l2[:,2]/1e3, 
        'r-', linewidth=1.5, alpha=0.7, label=sat2_name)

# Mark starting positions
ax.scatter(pos1_sem_l2[0,0]/1e3, pos1_sem_l2[0,1]/1e3, pos1_sem_l2[0,2]/1e3, 
          c='blue', s=100, marker='o', label=f'{sat1_name} start', zorder=5)
ax.scatter(pos2_sem_l2[0,0]/1e3, pos2_sem_l2[0,1]/1e3, pos2_sem_l2[0,2]/1e3, 
          c='red', s=100, marker='o', label=f'{sat2_name} start', zorder=5)

# Mark L2 point (origin)
ax.scatter(l2_pos_sem_l2[0]/1e3, l2_pos_sem_l2[1]/1e3, l2_pos_sem_l2[2]/1e3, 
          c='green', s=300, marker='*', label='L2 Point', zorder=10, edgecolors='black', linewidths=2)

# Mark Earth position
ax.scatter(earth_pos_sem_l2[0]/1e3, earth_pos_sem_l2[1]/1e3, earth_pos_sem_l2[2]/1e3, 
          c='cyan', s=300, marker='o', label='Earth', zorder=10, edgecolors='black', linewidths=2)

# Draw line from Earth to L2 (Sun-Earth line)
ax.plot([earth_pos_sem_l2[0]/1e3, l2_pos_sem_l2[0]/1e3],
        [earth_pos_sem_l2[1]/1e3, l2_pos_sem_l2[1]/1e3],
        [earth_pos_sem_l2[2]/1e3, l2_pos_sem_l2[2]/1e3],
        'k--', linewidth=2, alpha=0.5, label='Sun-Earth Line')

# Add arrow to show anti-sunward direction
arrow_start = l2_pos_sem_l2 / 1e3
arrow_end = arrow_start + np.array([500, 0, 0])  # 500,000 km in X direction
ax.quiver(arrow_start[0], arrow_start[1], arrow_start[2],
         arrow_end[0]-arrow_start[0], arrow_end[1]-arrow_start[1], arrow_end[2]-arrow_start[2],
         color='orange', arrow_length_ratio=0.3, linewidth=3, label='Anti-Sunward (+X)')

ax.set_xlabel('X (1000 km, anti-sunward)', fontsize=12)
ax.set_ylabel('Y (1000 km)', fontsize=12)
ax.set_zlabel('Z (1000 km, ecliptic north)', fontsize=12)
ax.set_title('SEM-L2 Frame: JWST Trajectories in 3D', fontsize=14, fontweight='bold')
ax.legend(loc='upper left', fontsize=10)
ax.grid(True, alpha=0.3)

# Set equal aspect ratio
max_range = max(
    np.ptp(pos1_sem_l2[:,0]/1e3), np.ptp(pos1_sem_l2[:,1]/1e3), np.ptp(pos1_sem_l2[:,2]/1e3),
    np.ptp(pos2_sem_l2[:,0]/1e3), np.ptp(pos2_sem_l2[:,1]/1e3), np.ptp(pos2_sem_l2[:,2]/1e3)
)
mid_x = (np.max(pos1_sem_l2[:,0]/1e3) + np.min(pos1_sem_l2[:,0]/1e3)) / 2
mid_y = (np.max(pos1_sem_l2[:,1]/1e3) + np.min(pos1_sem_l2[:,1]/1e3)) / 2
mid_z = (np.max(pos1_sem_l2[:,2]/1e3) + np.min(pos1_sem_l2[:,2]/1e3)) / 2

ax.set_xlim([mid_x - max_range/2, mid_x + max_range/2])
ax.set_ylim([mid_y - max_range/2, mid_y + max_range/2])
ax.set_zlim([mid_z - max_range/2, mid_z + max_range/2])

plt.tight_layout()
plt.savefig('plots/sem_l2_3d_visualization.png', dpi=300, bbox_inches='tight')
print("\nPlot saved: plots/sem_l2_3d_visualization.png")

# Print statistics
print("\n" + "="*60)
print("STATISTICS")
print("="*60)
print(f"\n{sat1_name}:")
print(f"  X range: [{np.min(pos1_sem_l2[:,0]):.0f}, {np.max(pos1_sem_l2[:,0]):.0f}] km")
print(f"  Y range: [{np.min(pos1_sem_l2[:,1]):.0f}, {np.max(pos1_sem_l2[:,1]):.0f}] km")
print(f"  Z range: [{np.min(pos1_sem_l2[:,2]):.0f}, {np.max(pos1_sem_l2[:,2]):.0f}] km")
print(f"  Distance from L2: [{np.min(np.linalg.norm(pos1_sem_l2, axis=1)):.0f}, {np.max(np.linalg.norm(pos1_sem_l2, axis=1)):.0f}] km")

print(f"\n{sat2_name}:")
print(f"  X range: [{np.min(pos2_sem_l2[:,0]):.0f}, {np.max(pos2_sem_l2[:,0]):.0f}] km")
print(f"  Y range: [{np.min(pos2_sem_l2[:,1]):.0f}, {np.max(pos2_sem_l2[:,1]):.0f}] km")
print(f"  Z range: [{np.min(pos2_sem_l2[:,2]):.0f}, {np.max(pos2_sem_l2[:,2]):.0f}] km")
print(f"  Distance from L2: [{np.min(np.linalg.norm(pos2_sem_l2, axis=1)):.0f}, {np.max(np.linalg.norm(pos2_sem_l2, axis=1)):.0f}] km")

print(f"\nEarth position in SEM-L2: [{earth_pos_sem_l2[0]:.0f}, {earth_pos_sem_l2[1]:.0f}, {earth_pos_sem_l2[2]:.0f}] km")
print(f"L2 position in SEM-L2: [{l2_pos_sem_l2[0]:.0f}, {l2_pos_sem_l2[1]:.0f}, {l2_pos_sem_l2[2]:.0f}] km")

print("\n" + "="*60)
print("✓ Visualization complete!")
print("="*60)

plt.show()
