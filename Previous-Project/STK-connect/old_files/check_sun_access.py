"""
Check what celestial objects are available in STK and how to access Sun position.
"""

import win32com.client

def check_stk_celestial_objects():
    """Check what celestial bodies are available in STK."""
    
    print("="*80)
    print("CHECKING STK CELESTIAL OBJECTS")
    print("="*80)
    
    # Connect to STK
    print("\nConnecting to STK...")
    uiApp = win32com.client.Dispatch("STK13.Application")
    root = uiApp.Personality2
    scenario = root.CurrentScenario
    
    # Set time format
    root.UnitPreferences.Item('DateFormat').SetCurrentUnit('EpSec')
    
    print(f"Connected to scenario: {scenario.InstanceName}")
    
    # Try different ways to access Sun
    print("\n" + "="*80)
    print("ATTEMPTING TO ACCESS SUN")
    print("="*80)
    
    # Method 1: Try as Star
    print("\n[1] Trying: Star/Sun")
    try:
        sun = root.GetObjectFromPath("Star/Sun")
        print(f"    ✓ SUCCESS! Found Sun as Star")
        print(f"    Type: {sun.ClassName}")
        return root, scenario, sun, "Star/Sun"
    except Exception as e:
        print(f"    ✗ Failed: {str(e)[:100]}")
    
    # Method 2: Try as Planet
    print("\n[2] Trying: Planet/Sun")
    try:
        sun = root.GetObjectFromPath("Planet/Sun")
        print(f"    ✓ SUCCESS! Found Sun as Planet")
        print(f"    Type: {sun.ClassName}")
        return root, scenario, sun, "Planet/Sun"
    except Exception as e:
        print(f"    ✗ Failed: {str(e)[:100]}")
    
    # Method 3: Try as CentralBody
    print("\n[3] Trying: CentralBody/Sun")
    try:
        sun = root.GetObjectFromPath("CentralBody/Sun")
        print(f"    ✓ SUCCESS! Found Sun as CentralBody")
        print(f"    Type: {sun.ClassName}")
        return root, scenario, sun, "CentralBody/Sun"
    except Exception as e:
        print(f"    ✗ Failed: {str(e)[:100]}")
    
    # Method 4: List all children to see what's available
    print("\n[4] Listing all scenario children:")
    try:
        children = scenario.Children
        print(f"    Found {children.Count} children:")
        for i in range(children.Count):
            child = children.Item(i)
            print(f"      - {child.ClassName}: {child.InstanceName}")
    except Exception as e:
        print(f"    ✗ Failed to list children: {e}")
    
    # Method 5: Try to access via VGT (Vector Geometry Tool)
    print("\n[5] Trying to access Sun via VGT:")
    try:
        # Get Earth central body
        earth = root.GetObjectFromPath("CentralBody/Earth")
        print(f"    Found Earth: {earth.ClassName}")
        
        # Try to get Sun vector from Earth
        print("    Attempting to get Sun vector from Earth...")
        vgt = earth.Vgt
        print(f"    VGT accessed")
        
        # List available vectors
        vectors = vgt.Vectors
        print(f"    Available vectors: {vectors.Count}")
        
        # Try to find Sun-related vector
        for i in range(min(10, vectors.Count)):  # Check first 10
            try:
                vec = vectors.Item(i)
                name = vec.Name if hasattr(vec, 'Name') else str(i)
                print(f"      Vector {i}: {name}")
            except:
                pass
                
    except Exception as e:
        print(f"    ✗ Failed: {str(e)[:100]}")
    
    print("\n" + "="*80)
    print("Sun not found via standard object paths.")
    print("We may need to use STK's built-in Sun vector or ephemeris.")
    print("="*80)
    
    return root, scenario, None, None


