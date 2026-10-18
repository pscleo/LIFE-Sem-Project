"""
Check and list available time components and formats in STK13.

This script connects to STK and explores:
- Available time formats
- Time data providers
- Time conversion capabilities
- Scenario time settings
"""

import sys
import os

# Add Scripts folder to path to find pywin32 modules
scripts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'SA-venv', 'Scripts'))
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

import win32com.client
from datetime import datetime


def connect_to_stk():
    """Connect to running STK instance"""
    print("Connecting to STK 13...")
    try:
        uiApp = win32com.client.Dispatch("STK13.Application")
        uiApp.Visible = True
        root = uiApp.Personality2
        scenario = root.CurrentScenario
        print(f"✓ Connected to scenario: {scenario.InstanceName}\n")
        return root, scenario
    except Exception as e:
        print(f"✗ Failed to connect to STK: {e}")
        return None, None


def check_unit_preferences(root):
    """Check available time format units"""
    print("="*70)
    print("UNIT PREFERENCES - Time Formats")
    print("="*70)
    
    try:
        unit_prefs = root.UnitPreferences
        
        # Get available date format units
        print("\nAvailable Date Format Units:")
        print("-" * 50)
        
        # Common STK time format units to check
        time_formats = [
            "DateFormat",
            "TimeFormat", 
            "EpochFormat",
            "DurationFormat"
        ]
        
        for fmt in time_formats:
            try:
                current = unit_prefs.GetCurrentUnit(fmt)
                print(f"  {fmt:20s}: {current}")
                
                # Try to get available units for this format
                try:
                    available = unit_prefs.GetUnits(fmt)
                    print(f"    Available options: {', '.join(available)}")
                except:
                    pass
                    
            except Exception as e:
                print(f"  {fmt:20s}: Not available ({e})")
        
        print("\n" + "-" * 50)
        
    except Exception as e:
        print(f"✗ Error checking unit preferences: {e}")


def check_scenario_time_info(scenario):
    """Check scenario time settings and properties"""
    print("\n" + "="*70)
    print("SCENARIO TIME INFORMATION")
    print("="*70)
    
    try:
        print(f"\nScenario Name: {scenario.InstanceName}")
        print(f"Start Time: {scenario.StartTime}")
        print(f"Stop Time:  {scenario.StopTime}")
        
        # Try to get scenario epoch
        try:
            print(f"Epoch:      {scenario.Epoch}")
        except:
            print("Epoch:      Not available")
        
        # Calculate duration
        try:
            start = float(scenario.StartTime)
            stop = float(scenario.StopTime)
            duration_sec = stop - start
            duration_days = duration_sec / 86400
            print(f"\nDuration:")
            print(f"  {duration_sec:,.0f} seconds")
            print(f"  {duration_days:,.2f} days")
        except:
            print("\nDuration: Could not calculate")
            
    except Exception as e:
        print(f"✗ Error checking scenario time info: {e}")


def check_time_data_providers(root, scenario):
    """Check available time-related data providers for a satellite"""
    print("\n" + "="*70)
    print("TIME DATA PROVIDERS")
    print("="*70)
    
    try:
        # Get first satellite in scenario
        satellites = root.CurrentScenario.Children.GetElements(18)  # 18 = eSatellite
        
        if satellites.Count == 0:
            print("\n✗ No satellites found in scenario")
            return
        
        sat = satellites.Item(0)
        print(f"\nChecking data providers for: {sat.InstanceName}")
        print("-" * 50)
        
        # Get data providers
        dp = sat.DataProviders
        print(f"\nTotal Data Providers: {dp.Count}")
        
        # List all data providers
        print("\nAll Available Data Providers:")
        for i in range(dp.Count):
            provider = dp.Item(i)
            print(f"  [{i:3d}] {provider.Name}")
        
        # Check for time-specific providers
        print("\nTime-Related Data Providers:")
        time_keywords = ['time', 'epoch', 'date', 'duration', 'calendar']
        
        for i in range(dp.Count):
            provider = dp.Item(i)
            name_lower = provider.Name.lower()
            if any(kw in name_lower for kw in time_keywords):
                print(f"  • {provider.Name}")
                
                # Try to get more info about this provider
                try:
                    if hasattr(provider, 'Group'):
                        group = provider.Group
                        print(f"    Has {group.Count} group items")
                        for j in range(min(5, group.Count)):
                            print(f"      - {group.Item(j).Name}")
                except:
                    pass
        
    except Exception as e:
        print(f"✗ Error checking data providers: {e}")


