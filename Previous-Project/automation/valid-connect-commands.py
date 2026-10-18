stkRoot.ExecuteCommand(f'VO * SetVectorGeometry Modify "CentralBody/Earth Inertial Axes" Show On') # Show Earth Inertial Axes
stkRoot.ExecuteCommand(f'VO * SetVectorGeometry Modify "CentralBody/Earth L2 Axes" Show On') # Show Earth L2 Axes
stkRoot.ExecuteCommand(f'VO * SetVectorGeometry Modify "CentralBody/Earth Sun Vector" Show On') # Show Earth-Sun Vector
Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Maneuver.Results Inclination Eccentricity # Set up control parameters for target sequence for Maneuver
Astrogator */Satellite/Base SetValue MainSequence.SegmentList.Target_Sequence.SegmentList.Prop_to_XZ_1.Results Vx # Set up result to XZ crossing propagate segment



# Common STK Color Values (BGR format: 0x00BBGGRR)
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


# Attach to running instance of STK
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