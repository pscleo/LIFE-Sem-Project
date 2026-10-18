import numpy as np
from stk_helpers import (
    connect_to_stk,
    get_sat_positions,
    compute_position_differences,
    plot_position_differences
)
from datetime import datetime, timedelta

print("DEBUG01: Starting script - imports successful")

# --- Connect to STK ---
root, scenario = connect_to_stk(version=13)

# --- User settings ---
timestep_seconds = 2 * 24 * 60 * 60  # 48 hours step size
sat_names = ["Webb-no-correction", "Webb-Vx-p1", "Webb-Vx-m1"]
reference_sat = "Webb-no-correction"

# Plot start time filter
plot_start_date = datetime(2022, 4, 7)  # April 7, 2022
print(f"DEBUG01: Plot will start from: {plot_start_date}")

print(f"DEBUG01: Satellites to process: {sat_names}")
print(f"DEBUG01: Reference satellite: {reference_sat}")
print(f"DEBUG01: Time step: {timestep_seconds} seconds")

# --- Get positions for all satellites ---
print("DEBUG01: Starting position retrieval for all satellites...")
sat_positions = {}
ref_times = None

for name in sat_names:
    print(f"DEBUG01: Processing satellite: {name}")
    times, pos = get_sat_positions(root, scenario, name, timestep_seconds)
    sat_positions[name] = pos
    print(f"DEBUG01: Position data stored for {name}, shape: {pos.shape}")
    
    if name == reference_sat:
        ref_times = times
        print(f"DEBUG01: Reference times stored from {name}")

print("DEBUG01: All satellite positions retrieved successfully")

# --- Check time format ---
print(f"DEBUG01: Time data type: {type(ref_times[0])}")
print(f"DEBUG01: First time value: {ref_times[0]}")
print(f"DEBUG01: Last time value: {ref_times[-1]}")

# --- Convert time strings to datetime objects ---
print(f"DEBUG01: Converting time strings to datetime objects...")
time_datetimes = []
for time_str in ref_times:
    # Parse format: "9 Feb 2024 13:00:00.000000000"
    dt = datetime.strptime(str(time_str).split('.')[0], "%d %b %Y %H:%M:%S")
    time_datetimes.append(dt)

time_datetimes = np.array(time_datetimes)
print(f"DEBUG01: Converted {len(time_datetimes)} time values")
print(f"DEBUG01: First datetime: {time_datetimes[0]}")
print(f"DEBUG01: Last datetime: {time_datetimes[-1]}")

# --- Filter data to start from April 7, 2022 ---
print(f"DEBUG01: Filtering data to start from {plot_start_date}...")

# Find the index where datetime >= plot_start_date
mask = time_datetimes >= plot_start_date
start_idx = np.argmax(mask)  # First True value

if not mask[start_idx]:
    print(f"DEBUG01: WARNING - No data found after {plot_start_date}")
    print(f"DEBUG01: Data range: {time_datetimes[0]} to {time_datetimes[-1]}")
    start_idx = 0
else:
    print(f"DEBUG01: Filtering from index {start_idx}")
    print(f"DEBUG01: Actual plot start datetime: {time_datetimes[start_idx]}")

# Filter all data
ref_times_filtered = ref_times[start_idx:]
time_datetimes_filtered = time_datetimes[start_idx:]
sat_positions_filtered = {}
for name, pos in sat_positions.items():
    sat_positions_filtered[name] = pos[start_idx:]
    print(f"DEBUG01: Filtered {name}: {sat_positions_filtered[name].shape}")

print(f"DEBUG01: Data filtered - {len(ref_times_filtered)} data points remaining")

# --- Compute differences ---
diffs = compute_position_differences(sat_positions_filtered, reference_sat)

# --- Plot and save results ---
# Convert datetimes to numeric values for plotting (days from first point)
time_numeric = np.array([(dt - time_datetimes_filtered[0]).total_seconds() / 86400 
                         for dt in time_datetimes_filtered])

plot_position_differences(time_numeric, diffs, reference_sat, show=True, save=True)

print("DEBUG01: Script completed successfully")
