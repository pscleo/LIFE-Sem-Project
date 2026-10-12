"""
Simple script to check STK connection and display scenario time information.
"""
import win32com.client
from datetime import datetime

print("=" * 60)
print("STK CONNECTION AND SCENARIO INFO CHECK")
print("=" * 60)

try:
    # Connect to STK
    print("\n1. Connecting to STK...")
    uiApp = win32com.client.Dispatch("STK13.Application")
    print("   ✓ Connected to STK 13")
    
    # Get root and scenario
    print("\n2. Getting STK objects...")
    root = uiApp.Personality2
    print("   ✓ Got root object")
    
    scenario = root.CurrentScenario
    print(f"   ✓ Got current scenario: {scenario.InstanceName}")
    
    # Get scenario times
    print("\n3. Scenario Time Information:")
    print("   " + "-" * 56)
    
    start_time = scenario.StartTime
    stop_time = scenario.StopTime
    
    print(f"   Raw Start Time: {start_time}")
    print(f"   Raw Stop Time:  {stop_time}")
    
    # Try to parse the times
    print("\n4. Parsed Times:")
    print("   " + "-" * 56)
    
    try:
        # Try standard format: "7 Apr 2022 12:00:00.000"
        start_dt = datetime.strptime(start_time.split('.')[0], "%d %b %Y %H:%M:%S")
        stop_dt = datetime.strptime(stop_time.split('.')[0], "%d %b %Y %H:%M:%S")
        
        print(f"   Start: {start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Stop:  {stop_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        duration = stop_dt - start_dt
        print(f"\n   Duration: {duration.days} days, {duration.seconds // 3600} hours")
        
    except Exception as e:
        print(f"   ✗ Could not parse times: {e}")
        print(f"   Try different parsing format")
    
    # Get scenario epoch (if available)
    print("\n5. Additional Info:")
    print("   " + "-" * 56)
    try:
        epoch = scenario.Epoch
        print(f"   Epoch: {epoch}")
    except:
        print(f"   Epoch: Not available")
    
    # Get animation time
    try:
        anim_start = scenario.Animation.StartTime
        anim_stop = scenario.Animation.StopTime
        print(f"   Animation Start: {anim_start}")
        print(f"   Animation Stop:  {anim_stop}")
    except:
        print(f"   Animation times: Not available")
    
    print("\n" + "=" * 60)
    print("CONNECTION TEST SUCCESSFUL")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    print("\nMake sure:")
    print("  1. STK 13 is running")
    print("  2. A scenario is open")
    print("=" * 60)