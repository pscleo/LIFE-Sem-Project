"""
Additional visualizations for SEM-L2 coordinate transformation results.
Creates time-series plots and coordinate component plots.
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import win32com.client


def load_transformed_data():
    """Load data from the main transformation script."""
    # Import the main script to reuse functions
    import transform_to_sem_l2_v2 as trans
    
    # Connect to STK
    root, scenario = trans.connect_to_stk()
    
    # Get satellite data
    sat_name = "JWST"
    timestep_seconds = 3600
    
    times, sat_pos_icrf, sat_vel_icrf = trans.get_satellite_state_vectors(
        root, scenario, sat_name, timestep_seconds
    )
    
    # Generate Sun/Earth ephemeris
    n_points = len(times)
    earth_pos_icrf = np.zeros((n_points, 3))
    earth_vel_icrf = np.zeros((n_points, 3))
    
    times_array = np.array(times, dtype=float)
    days = times_array / 86400.0
    year_days = 365.25
    angles = 2 * np.pi * days / year_days
    
    sun_dist = trans.AU_KM
    sun_pos_icrf = np.zeros((n_points, 3))
    sun_pos_icrf[:, 0] = -sun_dist * np.cos(angles)
    sun_pos_icrf[:, 1] = -sun_dist * np.sin(angles)
    sun_pos_icrf[:, 2] = 0
    
    omega = 2 * np.pi / (year_days * 86400)
    sun_vel_icrf = np.zeros((n_points, 3))
    sun_vel_icrf[:, 0] = sun_dist * omega * np.sin(angles)
    sun_vel_icrf[:, 1] = -sun_dist * omega * np.cos(angles)
    sun_vel_icrf[:, 2] = 0
    
    earth_vel_icrf = -sun_vel_icrf
    
    # Transform to SEM-L2
    sat_pos_sem_l2, sat_vel_sem_l2 = trans.transform_trajectory_to_sem_l2(
        times, sat_pos_icrf, sat_vel_icrf,
        sun_pos_icrf, sun_vel_icrf,
        earth_pos_icrf, earth_vel_icrf
    )
    
    return times_array, sat_pos_sem_l2, sat_vel_sem_l2, sat_pos_icrf


def plot_position_components(times, positions, save_path=None):
    """Plot X, Y, Z position components over time."""
    # Convert time to days
    days = times / 86400.0
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    
    labels = ['X (Anti-Sun)', 'Y', 'Z (Ecliptic North)']
    colors = ['r', 'g', 'b']
    
    for i, (ax, label, color) in enumerate(zip(axes, labels, colors)):
        ax.plot(days, positions[:, i], color=color, linewidth=0.5)
        ax.set_ylabel(f'{label} (km)', fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='k', linestyle='--', linewidth=0.5, alpha=0.5)
    
    axes[-1].set_xlabel('Time (days)', fontsize=11)
    axes[0].set_title('JWST Position Components in SEM-L2 Frame', fontsize=13, fontweight='bold')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Position components plot saved to {save_path}")
    
    plt.show()


def plot_velocity_components(times, velocities, save_path=None):
    """Plot VX, VY, VZ velocity components over time."""
    days = times / 86400.0
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    
    labels = ['VX (Anti-Sun)', 'VY', 'VZ (Ecliptic North)']
    colors = ['r', 'g', 'b']
    
    for i, (ax, label, color) in enumerate(zip(axes, labels, colors)):
        ax.plot(days, velocities[:, i], color=color, linewidth=0.5)
        ax.set_ylabel(f'{label} (km/s)', fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='k', linestyle='--', linewidth=0.5, alpha=0.5)
    
    axes[-1].set_xlabel('Time (days)', fontsize=11)
    axes[0].set_title('JWST Velocity Components in SEM-L2 Frame', fontsize=13, fontweight='bold')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Velocity components plot saved to {save_path}")
    
    plt.show()


def plot_distance_from_l2(times, positions, save_path=None):
    """Plot distance from L2 point over time."""
    days = times / 86400.0
    distance = np.linalg.norm(positions, axis=1)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(days, distance / 1000, 'purple', linewidth=1)
    ax.set_xlabel('Time (days)', fontsize=11)
    ax.set_ylabel('Distance from L2 (×10³ km)', fontsize=11)
    ax.set_title('JWST Distance from L2 Point Over Time', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Add statistics
    mean_dist = np.mean(distance)
    min_dist = np.min(distance)
    max_dist = np.max(distance)
    
    ax.axhline(y=mean_dist/1000, color='orange', linestyle='--', 
               linewidth=1, label=f'Mean: {mean_dist:.0f} km', alpha=0.7)
    
    textstr = f'Min: {min_dist:.0f} km\nMax: {max_dist:.0f} km\nMean: {mean_dist:.0f} km'
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, 
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Distance plot saved to {save_path}")
    
    plt.show()


def plot_xy_projection(positions, save_path=None):
    """Plot XY projection (view from ecliptic north)."""
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Plot trajectory
    ax.plot(positions[:, 0], positions[:, 1], 'b-', linewidth=0.5, alpha=0.6)
    
    # Mark start and end
    ax.scatter(positions[0, 0], positions[0, 1], c='green', s=100, 
               marker='o', label='Start', zorder=5)
    ax.scatter(positions[-1, 0], positions[-1, 1], c='red', s=100, 
               marker='x', label='End', zorder=5)
    
    # Mark L2
    ax.scatter(0, 0, c='purple', s=200, marker='*', 
               label='L2 Point', zorder=5)
    
    # Mark every 30 days
    days_per_point = 3600 / 86400  # 1 hour timestep
    points_per_30days = int(30 / days_per_point)
    
    for i in range(0, len(positions), points_per_30days):
        ax.scatter(positions[i, 0], positions[i, 1], c='orange', 
                   s=20, alpha=0.5, zorder=3)
    
    ax.set_xlabel('X (km) - Anti-Sun Direction', fontsize=11)
    ax.set_ylabel('Y (km)', fontsize=11)
    ax.set_title('JWST Orbit - XY Projection (View from Ecliptic North)', 
                 fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.axis('equal')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"XY projection plot saved to {save_path}")
    
    plt.show()


def plot_xz_projection(positions, save_path=None):
    """Plot XZ projection (view from side)."""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Plot trajectory
    ax.plot(positions[:, 0], positions[:, 2], 'b-', linewidth=0.5, alpha=0.6)
    
    # Mark start and end
    ax.scatter(positions[0, 0], positions[0, 2], c='green', s=100, 
               marker='o', label='Start', zorder=5)
    ax.scatter(positions[-1, 0], positions[-1, 2], c='red', s=100, 
               marker='x', label='End', zorder=5)
    
    # Mark L2
    ax.scatter(0, 0, c='purple', s=200, marker='*', 
               label='L2 Point', zorder=5)
    
    ax.set_xlabel('X (km) - Anti-Sun Direction', fontsize=11)
    ax.set_ylabel('Z (km) - Ecliptic North', fontsize=11)
    ax.set_title('JWST Orbit - XZ Projection (Side View)', 
                 fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.axis('equal')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"XZ projection plot saved to {save_path}")
    
    plt.show()


def plot_orbital_speed(times, velocities, save_path=None):
    """Plot orbital speed over time."""
    days = times / 86400.0
    speed = np.linalg.norm(velocities, axis=1)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(days, speed, 'darkgreen', linewidth=1)
    ax.set_xlabel('Time (days)', fontsize=11)
    ax.set_ylabel('Speed (km/s)', fontsize=11)
    ax.set_title('JWST Orbital Speed in SEM-L2 Frame', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Add statistics
    mean_speed = np.mean(speed)
    ax.axhline(y=mean_speed, color='orange', linestyle='--', 
               linewidth=1, label=f'Mean: {mean_speed:.6f} km/s', alpha=0.7)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Orbital speed plot saved to {save_path}")
    
    plt.show()


def main():
    """Generate all additional plots."""
    print("Loading transformed data...")
    times, positions, velocities, pos_icrf = load_transformed_data()
    
    # Create plots directory
    plots_dir = Path(__file__).parent / "plots"
    plots_dir.mkdir(exist_ok=True)
    
    print("\nGenerating additional visualizations...")
    
    # Position components
    plot_position_components(times, positions, 
                            save_path=plots_dir / "position_components_sem_l2.png")
    
    # Velocity components
    plot_velocity_components(times, velocities,
                            save_path=plots_dir / "velocity_components_sem_l2.png")
    
    # Distance from L2
    plot_distance_from_l2(times, positions,
                         save_path=plots_dir / "distance_from_l2.png")
    
    # XY projection
    plot_xy_projection(positions,
                      save_path=plots_dir / "xy_projection_sem_l2.png")
    
    # XZ projection
    plot_xz_projection(positions,
                      save_path=plots_dir / "xz_projection_sem_l2.png")
    
    # Orbital speed
    plot_orbital_speed(times, velocities,
                      save_path=plots_dir / "orbital_speed_sem_l2.png")
    
    print("\n=== All visualizations complete! ===")
    print(f"Plots saved to: {plots_dir}")


if __name__ == "__main__":
    main()
