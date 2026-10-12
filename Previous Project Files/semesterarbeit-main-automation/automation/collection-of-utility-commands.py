"""
================================================================================
UTILITY COMMANDS & CODE SNIPPETS - INTERACTIVE REFERENCE
================================================================================

Module: collection-of-utility-commands.py
Status: Reference/scratch file (copy-paste snippets as needed)

PURPOSE
-------
Centralized collection of frequently-used STK commands and Python code patterns.
Designed for copy-paste use in Jupyter notebooks, REPL, or debugging sessions.
NOT meant to be run as a standalone script.
Used mainly to reconnect to STK, after having to restart the jupyter kernel
while running the octahedron constellation simulations.

CONTENTS
--------
1. Visualization commands (axes, vectors, colors)
2. Astrogator MCS execution loops
3. STK color definitions (BGR format)
4. STK attachment/connection code
5. Scenario setup and epoch calculations

VISUALIZATION COMMANDS
----------------------
Show/hide Earth frames and Sun vectors:
  - Earth Inertial Axes
  - Earth L2 Axes
  - Earth-Sun Vector

Astrogator result configuration examples for maneuver and propagation segments.

STK COLOR PALETTE
-----------------
Common colors in BGR format (0x00BBGGRR):
  Red, Green, Blue, Yellow, Cyan, Magenta, White, Black, Gray
  
Use: color_value = COLORS['Cyan']  # returns 16776960

COMMON PATTERNS
---------------
1. Attach to running STK instance (for interactive work)
2. Configure scenario time bounds
3. Set up epoch calculations
4. Loop through constellation configs for MCS execution

USAGE EXAMPLES
--------------
Copy relevant sections into:
  - Jupyter notebooks (for interactive development)
  - Python REPL (for quick testing)
  - octahedron-constellation.py (for permanent integration)
  - Interactive jupyter session



NOTES
-----
- All commands tested with STK 13+
- Some commands require active STK scenario
- Modify as needed for your specific setup

WHEN TO USE
-----------
✓ Developing new features in interactive environment
✓ Debugging specific STK operations
✓ Quick reference for common patterns
✓ Testing command syntax before integration
✗ Running as standalone script (use octahedron-constellation.py instead)
✗ Production workflows (integrate tested snippets into main scripts)

================================================================================
"""

# Visualization commands to show Earth axes and Sun vector
'''
stkRoot.ExecuteCommand(f'VO * SetVectorGeometry Modify "CentralBody/Earth Inertial Axes" Show On') # Show Earth Inertial Axes
stkRoot.ExecuteCommand(f'VO * SetVectorGeometry Modify "CentralBody/Earth L2 Axes" Show On') # Show Earth L2 Axes
stkRoot.ExecuteCommand(f'VO * SetVectorGeometry Modify "CentralBody/Earth Sun Vector" Show On') # Show Earth-Sun Vector
Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Maneuver.Results Inclination Eccentricity # Set up control parameters for target sequence for Maneuver
Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_1.Results Vx # Set up result to XZ crossing propagate segment
'''


# Common STK Color Values (BGR format: 0x00BBGGRR)
# Used to set satellite colors
COLORS = {
    'Red': 255,           # 0x000000FF
    'Green': 65280,       # 0x0000FF00
    'Blue': 16711680,     # 0x00FF0000
    'Yellow': 65535,      # 0x0000FFFF
    'Cyan': 16776960,     # 0x00FFFF00
    'Magenta': 16711935,  # 0x00FF00FF
    'White': 16777215,    # 0x00FFFFFF
    'Black': 0,           # 0x00000000
    'Gray': 8421504,      # 0x00808080
}

# Run (parts of) the MCS for each constellation configuration
# For manual use in an interactive terminal
for config in CONSTELLATION_CONFIGS:
    print(f'\n--- Running MCS for {config["base_name"]} ---')
    
    for sat_name in config['satellite_names']:
        print(f'Running MCS for {sat_name}...')
        try:
            # stkRoot.ExecuteCommand(f'Astrogator */Satellite/{sat_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Action Run active profiles')
            stkRoot.ExecuteCommand(f'Astrogator */Satellite/{sat_name} SetValue MainSequence.SegmentList.Sequence.SegmentList.Target_Sequence.Action Run nominal sequence')
            stkRoot.ExecuteCommand(f'Astrogator */Satellite/{sat_name} RunMCS')
            print(f'  ✓ {sat_name} MCS completed successfully')
        except Exception as e:
            print(f'  ✗ {sat_name} MCS failed: {str(e)}')

###################################################################################
# Attach to running instance of STK
# (copy-paste the entire remainder into running jupyter instace after kernel restart)
# assumes the imports from octahedron-constellation.py are already done
###################################################################################
stk = STKDesktop.AttachToApplication()
stkRoot = stk.Root
scenario = stkRoot.CurrentScenario
# reset dimensions to default
dimensions = stkRoot.UnitPreferences
dimensions.ResetUnits()
dimensions.SetCurrentUnit("DateFormat", "UTCG")
dimensions.SetCurrentUnit("DistanceUnit", "km")

# Set scenario time bounds (JWST launch was 25 Dec 2021)
startTime = '26 Dec 2021 00:00:00.000'
stopTime = '26 Dec 2025 00:00:00.000'
epoch = '25 Dec 2021 00:00:00.000'
scenario.StartTime = startTime
scenario.StopTime = stopTime
scenario.Epoch = epoch
set_current_time(stkRoot, scenario, '26 Dec 2021 00:00:00.000')

base_separation_epoch = "6 Oct 2022 07:00:00.000 UTCG"

constellation_separation_epoch = epoch_seconds_to_time_string(
    scenario, 
    time_string_to_epoch_seconds(scenario, base_separation_epoch) + 10 * 60
)