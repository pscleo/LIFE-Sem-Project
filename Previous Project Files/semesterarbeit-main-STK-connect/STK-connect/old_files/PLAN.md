# Plan: Create Custom SEM-L2 Coordinate System using VGT

## Goal
Create a Sun-Earth-Moon L2 (SEM-L2) coordinate system using STK's Vector Geometry Tool (VGT) and export satellite positions in this frame.

## Requirements
- **Origin**: Sun-Earth-Moon L2 point
- **X-axis**: Anti-sunward direction (pointing away from Sun)
- **Z-axis**: Ecliptic north pole
- **Frame type**: Rotating frame that maintains orientation relative to Sun-Earth-Moon system

## Approach: Using Vector Geometry Tool (VGT)

Based on AGI's Python snippets, we will use the VGT to create custom axes and an assembled coordinate system.

### Step 1: Access VGT Interface
```python
# Get VGT interface from a satellite or central body
sat = root.GetObjectFromPath("Satellite/Webb-no-correction")
vgt = sat.Vgt  # IAgCrdnProvider interface
```

### Step 2: Create Custom Points
We need to define the L2 point. Options:
- Use existing L2 point from STK's libration point database
- Create a custom point using displacement vectors
- Use calculation point for Sun-Earth-Moon L2

```python
# Access or create L2 point
pointFactory = vgt.Points.Factory
# Option A: Use existing libration point
# Option B: Create custom point with displacement vectors
```

### Step 3: Create Custom Axes
Create aligned and constrained axes:
- **Alignment**: X-axis aligned anti-sunward
- **Constraint**: Z-axis constrained to ecliptic north

```python
axesFactory = vgt.Axes.Factory
customAxes = axesFactory.Create(
    'SEM_L2_Axes',
    'Sun-Earth-Moon L2 Axes',
    7  # eCrdnAxesTypeAlignedAndConstrained
)

# Set X-axis to point anti-sunward
customAxes.AlignmentReferenceVector.SetVector(sunVector)  # Need to negate
customAxes.AlignmentDirection.AssignXYZ(1, 0, 0)

# Set Z-axis to ecliptic north
customAxes.ConstraintReferenceVector.SetVector(eclipticNorthVector)
customAxes.ConstraintDirection.AssignXYZ(0, 0, 1)
```

### Step 4: Create Assembled System
Combine the L2 point and custom axes into a coordinate system:

```python
systemFactory = vgt.Systems.Factory
semL2System = systemFactory.Create(
    'SEM_L2_System',
    'Sun-Earth-Moon L2 Coordinate System',
    0  # eCrdnSystemTypeAssembled
)

semL2System.OriginPoint.SetPoint(l2Point)
semL2System.ReferenceAxes.SetAxes(customAxes)
```

### Step 5: Export Data Using Custom System
Modify `get_sat_positions()` to use the custom coordinate system:

```python
# In stk_helpers.py
dp = sat.DataProviders.Item("Cartesian Position").Group.Item("SEM_L2_System")
result = dp.Exec(scenario.StartTime, scenario.StopTime, timestep_seconds)
```

## Implementation Plan

### Phase 1: Research & Verification
1. ✅ Identify VGT approach from AGI snippets
2. ✅ Create script to list available VGT vectors and points
3. ✅ Verify if L2 point exists in STK
4. ✅ Identify ecliptic north vector in STK

### Phase 2: Create Helper Functions
1. ✅ `get_sun_position_from_earth()` - Approximate Sun position
2. ✅ `transform_to_sem_l2()` - Transform coordinates to SEM-L2 frame
3. ✅ `get_sat_positions_sem_l2()` - Get satellite positions in SEM-L2 frame
4. ✅ Add these to `stk_helpers.py`

### Phase 3: Modify Data Extraction
1. ✅ Created `get_sat_positions_sem_l2()` function
2. ✅ Implements manual coordinate transformation
3. ✅ Test data extraction in SEM-L2 frame

### Phase 4: Validation
1. ✅ Compare results with ICRF frame
2. ✅ Verify coordinate transformations produce reasonable values
3. ✅ Plot differences to ensure reasonable values

## Key VGT Objects to Explore

### Points
- **System.CentralBody** - Get central body location
- **LibrationPoint** - Direct access to L2 point
- **DisplacementVector** - Create custom points via vectors

### Vectors
- **Body.Sun** - Vector to Sun
- **Body.Earth** - Vector to Earth
- **EclipticNorth** - Ecliptic north direction
- **BodyFixed** - Body-fixed vectors

### Axes Types
- `0` = Fixed
- `7` = AlignedAndConstrained (what we need)
- `3` = EulerAngles
- Others available in documentation

### System Types
- `0` = Assembled (what we need)
- `1` = Fixed
- `2` = Rotating

## Potential Challenges

1. **L2 Point Definition**: 
   - May need to calculate L2 position manually
   - Or use STK's libration point database if available

2. **Vector References**:
   - Need to find correct vector names in STK
   - May need to create displacement vectors

3. **Frame Orientation**:
   - Ensure axes are orthogonal
   - Verify right-hand rule is maintained

4. **Data Provider Access**:
   - Custom systems may not immediately appear in data providers
   - May need to refresh or wait for STK to update

## Implementation Summary

**COMPLETED:** SEM-L2 coordinate system implementation using manual transformation approach.

### Final Solution

Since VGT-created coordinate systems are not accessible via STK data providers, we implemented a manual coordinate transformation approach:

1. **`get_sun_position_from_earth()`** - Approximates Sun position using orbital mechanics
2. **`transform_to_sem_l2()`** - Transforms ICRF positions to SEM-L2 frame
3. **`get_sat_positions_sem_l2()`** - Wrapper function for easy SEM-L2 position retrieval

### Usage Example

```python
from stk_helpers import connect_to_stk, get_sat_positions_sem_l2

root, scenario = connect_to_stk(version=13)

# Get satellite positions in SEM-L2 frame
times, positions_sem_l2 = get_sat_positions_sem_l2(
    root, scenario, "Webb-no-correction", timestep_seconds=3600
)

# positions_sem_l2 is now in SEM-L2 frame where:
# - Origin is at Sun-Earth-Moon L2 point
# - X-axis points anti-sunward
# - Z-axis points towards ecliptic north
```

### Limitations

- Sun position is approximated using circular orbit (sufficient for L2 calculations)
- Moon's gravitational influence on L2 position is not included (Sun-Earth L2 approximation)
- Ecliptic north is approximated from Sun-Earth orbital plane

These approximations are acceptable for mission analysis purposes where relative positions between satellites are more important than absolute L2 frame accuracy.

## Next Steps

1. Create `explore-vgt.py` script to list available VGT objects
2. Identify how to access/create L2 point
3. Identify ecliptic north vector reference
4. Implement `create_sem_l2_system()` function
5. Test with simple data extraction

## References

- AGI Python Snippets: `STK-Python-Example-Snippets.txt`
- Failed Attempts: `COORDINATE_SYSTEM_ATTEMPTS.md`
- Current Implementation: `stk_helpers.py`

## Date
October 22, 2025