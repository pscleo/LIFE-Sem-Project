"""Quick diagnostic to check Earth position interpolation issue."""
import sys
sys.path.insert(0, r'D:\Max\Uni\03-SpaceSystems\03-3. Semester\Semesterarbeit\code\STK-connect')

from transform_to_sem_l2_v2 import connect_to_stk, get_body_state_vectors, get_satellite_state_vectors
import numpy as np

# Connect to STK
root, scenario = connect_to_stk()

# Get data
timestep_seconds = 3600

print("Getting Sun...")
sun_times, sun_pos_icrf, sun_vel_icrf = get_body_state_vectors(root, scenario, "Sun", timestep_seconds)
print(f"  Sun: {len(sun_times)} points")
print(f"  Sun pos[0]: {sun_pos_icrf[0]}")

print("\nGetting Earth...")
earth_times, earth_pos_icrf, earth_vel_icrf = get_body_state_vectors(root, scenario, "Earth", timestep_seconds)
print(f"  Earth: {len(earth_times)} points")
print(f"  Earth pos[0]: {earth_pos_icrf[0]}")
print(f"  Earth pos[1]: {earth_pos_icrf[1]}")
print(f"  Earth pos[2]: {earth_pos_icrf[2]}")

print("\nGetting satellite...")
sat_times, sat_pos_icrf, sat_vel_icrf = get_satellite_state_vectors(root, scenario, "JWST", timestep_seconds)
print(f"  Satellite: {len(sat_times)} points")

print("\n" + "="*70)
print("INTERPOLATING...")
print("="*70)

sat_times_array = np.array(sat_times, dtype=float)
earth_times_array = np.array(earth_times, dtype=float)

print(f"sat_times_array[0:3]: {sat_times_array[0:3]}")
print(f"earth_times_array[0:3]: {earth_times_array[0:3]}")

print(f"\nBEFORE INTERP: earth_pos_icrf[0:3]:")
print(f"  {earth_pos_icrf[0]}")
print(f"  {earth_pos_icrf[1]}")
print(f"  {earth_pos_icrf[2]}")

earth_pos_interp = np.zeros((len(sat_times), 3))
for i in range(3):
    earth_pos_interp[:, i] = np.interp(sat_times_array, earth_times_array, earth_pos_icrf[:, i])

print(f"\nAFTER INTERP: earth_pos_interp[0:3]:")
print(f"  {earth_pos_interp[0]}")
print(f"  {earth_pos_interp[1]}")
print(f"  {earth_pos_interp[2]}")

print(f"\nInterpolation result norm[0]: {np.linalg.norm(earth_pos_interp[0])}")
