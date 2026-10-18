# Coordinate System Creation Attempts in STK 13

## Goal
Create a custom Sun-Earth-Moon L2 (SEM-L2) coordinate system in STK 13 via Python automation.

## Requirements
- Center: Sun-Earth-Moon L2 point
- X-axis: Anti-sunward direction
- Z-axis: Ecliptic north pole

## Failed Attempts

### Attempt 1: Connect Commands - CoordSystem
```python
root.ExecuteCommand(f'CoordSystem */CoordinateSystem Add {cs_name}')
root.ExecuteCommand(f'CoordSystem */CoordinateSystem/{cs_name} SetType Fixed')
root.ExecuteCommand(f'CoordSystem */CoordinateSystem/{cs_name} SetOriginCentralBody Sun')
```
**Result**: `Exception occurred. Command has failed.` (Error: -2147220988)

### Attempt 2: New Command - Various Syntaxes
```python
# Syntax 1
root.ExecuteCommand(f'New / CoordinateSystem {cs_name}')

# Syntax 2
root.ExecuteCommand(f'New / */CoordinateSystem {cs_name}')
```
**Result**: `Exception occurred. Command has failed.` (Error: -2147220988)

### Attempt 3: Object Model - Children.New()
```python
cs = root.CurrentScenario.Children.New(18, cs_name)  # 18 = eCoordinateSystem
cs.Type = 0  # 0 = eCoordSystemTypeFixed
```
**Result**: Object was created, but `Property 'New.Type' can not be set.`
- The coordinate system object is created in STK
- Properties cannot be set after creation
- Object exists but cannot be configured

### Attempt 4: CalculationTool Command
```python
# Syntax 1
cmd = f'CalculationTool {scenario_path} CoordinateSystemTool Add "{cs_name}" "Sun" "Fixed"'
root.ExecuteCommand(cmd)

# Syntax 2
cmd = f'CalculationTool {scenario_path} CoordinateSystemTool Create "{cs_name}"'
root.ExecuteCommand(cmd)
```
**Result**: Both syntaxes failed with command execution errors

## Current Status
- **Manual creation in STK GUI**: No obvious GUI option in STK 13
- **Programmatic creation**: All attempted methods have failed
- **Workaround**: May need to use existing coordinate systems or create via STK scenario file modification

## Possible Next Steps (Not Yet Attempted)
1. Check if coordinate systems can be defined in the scenario file (.sc) directly
2. Contact AGI support for proper STK 13 syntax
3. Use alternative approach: compute coordinate transformations in Python instead of relying on STK
4. Check if there's a pre-existing libration point coordinate system in STK

## Notes
- STK 13 may have changed the coordinate system creation API compared to older versions
- The object model partially works (can create object) but doesn't allow property setting
- Data providers can only access pre-existing coordinate systems
- Custom coordinate systems may need to be created through a different workflow in STK 13

## Date
October 22, 2025