def check_time_conversion(root, scenario):
    """Check time conversion capabilities"""
    print("\n" + "="*70)
    print("TIME CONVERSION")
    print("="*70)
    
    try:
        # Get a sample time from scenario
        start_time = scenario.StartTime
        print(f"\nScenario Start Time: {start_time}")
        
        # Try different time format conversions
        print("\nAttempting Time Format Conversions:")
        print("-" * 50)
        
        # Save current format
        try:
            current_format = root.UnitPreferences.GetCurrentUnit("DateFormat")
            print(f"Current format: {current_format}")
        except:
            current_format = None
        
        # Try different formats
        test_formats = [
            "EpSec",
            "UTCG", 
            "ISO-YD",
            "EpMin",
            "EpHr",
            "EpDay"
        ]
        
        for fmt in test_formats:
            try:
                root.UnitPreferences.SetCurrentUnit("DateFormat", fmt)
                converted = scenario.StartTime
                print(f"  {fmt:15s}: {converted}")
            except Exception as e:
                print(f"  {fmt:15s}: Failed ({e})")
        
        # Restore original format
        if current_format:
            try:
                root.UnitPreferences.SetCurrentUnit("DateFormat", current_format)
                print(f"\n✓ Restored original format: {current_format}")
            except:
                pass
                
    except Exception as e:
        print(f"✗ Error checking time conversion: {e}")


def check_epoch_info(root, scenario):
    """Check epoch and reference time information"""
    print("\n" + "="*70)
    print("EPOCH & REFERENCE TIME")
    print("="*70)
    
    try:
        # Try to get epoch information
        print("\nSTK Epoch Information:")
        print("-" * 50)
        
        # J2000 epoch
        print("Standard Epochs:")
        print("  J2000:  2000 Jan 01 12:00:00.000 UTC")
        print("  Unix:   1970 Jan 01 00:00:00.000 UTC")
        
        # Try to get scenario epoch
        try:
            # Set to UTCG to get readable format
            root.UnitPreferences.SetCurrentUnit("DateFormat", "UTCG")
            epoch_readable = scenario.StartTime
            
            # Set to EpSec to get numeric value
            root.UnitPreferences.SetCurrentUnit("DateFormat", "EpSec")
            epoch_numeric = float(scenario.StartTime)
            
            print(f"\nScenario Epoch:")
            print(f"  Readable: {epoch_readable}")
            print(f"  Seconds:  {epoch_numeric:,.1f} sec")
            print(f"  Days:     {epoch_numeric/86400:,.3f} days")
            
        except Exception as e:
            print(f"\n✗ Could not determine scenario epoch: {e}")
            
    except Exception as e:
        print(f"✗ Error checking epoch info: {e}")


def main():
    """Main function to check all time components"""
    print("\n" + "="*70)
    print("STK13 TIME COMPONENTS CHECK")
    print("="*70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Connect to STK
    root, scenario = connect_to_stk()
    if not root or not scenario:
        return
    
    # Run all checks
    check_unit_preferences(root)
    check_scenario_time_info(scenario)
    check_epoch_info(root, scenario)
    check_time_conversion(root, scenario)
    check_time_data_providers(root, scenario)
    
    print("\n" + "="*70)
    print("CHECK COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()