def try_sun_vector_from_earth(root, scenario):
    """Try to get Sun vector using VGT from Earth."""
    
    print("\n" + "="*80)
    print("TRYING TO GET SUN VECTOR VIA VGT")
    print("="*80)
    
    try:
        # Get Earth
        earth = root.GetObjectFromPath("CentralBody/Earth")
        
        # Create a point for Sun using VGT
        print("\n[1] Creating Sun point via VGT System...")
        
        # Try using ICRF axes
        print("    Attempting to access Sun through coordinate systems...")
        
        # Get a satellite to test with
        jwst = root.GetObjectFromPath("Satellite/JWST")
        
        # Try to get Sun data through satellite's data providers
        print("\n[2] Checking JWST data providers for Sun-related data...")
        
        providers = jwst.DataProviders
        print(f"    Found {providers.Count} data providers")
        
        # List some providers
        for i in range(min(20, providers.Count)):
            try:
                provider = providers.Item(i)
                print(f"      Provider {i}: {provider.Name}")
                
                # Check if it's lighting or Sun-related
                if 'sun' in provider.Name.lower() or 'solar' in provider.Name.lower() or 'lighting' in provider.Name.lower():
                    print(f"        *** FOUND SUN-RELATED: {provider.Name}")
            except Exception as e:
                pass
        
        # Try using SPICE for Sun position
        print("\n[3] Attempting to use STK's internal Sun ephemeris...")
        
        # STK uses SPICE internally - try to access it
        # Get scenario analysis interval
        start_time = scenario.StartTime
        stop_time = scenario.StopTime
        
        print(f"    Scenario time: {start_time} to {stop_time}")
        
        # Try to create a custom vector pointing to Sun
        print("\n[4] Trying to create custom Sun vector...")
        
        # This might work - create a vector from Earth to Sun using SPICE body
        try:
            # Access VGT vector factory
            vgt_root = root.Vgt
            print("    Accessed root VGT")
            
            # Try to create a vector
            # This is STK-specific and may require specific SPICE kernel
            
        except Exception as e:
            print(f"    Failed: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def try_solar_data_provider(root, scenario):
    """Try to get Sun position via solar-related data providers."""
    
    print("\n" + "="*80)
    print("TRYING SOLAR DATA PROVIDERS")
    print("="*80)
    
    try:
        jwst = root.GetObjectFromPath("Satellite/JWST")
        
        # Try "Lighting" data provider
        print("\n[1] Trying Lighting data provider...")
        try:
            lighting = jwst.DataProviders.GetDataPrvTimeVarFromPath("Lighting")
            
            # Execute for first point
            result = lighting.ExecSingle(0)  # At t=0
            
            print(f"    ✓ Got lighting data!")
            print(f"    Available datasets: {result.DataSets.Count}")
            
            for i in range(result.DataSets.Count):
                dataset = result.DataSets.Item(i)
                print(f"      Dataset {i}: {dataset.Name}")
                
        except Exception as e:
            print(f"    ✗ Failed: {str(e)[:100]}")
        
        # Try "Solar Intensity" 
        print("\n[2] Trying Solar Intensity data provider...")
        try:
            solar = jwst.DataProviders.GetDataPrvTimeVarFromPath("Solar Intensity")
            result = solar.ExecSingle(0)
            print(f"    ✓ Got solar intensity data!")
        except Exception as e:
            print(f"    ✗ Failed: {str(e)[:100]}")
        
        # Try Vectors - Sun vector
        print("\n[3] Trying Vectors/Sun...")
        try:
            sun_vec = jwst.DataProviders.GetDataPrvTimeVarFromPath("Vectors/Sun")
            result = sun_vec.Exec(scenario.StartTime, scenario.StopTime, 3600)
            
            print(f"    ✓ SUCCESS! Got Sun vector data!")
            print(f"    Datasets: {result.DataSets.Count}")
            
            for i in range(result.DataSets.Count):
                dataset = result.DataSets.Item(i)
                print(f"      Dataset {i}: {dataset.Name}")
            
            return sun_vec
            
        except Exception as e:
            print(f"    ✗ Failed: {str(e)[:100]}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    return None


def main():
    """Run all checks."""
    
    # Check celestial objects
    root, scenario, sun_obj, sun_path = check_stk_celestial_objects()
    
    # If Sun object found, try to get data
    if sun_obj:
        print("\n" + "="*80)
        print("TESTING SUN DATA RETRIEVAL")
        print("="*80)
        
        try:
            # Try to get position data
            print("\nAttempting to get Cartesian Position...")
            pos_provider = sun_obj.DataProviders.Item("Cartesian Position")
            print(f"✓ Found position data provider")
            
            # Try ICRF frame
            icrf_provider = pos_provider.Group.Item("ICRF")
            print(f"✓ Found ICRF frame")
            
            # Execute
            result = icrf_provider.Exec(scenario.StartTime, scenario.StopTime, 86400)
            print(f"✓ Retrieved Sun position data!")
            
            # Get values
            times = result.DataSets.GetDataSetByName("Time").GetValues()
            x = result.DataSets.GetDataSetByName("x").GetValues()
            y = result.DataSets.GetDataSetByName("y").GetValues()
            z = result.DataSets.GetDataSetByName("z").GetValues()
            
            print(f"\nSun position at t=0:")
            print(f"  X: {x[0]} km")
            print(f"  Y: {y[0]} km")
            print(f"  Z: {z[0]} km")
            
        except Exception as e:
            print(f"✗ Failed to get Sun data: {e}")
            import traceback
            traceback.print_exc()
    else:
        # Try alternative methods
        try_sun_vector_from_earth(root, scenario)
        
        # Try solar data providers
        sun_vec = try_solar_data_provider(root, scenario)
        
        if sun_vec:
            print("\n" + "="*80)
            print("SUCCESS: Found way to access Sun data!")
            print("Use: Vectors/Sun data provider from satellite")
            print("="*80)
    
    print("\n" + "="*80)
    print("DIAGNOSTIC COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
