import win32com.client
import sys

print("Testing STK connection...")

for version in [13, 12, 11, 10]:
    try:
        print(f"\nTrying STK {version}...")
        app = win32com.client.Dispatch(f"STK{version}.Application")
        print(f"✓ STK {version} is running and accessible")
        
        # Try to get root and scenario to verify full access
        try:
            root = app.Personality2
            scenario = root.CurrentScenario
            print(f"  Scenario: {scenario.InstanceName}")
            print(f"  Start Time: {scenario.StartTime}")
            print(f"  Stop Time: {scenario.StopTime}")
            sys.exit(0)
        except Exception as e:
            print(f"  Scenario access failed: {e}")
        
    except Exception as e:
        print(f"✗ STK {version} not available: {e}")

print("\nNo running STK instance found!")