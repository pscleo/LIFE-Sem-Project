%matplotlib tk

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
