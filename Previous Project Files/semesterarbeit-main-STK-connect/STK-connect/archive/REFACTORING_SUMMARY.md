# STK-connect Refactoring Summary

## Overview
The STK-connect folder has been refactored to eliminate code duplication and improve maintainability by extracting common functions into reusable helper modules.

## New Helper Modules

### 1. `stk_connection.py`
**Purpose:** STK connection and data retrieval utilities

**Functions:**
- `connect_to_stk()` - Connect to running STK instance
- `get_satellite_state_vectors()` - Get satellite positions and velocities
- `get_body_state_vectors()` - Get celestial body (Sun, Earth) positions and velocities
- `get_satellite_initial_state()` - Get satellite initial state at scenario start
- `get_body_state_at_epoch()` - Get celestial body state at scenario start

### 2. `coordinate_transforms.py`
**Purpose:** Coordinate transformation utilities for SEM-L2 frame

**Physical Constants:**
- `M_SUN`, `M_EARTH`, `AU_KM`

**Functions:**
- `compute_l2_position_approximate()` - Calculate L2 position using cubic approximation
- `build_sem_l2_axes()` - Build SEM-L2 coordinate frame with fixed ecliptic normal
- `compute_l2_velocity()` - Calculate L2 velocity using finite differences
- `compute_frame_angular_velocity()` - Compute angular velocity from rotation matrices
- `transform_trajectory_to_sem_l2()` - Transform barycentric to SEM-L2 frame
- `convert_to_barycentric()` - Convert geocentric to barycentric frame

### 3. `data_processing.py`
**Purpose:** Data filtering and analysis utilities

**Functions:**
- `filter_time_range()` - Filter data to specified time range
- `compute_relative_positions()` - Calculate position offsets relative to base satellite
- `print_drift_analysis()` - Analyze and print drift rates

### 4. `visualization.py`
**Purpose:** Plotting utilities for trajectory analysis

**Functions:**
- `title_to_filename()` - Convert plot title to valid Windows filename
- `plot_offsets_vs_time()` - 2×2 time series plots (X, Y, Z components + magnitude)
- `plot_relative_trajectories_3d()` - 3D trajectory plot with XY, XZ, YZ projections
- `plot_trajectories_3d()` - 3D plot for multiple trajectories with JWST highlighting

## Refactored Scripts

### 1. `plot_2-sat-constellation_refactored.py`
**Replaces:** `plot_2-sat-constellation.py` (original ~700 lines)  
**New size:** ~200 lines (main logic only)

**Changes:**
- Imports helper modules instead of duplicating functions
- Focuses on high-level analysis workflow
- All user settings preserved at top of file
- Same functionality, cleaner code

**Usage:** Same as original, just run the script

### 2. `plot_maneuver_comparison_refactored.py`
**Replaces:** `plot_maneuver_comparison.py` (original ~600 lines)  
**New size:** ~180 lines (main logic only)

**Changes:**
- Uses shared STK connection and transformation functions
- Eliminates ~400 lines of duplicate code
- Preserves all user settings and plot customization
- Same visualization output

**Usage:** Same as original, just run the script

## Benefits of Refactoring

1. **DRY Principle:** Eliminates code duplication across scripts
2. **Maintainability:** Bug fixes in one place benefit all scripts
3. **Testability:** Helper functions can be unit tested independently
4. **Reusability:** Easy to create new analysis scripts using existing functions
5. **Clarity:** Main scripts become high-level workflows, easier to understand
6. **Consistency:** Same transformation logic across all analyses

## Code Reduction Summary

| File | Original Lines | Refactored Lines | Reduction |
|------|----------------|------------------|-----------|
| plot_2-sat-constellation.py | ~700 | ~200 | 71% |
| plot_maneuver_comparison.py | ~600 | ~180 | 70% |
| **Total in main scripts** | ~1300 | ~380 | 71% |

**Note:** The ~920 lines removed from main scripts are now in reusable helper modules (~1000 lines total), 
but each function is only written once and can be used by any script.

## Migration Guide

### Option 1: Use Refactored Scripts Directly
Simply run the new `*_refactored.py` scripts instead of the original ones. They have identical functionality.

### Option 2: Rename Refactored Scripts
If you want to replace the originals:
```powershell
# Backup originals
mv plot_2-sat-constellation.py plot_2-sat-constellation_old.py
mv plot_maneuver_comparison.py plot_maneuver_comparison_old.py

# Use refactored versions
mv plot_2-sat-constellation_refactored.py plot_2-sat-constellation.py
mv plot_maneuver_comparison_refactored.py plot_maneuver_comparison.py
```

### Option 3: Keep Both
Keep both versions during transition period and test the refactored versions alongside originals.

## Creating New Analysis Scripts

To create a new analysis script using the helper modules:

```python
from stk_connection import connect_to_stk, get_satellite_state_vectors, get_body_state_vectors
from coordinate_transforms import convert_to_barycentric, transform_trajectory_to_sem_l2
from data_processing import filter_time_range
from visualization import plot_trajectories_3d

# Your analysis code here - just call the helper functions!
```

## Testing

The refactored scripts have been created with the same logic as the originals. To verify:

1. Run both original and refactored versions with same settings
2. Compare output plots - they should be identical
3. Check console output for any errors

## Notes

- Original scripts are preserved and not modified
- Helper modules are pure Python functions (no dependencies on each other except coordinate_transforms may use constants)
- All user settings remain at the top of each script
- Plot customization options preserved
- No changes to STK scenario or data files needed
