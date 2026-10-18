"""
Diagnostic script to analyze the SEM-L2 transformation and identify issues.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import transform_to_sem_l2_v2 as trans
from pathlib import Path

def analyze_frame_definition():
    """Analyze the frame definition to identify potential issues."""
    
    print("=" * 80)
    print("SEM-L2 TRANSFORMATION DIAGNOSTIC ANALYSIS")
    print("=" * 80)
    
    # Test data
    r_sun = np.array([-149597870.7, -2571258.7, 0.0])  # Sun in ICRF (Earth-centered)
    r_earth = np.array([0.0, 0.0, 0.0])  # Earth at origin
    v_earth = np.array([0.0, 0.0, 0.0])  # Earth velocity
    
    print("\n[1] EXPECTED FRAME DEFINITION (from plan):")
    print("    +X axis: Anti-Sun (points AWAY from Sun)")
    print("    +Z axis: Ecliptic north")
    print("    +Y axis: Completes right-handed system (Y = Z × X)")
    
    # Compute L2 position
    r_l2 = trans.compute_l2_position_approximate(r_sun, r_earth)
    
    print("\n[2] VECTORS IN PROBLEM:")
    print(f"    Sun position (ICRF):  {r_sun}")
    print(f"    Earth position (ICRF): {r_earth}")
    print(f"    L2 position (ICRF):    {r_l2}")
    
    # Sun-to-Earth vector
    sun_to_earth = r_earth - r_sun
    sun_to_earth_hat = sun_to_earth / np.linalg.norm(sun_to_earth)
    
    # Sun-to-L2 vector
    sun_to_l2 = r_l2 - r_sun
    sun_to_l2_hat = sun_to_l2 / np.linalg.norm(sun_to_l2)
    
    # Earth-to-L2 vector (should be anti-sunward)
    earth_to_l2 = r_l2 - r_earth
    earth_to_l2_hat = earth_to_l2 / np.linalg.norm(earth_to_l2)
    
    print("\n[3] DIRECTIONAL VECTORS:")
    print(f"    Sun→Earth (normalized):  {sun_to_earth_hat}")
    print(f"    Sun→L2 (normalized):     {sun_to_l2_hat}")
    print(f"    Earth→L2 (normalized):   {earth_to_l2_hat}")
    
    # Build axes
    x_hat, y_hat, z_hat, R = trans.build_sem_l2_axes(r_sun, r_earth, v_earth)
    
    print("\n[4] COMPUTED SEM-L2 AXES:")
    print(f"    X-axis: {x_hat}")
    print(f"    Y-axis: {y_hat}")
    print(f"    Z-axis: {z_hat}")
    
    print("\n[5] EXPECTED vs ACTUAL X-AXIS:")
    print(f"    Expected (anti-Sun from L2): Earth→L2 direction = {earth_to_l2_hat}")
    print(f"    Actual X-axis:                                    {x_hat}")
    print(f"    Alignment (should be ~1.0): {np.dot(x_hat, earth_to_l2_hat):.10f}")
    
    # Check what direction X actually points
    print("\n[6] X-AXIS DIRECTION ANALYSIS:")
    print(f"    X·(Sun→Earth): {np.dot(x_hat, sun_to_earth_hat):.10f}")
    print(f"    X·(Earth→L2):  {np.dot(x_hat, earth_to_l2_hat):.10f}")
    print(f"    X·(Sun→L2):    {np.dot(x_hat, sun_to_l2_hat):.10f}")
    
    # The issue: let's check what the code actually computes
    print("\n[7] CHECKING CODE LOGIC:")
    print("    In build_sem_l2_axes():")
    print("      r_l2 = compute_l2_position_approximate(r_sun, r_earth)")
    print(f"      r_l2 = {r_l2}")
    print("      u_x = r_l2 - r_sun")
    print(f"      u_x = {r_l2 - r_sun}")
    print("      x_hat = u_x / |u_x|")
    print(f"      x_hat = {x_hat}")
    
    print("\n[8] PROBLEM IDENTIFICATION:")
    if np.dot(x_hat, sun_to_l2_hat) > 0.99:
        print("    ✓ X points from Sun→L2 (CORRECT)")
    else:
        print("    ✗ X does NOT point from Sun→L2")
    
    if np.dot(x_hat, earth_to_l2_hat) > 0.99:
        print("    ✓ X points from Earth→L2 (anti-sunward from L2) (CORRECT)")
    else:
        print("    ✗ X does NOT point from Earth→L2")
        print(f"      Instead, alignment is: {np.dot(x_hat, earth_to_l2_hat):.10f}")
    
    # Check the Sun-Earth-L2 geometry
    print("\n[9] SUN-EARTH-L2 GEOMETRY CHECK:")
    angle_sun_earth_l2 = np.arccos(np.dot(sun_to_earth_hat, sun_to_l2_hat)) * 180/np.pi
    print(f"    Angle between Sun→Earth and Sun→L2: {angle_sun_earth_l2:.6f}°")
    print(f"    (Should be ~0° for collinear L2)")
    
    # Check ICRF coordinates
    print("\n[10] ICRF COORDINATE ANALYSIS:")
    print(f"     Sun is at:   [{r_sun[0]/1e6:.1f}, {r_sun[1]/1e6:.1f}, {r_sun[2]/1e6:.1f}] million km")
    print(f"     Earth is at: [{r_earth[0]:.1f}, {r_earth[1]:.1f}, {r_earth[2]:.1f}] km")
    print(f"     L2 is at:    [{r_l2[0]/1e6:.1f}, {r_l2[1]/1e6:.1f}, {r_l2[2]/1e6:.1f}] million km")
    
    # The critical issue: Check if Sun is on -X or +X side in ICRF
    print("\n[11] ICRF COORDINATE SYSTEM:")
    print("     In Earth-centered ICRF:")
    print(f"     - Sun has NEGATIVE X component: {r_sun[0] < 0}")
    print(f"     - This means Sun is in the -X direction from Earth")
    print(f"     - Anti-sunward (L2 direction) should be in +X direction")
    print(f"     - But L2 has X component: {r_l2[0]}")
    
    return x_hat, y_hat, z_hat, r_sun, r_earth, r_l2


def check_transformation_with_test_point():
    """Check transformation with a known test point."""
    
    print("\n" + "=" * 80)
    print("TRANSFORMATION TEST WITH KNOWN POINT")
    print("=" * 80)
    
    # Setup
    r_sun = np.array([-149597870.7, -2571258.7, 0.0])
    r_earth = np.array([0.0, 0.0, 0.0])
    v_earth = np.array([0.0, 0.0, 0.0])
    
    r_l2 = trans.compute_l2_position_approximate(r_sun, r_earth)
    
    # Test point: A satellite at L2 + 1 million km in anti-sunward direction
    # In ICRF, anti-sunward from L2 means further in the direction of r_l2
    earth_to_l2 = r_l2 - r_earth
    direction_anti_sun = earth_to_l2 / np.linalg.norm(earth_to_l2)
    
    r_test_icrf = r_l2 + 1e6 * direction_anti_sun  # 1 million km from L2, anti-sunward
    
    print(f"\n[1] Test point (ICRF): {r_test_icrf}")
    print(f"    This is L2 + 1 million km in anti-sunward direction")
    
    # Transform
    r_test_sem = trans.transform_position_to_sem_l2(r_test_icrf, r_sun, r_earth, v_earth)
    
    print(f"\n[2] Test point (SEM-L2): {r_test_sem}")
    print(f"    Expected: [~1000000, 0, 0] (positive X, on anti-Sun axis)")
    print(f"    Actual X component: {r_test_sem[0]:.2f}")
    print(f"    Actual Y component: {r_test_sem[1]:.2f}")
    print(f"    Actual Z component: {r_test_sem[2]:.2f}")
    
    if r_test_sem[0] > 0:
        print("\n    ✓ X is positive (correct - anti-sunward)")
    else:
        print("\n    ✗ X is negative (wrong - towards Sun)")
    
    # Another test: Point towards Sun from L2
    r_test2_icrf = r_l2 - 1e6 * direction_anti_sun  # Towards Sun from L2
    r_test2_sem = trans.transform_position_to_sem_l2(r_test2_icrf, r_sun, r_earth, v_earth)
    
    print(f"\n[3] Test point 2 (towards Sun from L2):")
    print(f"    ICRF: {r_test2_icrf}")
    print(f"    SEM-L2: {r_test2_sem}")
    print(f"    Expected: [~-1000000, 0, 0] (negative X)")
    
    # Test: Earth position
    r_earth_sem = trans.transform_position_to_sem_l2(r_earth, r_sun, r_earth, v_earth)
    print(f"\n[4] Earth position in SEM-L2: {r_earth_sem}")
    print(f"    Expected: negative X (towards Sun from L2)")
    print(f"    Distance: {np.linalg.norm(r_earth_sem):.2f} km")
    
    # Test: Sun position
    r_sun_sem = trans.transform_position_to_sem_l2(r_sun, r_sun, r_earth, v_earth)
    print(f"\n[5] Sun position in SEM-L2: {r_sun_sem}")
    print(f"    Expected: very negative X (far towards Sun from L2)")
    print(f"    Distance: {np.linalg.norm(r_sun_sem):.2f} km")


def visualize_frame_orientation():
    """Create a simple 2D diagram showing the frame orientation."""
    
    print("\n" + "=" * 80)
    print("CREATING FRAME ORIENTATION DIAGRAM")
    print("=" * 80)
    
    # Setup
    r_sun = np.array([-149597870.7, -2571258.7, 0.0])
    r_earth = np.array([0.0, 0.0, 0.0])
    v_earth = np.array([0.0, 0.0, 0.0])
    
    r_l2 = trans.compute_l2_position_approximate(r_sun, r_earth)
    x_hat, y_hat, z_hat, R = trans.build_sem_l2_axes(r_sun, r_earth, v_earth)
    
    # Create 2D plot in XY plane
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Scale for visibility (in millions of km)
    scale = 1e6
    
    # Plot positions
    ax.scatter(r_sun[0]/scale, r_sun[1]/scale, s=500, c='yellow', 
               edgecolors='orange', linewidths=2, marker='o', label='Sun', zorder=5)
    ax.scatter(r_earth[0]/scale, r_earth[1]/scale, s=200, c='blue', 
               marker='o', label='Earth', zorder=5)
    ax.scatter(r_l2[0]/scale, r_l2[1]/scale, s=300, c='purple', 
               marker='*', label='L2', zorder=5)
    
    # Draw line from Sun to Earth to L2
    ax.plot([r_sun[0]/scale, r_earth[0]/scale, r_l2[0]/scale],
            [r_sun[1]/scale, r_earth[1]/scale, r_l2[1]/scale],
            'k--', linewidth=1, alpha=0.5, label='Sun-Earth-L2 line')
    
    # Draw SEM-L2 axes at L2 position
    axis_length = 30  # million km
    
    # X axis (red)
    ax.arrow(r_l2[0]/scale, r_l2[1]/scale, 
             x_hat[0]*axis_length, x_hat[1]*axis_length,
             head_width=2, head_length=3, fc='red', ec='red', linewidth=2,
             label='SEM-L2 +X (anti-Sun)', zorder=4)
    
    # Y axis (green)
    ax.arrow(r_l2[0]/scale, r_l2[1]/scale,
             y_hat[0]*axis_length, y_hat[1]*axis_length,
             head_width=2, head_length=3, fc='green', ec='green', linewidth=2,
             label='SEM-L2 +Y', zorder=4)
    
    # Draw ICRF axes at Earth
    icrf_length = 30
    ax.arrow(0, 0, icrf_length, 0,
             head_width=1.5, head_length=2, fc='pink', ec='pink', 
             linewidth=1.5, alpha=0.7, label='ICRF +X', zorder=3)
    ax.arrow(0, 0, 0, icrf_length,
             head_width=1.5, head_length=2, fc='lightgreen', ec='lightgreen',
             linewidth=1.5, alpha=0.7, label='ICRF +Y', zorder=3)
    
    ax.set_xlabel('X (million km) - ICRF', fontsize=12)
    ax.set_ylabel('Y (million km) - ICRF', fontsize=12)
    ax.set_title('SEM-L2 Frame Orientation in ICRF Coordinates', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=10)
    ax.axis('equal')
    
    # Save
    plots_dir = Path(__file__).parent / "plots"
    plots_dir.mkdir(exist_ok=True)
    save_path = plots_dir / "frame_orientation_diagnostic.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\nFrame orientation diagram saved to: {save_path}")
    
    plt.show()


def main():
    """Run all diagnostic tests."""
    
    # Analyze frame definition
    x_hat, y_hat, z_hat, r_sun, r_earth, r_l2 = analyze_frame_definition()
    
    # Check transformation
    check_transformation_with_test_point()
    
    # Visualize
    visualize_frame_orientation()
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 80)
    print("\nPossible issues to investigate:")
    print("1. Frame axis definition (X should point anti-sunward from L2)")
    print("2. Sign conventions (anti-Sun vs towards-Sun)")
    print("3. ICRF coordinate system orientation")
    print("4. Rotation matrix construction")
    print("5. Sun ephemeris approximation accuracy")
    print("\nPlease review the diagnostic output above to identify the problem.")
    print("=" * 80)


if __name__ == "__main__":
    main()
