"""
================================================================================
DELTA-V ESTIMATION - CIRCULAR ORBIT DYNAMICS
================================================================================

Module: rotation-dv-estimate.py
Status: Analysis/validation tool (theoretical calculations)

PURPOSE
-------
Estimates Delta-V requirements for maintaining circular orbits at various radii
and periods. Used to validate simulation results and understand fuel consumption
trends for constellation station-keeping.

CALCULATION
-----------
For a circular orbit in gravity-free space:
  ΔV = 4π²R / P  (per orbit)
  
Where R = orbital radius (m), P = orbital period (s)

Cumulative ΔV over 180 days = ΔV_per_orbit × (180 days / Period)

OUTPUTS
-------
1. ΔV vs Period plot (fixed R=60m)
2. Cumulative ΔV over 180 days (multiple radii: 50-300m)
3. Console estimate for R=300m, 7-day period

KEY RESULTS
-----------
Shows inverse relationship: larger periods (less frequent maneuvers) require
less cumulative fuel, but longer individual maneuvers.

================================================================================
"""

# %matplotlib tk # magic command for interactive plots (uncomment if needed)

import numpy as np
import matplotlib.pyplot as plt

# Constants
R = 60  # radius in meters

def calculate_delta_v(radius, period):
    """
    Calculate delta-v needed for circular motion in gravity-free space, for one orbit.
    
    Args:
        radius: orbital radius in meters
        period: orbital period in seconds
    
    Returns:
        delta_v: required velocity in m/s
    """
    deltaV = 4 * np.pi**2 * radius / period
    return deltaV

# Create range of periods for plotting
periods = np.linspace(10, 500, 100)  # 10 to 500 seconds
delta_vs = [calculate_delta_v(R, p) for p in periods]

# Plot results
plt.figure(figsize=(10, 6))
plt.plot(periods, delta_vs, linewidth=2)
plt.xlabel('Period (seconds)')
plt.ylabel('Delta-v (m/s)')
plt.title(f'Delta-v Required for Circular Orbit (R = {R}m)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# Calculate cumulative delta-v over 180 days for a range of R values
radius_range = np.linspace(50, 300, 6)  # 50m to 300m
days_180 = 180 * 24 * 3600  # seconds
periods_range = np.linspace(3600*12, 28*24*3600, 100)  # 12 hours to 28 days

# Plot cumulative delta-v for different radii
plt.figure(figsize=(10, 6))
for radius in radius_range:
    delta_vs = [calculate_delta_v(radius, p) for p in periods_range]
    cumulative_delta_v = delta_vs * (days_180 / periods_range)
    plt.plot(periods_range / (24*3600), cumulative_delta_v, linewidth=2, label=f'R = {radius:.0f}m')

plt.xlabel('Period (days)', fontsize=14)
plt.ylabel('Cumulative Delta-v (m/s)', fontsize=14)
plt.title('Cumulative Delta-v Over 180 Days (Multiple Radii)', fontsize=16)
plt.yscale('log')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()

# %% Print cumulative dv estimate for 7day, 300m orbit
period_7days = 7 * 24 * 3600  # seconds
dv_7days_300m = calculate_delta_v(300, period_7days)
print(f'Cumulative delta-v for R=300m, Period=7days: {dv_7days_300m * (days_180 / period_7days):.2f} m/s over 180 days')
# %%
