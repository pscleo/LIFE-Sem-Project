"""
List all available coordinate systems in STK for a satellite.
"""
from stk_helpers import connect_to_stk

print("DEBUG01: Starting script - listing coordinate systems")

# --- Connect to STK ---
root, scenario = connect_to_stk(version=13)

# --- Get a satellite object ---
sat_name = "Webb-no-correction"  # Use one of your satellites
print(f"DEBUG01: Using satellite: {sat_name}")

try:
    sat = root.GetObjectFromPath(f"Satellite/{sat_name}")
    print(f"DEBUG01: Satellite object retrieved: {sat_name}")
except Exception as e:
    print(f"DEBUG01: Failed to get satellite {sat_name}: {e}")
    raise

# --- Function to list coordinate systems ---
def list_coordinate_systems(sat, label=""):
    """List all available coordinate systems for a satellite."""
    try:
        cart_pos = sat.DataProviders.Item("Cartesian Position")
        coord_group = cart_pos.Group
        count = coord_group.Count
        
        print("\n" + "="*60)
        print(f"AVAILABLE COORDINATE SYSTEMS {label}")
        print("="*60)
        print(f"Total count: {count}")
        print("-"*60)
        
        # List all available coordinate systems
        for i in range(count):
            coord_system = coord_group.Item(i)
            print(f"{i+1}. {coord_system.Name}")
        
        print("="*60)
        return count
        
    except Exception as e:
        print(f"DEBUG01: Failed to access coordinate systems: {e}")
        raise

# --- List all available coordinate systems ---
count = list_coordinate_systems(sat)

print(f"\nDEBUG01: Found {count} available coordinate systems")
print("DEBUG01: Script completed")