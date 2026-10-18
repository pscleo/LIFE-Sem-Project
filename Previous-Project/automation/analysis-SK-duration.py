%matplotlib tk

# %% Analysis of Octahedron Constellations - Delta V Summary
import pandas as pd
from pathlib import Path
from collections import defaultdict
import re
import numpy as np
import matplotlib.pyplot as plt

# Get the path to the maneuver summaries directory
current_dir = Path(__file__).resolve().parent
summaries_dir = current_dir / "data-export" / "maneuver-summaries"

# Global plot dimensions configuration
scaler = 0.75
PLOT_DIM_SINGLE = (15 * scaler, 7 * scaler)      # Single plot (Delta V vs SK)
PLOT_DIM_4SUBPLOT = (15 * scaler, 12 * scaler)   # 2x2 subplot grid (Max deviations)
PLOT_DIM_TIMESERIES = (15 * scaler, 8 * scaler) # 4x1 subplot grid (Deviations over time)

def parse_sk_interval(sk_string):
    """
    Parse SK interval string and return numeric value and unit.
    
    Handles formats:
    - SK1d, SK7d, SK14d, etc. (days)
    - SK12h, SK6h, etc. (hours)
    
    Parameters:
    -----------
    sk_string : str
        SK interval string (e.g., "SK7d", "SK12h")
    
    Returns:
    --------
    tuple : (numeric_value_in_hours, original_string)
        numeric_value_in_hours: float value for sorting (hours)
        original_string: str for display
    """
    match = re.match(r'SK(\d+(?:[\.p]\d+)?)(d|h)', sk_string)
    if not match:
        raise ValueError(f"Invalid SK format: {sk_string}")
    
    value = float(match.group(1).replace('p', '.'))
    unit = match.group(2)
    
    # Convert to hours for consistent sorting
    if unit == 'd':
        value_in_hours = value * 24
    else:  # 'h'
        value_in_hours = value
    
    return value_in_hours, sk_string

def calculate_delta_v_from_data(csv_file_path):
    """
    Calculate Delta V by summing all maneuver Delta V values from the data section.
    
    Parameters:
    -----------
    csv_file_path : Path
        Path to the CSV file
    
    Returns:
    --------
    delta_v : float
        Sum of all Delta V values
    num_maneuvers : int
        Number of maneuvers
    """
    # Read the file and find where the actual data starts
    with open(csv_file_path, 'r') as f:
        lines = f.readlines()
    
    # Find the line with actual data header (the one after "--- BEGIN DATA ---")
    data_start_idx = None
    for i, line in enumerate(lines):
        if '--- BEGIN DATA ---' in line:
            data_start_idx = i + 1
            break
    
    if data_start_idx is None:
        raise ValueError("Could not find '--- BEGIN DATA ---' marker in file")
    
    # Read CSV starting from the actual data header
    df = pd.read_csv(csv_file_path, skiprows=data_start_idx)
    
    # Sum the Delta V column
    delta_v_sum = df['Delta V (m/sec)'].sum()
    num_maneuvers = len(df)
    
    return delta_v_sum, num_maneuvers

def extract_delta_v_from_header(csv_file_path):
    """
    Extract Total Delta V from the CSV header statistics section.
    """
    with open(csv_file_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        if 'Total Delta V (m/sec)' in line:
            parts = line.strip().split(',')
            if len(parts) >= 2:
                try:
                    return float(parts[1])
                except ValueError:
                    return None
    return None

def analyze_octahedron_constellations():
    """
    Analyze all Octahedron constellation CSV files and compare calculated vs header Delta V.
    Supports both SK{days}d and SK{hours}h formats.
    """
    # Group files by constellation (SK interval)
    constellations = defaultdict(list)
    sk_display = {}  # Store display format for each SK interval
    
    # Find all Octahedron CSV files
    csv_files = list(summaries_dir.glob("Octahedron_*.csv"))
    
    if not csv_files:
        print(f"No Octahedron CSV files found in {summaries_dir}")
        return
    
    # Group by SK interval (extract SK{X}d or SK{X}h after "Octahedron_")
    for csv_file in csv_files:
        filename = csv_file.stem
        # Extract SK interval: "Octahedron_SK7d_Xm_1000m" -> "SK7d"
        parts = filename.split('_')
        if len(parts) < 2:
            continue
        
        sk_string = parts[1]  # e.g., "SK7d" or "SK12h"
        
        try:
            sk_hours, sk_display_str = parse_sk_interval(sk_string)
            constellations[sk_hours].append(csv_file)
            sk_display[sk_hours] = sk_display_str
        except ValueError as e:
            print(f"Warning: {e} in file {filename}, skipping...")
            continue
    
    # Sort SK intervals numerically (by hours)
    sk_hours_list = sorted(constellations.keys())
    
    print(f'\n{"="*100}')
    print(f'OCTAHEDRON CONSTELLATION DELTA V ANALYSIS')
    print(f'{"="*100}\n')
    
    summary_data = []
    
    for sk_hours in sk_hours_list:
        csv_files = sorted(constellations[sk_hours])
        sk_string = sk_display[sk_hours]
        
        print(f'--- SK Interval: {sk_string} ---')
        print(f'Number of satellites: {len(csv_files)}\n')
        
        total_delta_v_calculated = 0.0
        total_delta_v_header = 0.0
        constellation_maneuvers = 0
        validation_passed = True
        
        # Process each satellite
        for csv_file in csv_files:
            sat_name = csv_file.stem
            
            # Extract values from header
            delta_v_header = extract_delta_v_from_header(csv_file)
            
            # Calculate from data
            try:
                delta_v_calc, num_maneuvers = calculate_delta_v_from_data(csv_file)
                constellation_maneuvers += num_maneuvers
            except Exception as e:
                print(f'  ✗ {sat_name}: Error reading data - {str(e)}')
                validation_passed = False
                continue
            
            # Compare
            if delta_v_header is not None:
                diff = abs(delta_v_calc - delta_v_header)
                match = '✓' if diff < 1e-6 else '✗'
                
                print(f'  {match} {sat_name}')
                print(f'      Header: {delta_v_header:.10f} m/sec')
                print(f'      Calced: {delta_v_calc:.10f} m/sec')
                
                if diff >= 1e-6:
                    print(f'      Diff:   {diff:.10e} m/sec')
                    validation_passed = False
                
                total_delta_v_header += delta_v_header
                total_delta_v_calculated += delta_v_calc
            else:
                print(f'  ✗ {sat_name}: Could not extract header value')
                validation_passed = False
        
        # Print constellation summary
        print(f'\n  Constellation Total ({sk_string}):')
        print(f'    Total Calculated Delta V: {total_delta_v_calculated:.10f} m/sec')
        print(f'    Total Header Delta V:     {total_delta_v_header:.10f} m/sec')
        print(f'    Total Maneuvers:          {constellation_maneuvers}')
        print(f'    Validation:               {"PASSED ✓" if validation_passed else "FAILED ✗"}')
        
        summary_data.append({
            'SK Interval': sk_string,
            'Num Satellites': len(csv_files),
            'Total Maneuvers': constellation_maneuvers,
            'Delta V (m/sec)': total_delta_v_calculated,
            'Validation': 'PASSED' if validation_passed else 'FAILED'
        })
        
        print()
    
    # Print final summary table
    print(f'{"="*100}')
    print(f'SUMMARY TABLE')
    print(f'{"="*100}\n')
    
    summary_df = pd.DataFrame(summary_data)
    print(summary_df.to_string(index=False))
    
    print(f'\n{"="*100}')
    print(f'Analysis complete!')

# %% Run analysis
if __name__ == '__main__':
    analyze_octahedron_constellations()

# %% Plot Delta V vs SK Duration for Octahedron Constellations
import pandas as pd
from pathlib import Path
from collections import defaultdict
import re
import matplotlib.pyplot as plt
import numpy as np

# Get the path to the maneuver summaries directory
current_dir = Path(__file__).resolve().parent
summaries_dir = current_dir / "data-export" / "maneuver-summaries"

def extract_satellite_info(filename):
    """
    Extract SK interval and satellite direction from filename.
    
    Example: "Octahedron_SK7d_Xm1000m" -> ("SK7d", "X", "minus")
    """
    parts = filename.split('_')
    if len(parts) < 3:
        return None, None, None
    
    sk_string = parts[1]  # e.g., "SK7d"
    direction_part = parts[2]  # e.g., "Xm1000m"
    
    # Extract axis (X, Y, Z) and sign (p for plus, m for minus)
    match = re.match(r'([XYZ])([pm])', direction_part)
    if not match:
        return None, None, None
    
    axis = match.group(1)
    sign = 'plus' if match.group(2) == 'p' else 'minus'
    
    return sk_string, axis, sign


def plot_delta_v_vs_sk_duration(exclude_names=None, y_log=True, x_axis_days=False):
    """
    Plot total Delta V vs SK duration for all satellites.
    Uses 3 colors for X, Y, Z axes and light/dark shades for plus/minus.
    
    Parameters:
    -----------
    exclude_names : list, optional
        List of satellite name patterns to exclude from the plot.
        Matches against satellite filenames using substring matching (case-insensitive).
        Examples:
            ['SK3h']              - Exclude all satellites with 'SK3h' in filename
            ['Xm']                - Exclude all Xm satellites
            ['SK1h', 'SK3h']      - Exclude SK1h or SK3h satellites
        If None, all satellites are plotted. (default: None)
    y_log : bool, optional
        Use logarithmic scale for y-axis (Delta V). (default: True)
    x_axis_days : bool, optional
        If True, show x-axis in days. If False, show in hours. (default: False)
    """
    # Find all Octahedron CSV files
    csv_files = list(summaries_dir.glob("Octahedron_*.csv"))
    
    if not csv_files:
        print(f"No Octahedron CSV files found in {summaries_dir}")
        return
    
    # Initialize exclude list
    if exclude_names is None:
        exclude_names = []
    
    # Convert exclude list to uppercase for consistency
    exclude_names = [name.upper() for name in exclude_names]
    
    # Collect data organized by satellite
    satellite_data = defaultdict(lambda: {
        'sk_hours': [],
        'sk_display': [],
        'delta_v': [],
        'filenames': []  # Store filenames for filtering
    })
    
    # Process each file
    for csv_file in csv_files:
        filename = csv_file.stem
        sk_string, axis, sign = extract_satellite_info(filename)
        
        if sk_string is None:
            continue
        
        # Parse SK interval
        try:
            sk_hours, sk_display = parse_sk_interval(sk_string)
        except ValueError:
            continue
        
        # Extract Delta V
        delta_v = extract_delta_v_from_header(csv_file)
        if delta_v is None:
            continue
        
        # Create satellite key
        sat_key = f"{axis}{sign[0].upper()}"  # e.g., "XM", "YP", etc.
        
        satellite_data[sat_key]['sk_hours'].append(sk_hours)
        satellite_data[sat_key]['sk_display'].append(sk_display)
        satellite_data[sat_key]['delta_v'].append(delta_v)
        satellite_data[sat_key]['filenames'].append(filename)
    
    # Sort each satellite's data by SK hours
    for sat_key in satellite_data:
        indices = np.argsort(satellite_data[sat_key]['sk_hours'])
        satellite_data[sat_key]['sk_hours'] = np.array(satellite_data[sat_key]['sk_hours'])[indices]
        satellite_data[sat_key]['sk_display'] = np.array(satellite_data[sat_key]['sk_display'])[indices]
        satellite_data[sat_key]['delta_v'] = np.array(satellite_data[sat_key]['delta_v'])[indices]
        satellite_data[sat_key]['filenames'] = np.array(satellite_data[sat_key]['filenames'])[indices]
    
    # Filter satellite data by name patterns
    filtered_satellites = {}
    excluded_names_list = []
    
    for sat_key, data in satellite_data.items():
        filenames = data.get('filenames', [])
        
        # Keep only filenames that don't match any exclusion pattern
        filtered_indices = []
        
        for i, filename in enumerate(filenames):
            should_exclude = False
            
            for pattern in exclude_names:
                if pattern in filename.upper():
                    should_exclude = True
                    excluded_names_list.append(filename)
                    break
            
            if not should_exclude:
                filtered_indices.append(i)
        
        # Only include satellite type if it still has data points after filtering
        if filtered_indices:
            filtered_data = {}
            for key in data:
                if key == 'filenames':
                    filtered_data[key] = np.array(data[key])[filtered_indices]
                else:
                    filtered_data[key] = np.array(data[key])[filtered_indices]
            
            filtered_satellites[sat_key] = filtered_data
    
    if not filtered_satellites:
        print("No satellites to plot after applying exclusions")
        return
    
    # Print excluded satellites info
    if excluded_names_list:
        print(f"Excluding satellite patterns: {', '.join(exclude_names)}")
        print(f"Excluded satellites:")
        for name in sorted(set(excluded_names_list)):
            print(f"  - {name}")
        print()
    
    # Define colors: X=blue, Y=green, Z=red
    # Light for plus, dark for minus
    colors = {
        'XP': '#4DA6FF',  # Light blue
        'XM': '#0033CC',  # Dark blue
        'YP': '#66FF66',  # Light green
        'YM': '#006600',  # Dark green
        'ZP': '#FF6666',  # Light red
        'ZM': '#CC0000',  # Dark red
    }
    
    # Create figure
    fig, ax = plt.subplots(figsize=PLOT_DIM_SINGLE)
    
    # Collect all unique SK intervals for x-axis labels
    all_sk_displays = []
    all_sk_hours = []
    for sat_key in filtered_satellites.keys():
        all_sk_displays.extend(filtered_satellites[sat_key]['sk_display'].tolist())
        all_sk_hours.extend(filtered_satellites[sat_key]['sk_hours'].tolist())
    
    # Get unique SK intervals (preserving order)
    unique_sk_pairs = list(dict.fromkeys(zip(all_sk_hours, all_sk_displays)))
    unique_sk_hours_sorted = sorted(unique_sk_pairs, key=lambda x: x[0])
    
    # Prepare x-axis data and labels
    if x_axis_days:
        x_plot_data = np.array([sk_hours / 24.0 for sk_hours, _ in unique_sk_hours_sorted])
        x_label = 'Station Keeping Interval'
    else:
        x_plot_data = np.array([sk_hours for sk_hours, _ in unique_sk_hours_sorted])
        x_label = 'Station Keeping Interval'
    
    # Remove "SK" prefix from labels, keep only the time value
    x_tick_labels = [sk_display.replace('SK', '') for _, sk_display in unique_sk_hours_sorted]
    
    # Plot each satellite (only non-excluded ones)
    for sat_key in sorted(filtered_satellites.keys()):
        data = filtered_satellites[sat_key]
        color = colors.get(sat_key, '#000000')
        
        # Convert x-axis data if needed
        if x_axis_days:
            x_data = np.array(data['sk_hours']) / 24.0
        else:
            x_data = np.array(data['sk_hours'])
        
        ax.plot(x_data, data['delta_v'] * 1000,  # Convert to mm/s for better scale
                marker='o', label=sat_key, color=color, linewidth=2, markersize=8)
    
    # Formatting
    ax.set_xlabel(x_label, fontsize=12, fontweight='bold')
    ax.set_ylabel('Total Delta V (mm/s/orbit)', fontsize=12, fontweight='bold')
    ax.set_title('Delta V Required vs Station Keeping Duration', 
                 fontsize=14, fontweight='bold')
    
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(ncol=2, loc='best', fontsize=10, framealpha=0.9)
    
    # Set x-axis to log scale and use custom tick labels
    ax.set_xscale('log')
    ax.set_xticks(x_plot_data)
    ax.set_xticklabels(x_tick_labels, ha='center')
    
    # Set y-axis scale based on parameter
    if y_log:
        ax.set_yscale('log')
    
    plt.tight_layout()
    
    # Save figure
    plots_dir = current_dir / "results"
    plots_dir.mkdir(exist_ok=True)
    
    # Add scale and exclusion info to filename if applicable
    filename = "delta_v_vs_sk_duration"
    if x_axis_days:
        filename += "_xdays"
    if y_log:
        filename += "_ylog"
    if excluded_names_list:
        exclude_suffix = "_exclude_" + "_".join([name.split('_')[1] for name in excluded_names_list]).lower()
        filename += exclude_suffix
    filename += ".png"
    
    fig.savefig(plots_dir / filename, dpi=600, bbox_inches='tight')
    print(f"Plot saved to: {plots_dir / filename}")
    
    plt.show()

def extract_offset_from_filename(filename):
    """
    Extract the intended offset from the filename.
    
    Example: "Octahedron_SK7d_Xp1000m" -> {'x': 1.0, 'y': 0.0, 'z': 0.0}
    """
    parts = filename.split('_')
    if len(parts) < 3:
        return None
    
    direction_part = parts[2]  # e.g., "Xp1000m"
    
    # Parse direction: Xp1000m, Xm1000m, etc.
    match = re.match(r'([XYZ])([pm])(\d+)m', direction_part)
    if not match:
        return None
    
    axis = match.group(1)
    sign = 1.0 if match.group(2) == 'p' else -1.0
    magnitude_m = float(match.group(3))
    
    # Convert meters to km
    magnitude_km = magnitude_m / 1000.0
    
    offset = {'x': 0.0, 'y': 0.0, 'z': 0.0}
    offset[axis.lower()] = sign * magnitude_km
    
    return offset


def shift_position_data_to_origin(csv_file_path, offset):
    """
    Shift position data to the origin of the satellite by subtracting the offset.
    Returns a dataframe with the shifted positions.
    
    Parameters:
    -----------
    csv_file_path : Path
        Path to the CSV position file
    offset : dict
        Dictionary with 'x', 'y', 'z' keys (in km)
    
    Returns:
    --------
    df_deviations : pd.DataFrame
        DataFrame with deviation columns
    """
    # Find the data start marker
    with open(csv_file_path, 'r') as f:
        lines = f.readlines()
    
    data_start_idx = None
    for i, line in enumerate(lines):
        if '--- BEGIN DATA ---' in line:
            data_start_idx = i + 1
            break
    
    if data_start_idx is None:
        raise ValueError("Could not find '--- BEGIN DATA ---' marker in file")
    
    # Read the CSV starting from the data section
    df = pd.read_csv(csv_file_path, skiprows=data_start_idx)
    
    # Create deviation columns by subtracting offset
    df_deviations = df.copy()
    df_deviations['x_deviation (km)'] = df['x (km)'] - offset['x']
    df_deviations['y_deviation (km)'] = df['y (km)'] - offset['y']
    df_deviations['z_deviation (km)'] = df['z (km)'] - offset['z']
    
    # Calculate magnitude of deviation
    df_deviations['magnitude_deviation (km)'] = np.sqrt(
        df_deviations['x_deviation (km)']**2 + 
        df_deviations['y_deviation (km)']**2 + 
        df_deviations['z_deviation (km)']**2
    )
    
    return df_deviations


def save_deviation_data(csv_file_path, df_deviations):
    """
    Save deviation data to a new CSV file with _deviations suffix.
    
    Parameters:
    -----------
    csv_file_path : Path
        Original CSV path
    df_deviations : pd.DataFrame
        DataFrame with deviation columns
    
    Returns:
    --------
    output_path : Path
        Path to the saved deviation file
    """
    csv_path = Path(csv_file_path)
    
    # Create deviations folder
    deviations_dir = csv_path.parent.parent / "deviations"
    deviations_dir.mkdir(parents=True, exist_ok=True)
    
    # Create new filename with _deviations suffix
    stem = csv_path.stem
    output_filename = f"{stem}_deviations.csv"
    output_path = deviations_dir / output_filename
    
    # Save CSV (without header rows, just data)
    df_deviations.to_csv(output_path, index=False)
    
    return output_path


def calculate_max_deviations():
    """
    Calculate maximum deviations for all position CSV files.
    
    Returns:
    --------
    dict : Dictionary organized by satellite with SK intervals and max deviations
    """
    current_dir = Path(__file__).resolve().parent
    positions_dir = current_dir / "data-export" / "positions"
    
    csv_files = list(positions_dir.glob("Octahedron_*.csv"))
    
    if not csv_files:
        print(f"No position CSV files found in {positions_dir}")
        return {}
    
    # Organize data by satellite
    satellite_data = defaultdict(lambda: {
        'full_names': [],  # Store full satellite names
        'sk_hours': [],
        'sk_display': [],
        'max_x_dev': [],
        'max_y_dev': [],
        'max_z_dev': [],
        'max_mag_dev': []
    })
    
    print(f'\n{"="*100}')
    print(f'CALCULATING POSITION DEVIATIONS')
    print(f'{"="*100}\n')
    
    for csv_file in sorted(csv_files):
        filename = csv_file.stem
        
        # Extract SK interval and satellite direction
        parts = filename.split('_')
        if len(parts) < 3:
            continue
        
        sk_string = parts[1]  # e.g., "SK7d"
        direction_part = parts[2]  # e.g., "Xp1000m"
        
        # Extract offset
        offset = extract_offset_from_filename(filename)
        if offset is None:
            print(f"  ✗ Could not parse offset from {filename}")
            continue
        
        # Parse SK interval
        try:
            sk_hours, sk_display = parse_sk_interval(sk_string)
        except ValueError as e:
            print(f"  ✗ {filename}: {e}")
            continue
        
        # Calculate deviations
        try:
            df_deviations = shift_position_data_to_origin(csv_file, offset)
            
            # Save deviation data
            output_path = save_deviation_data(csv_file, df_deviations)
            
            # Calculate maximum deviations
            max_x_dev = df_deviations['x_deviation (km)'].abs().max()
            max_y_dev = df_deviations['y_deviation (km)'].abs().max()
            max_z_dev = df_deviations['z_deviation (km)'].abs().max()
            max_mag_dev = df_deviations['magnitude_deviation (km)'].max()
            
            # Create satellite key (axis and direction)
            match = re.match(r'([XYZ])([pm])', direction_part)
            if match:
                axis = match.group(1)
                sign = 'P' if match.group(2) == 'p' else 'M'
                sat_key = f"{axis}{sign}"
                
                satellite_data[sat_key]['full_names'].append(filename)  # Store full name
                satellite_data[sat_key]['sk_hours'].append(sk_hours)
                satellite_data[sat_key]['sk_display'].append(sk_string)
                satellite_data[sat_key]['max_x_dev'].append(max_x_dev)
                satellite_data[sat_key]['max_y_dev'].append(max_y_dev)
                satellite_data[sat_key]['max_z_dev'].append(max_z_dev)
                satellite_data[sat_key]['max_mag_dev'].append(max_mag_dev)
                
                print(f"  ✓ {filename}")
                print(f"      Max deviations - X: {max_x_dev*1000:.3f}m, Y: {max_y_dev*1000:.3f}m, Z: {max_z_dev*1000:.3f}m, Mag: {max_mag_dev*1000:.3f}m")
                
        except Exception as e:
            print(f"  ✗ {filename}: Error processing - {str(e)}")
            continue
    
    # Sort each satellite's data by SK hours
    for sat_key in satellite_data:
        indices = np.argsort(satellite_data[sat_key]['sk_hours'])
        for key in ['full_names', 'sk_hours', 'sk_display', 'max_x_dev', 'max_y_dev', 'max_z_dev', 'max_mag_dev']:
            satellite_data[sat_key][key] = np.array(satellite_data[sat_key][key])[indices]
    
    return satellite_data


def plot_max_deviations(satellite_data, x_log=False, y_log=False, exclude_names=None):
    """
    Plot maximum deviations vs SK interval in 4 separate plots (X, Y, Z, Magnitude).
    
    Parameters:
    -----------
    satellite_data : dict
        Dictionary with deviation data organized by satellite
    x_log : bool, optional
        Use logarithmic scale for x-axis (SK interval) (default: False)
    y_log : bool, optional
        Use logarithmic scale for y-axis (deviation) (default: False)
    exclude_names : list, optional
        List of satellite name patterns to exclude from the plot.
        Matches against full satellite names using substring matching (case-insensitive).
        Examples:
            ['SK3d']              - Exclude all satellites with 'SK3d' in name
            ['Octahedron_SK1h_Ym1000m']  - Exclude specific satellite by full name
            ['SK3d', 'Ym']        - Exclude SK3d satellites OR Ym satellites
        If None, all satellites are plotted. (default: None)
    """
    if not satellite_data:
        print("No satellite data to plot")
        return
    
    # Initialize exclude list
    if exclude_names is None:
        exclude_names = []
    
    # Convert exclude list to uppercase for consistency
    exclude_names = [name.upper() for name in exclude_names]
    
    # Filter satellite data by name patterns
    filtered_satellites = {}
    excluded_names_list = []
    
    for sat_key, data in satellite_data.items():
        # Get full names for this satellite type
        full_names = data.get('full_names', [])
        
        # Keep only full names that don't match any exclusion pattern
        filtered_full_names = []
        
        for full_name in full_names:
            should_exclude_this = False
            
            for pattern in exclude_names:
                if pattern in full_name.upper():
                    should_exclude_this = True
                    excluded_names_list.append(full_name)
                    break
            
            if not should_exclude_this:
                filtered_full_names.append(full_name)
        
        # Only include satellite type if it still has data points after filtering
        if filtered_full_names:
            # Create a copy of data with filtered entries
            filtered_data = {}
            for key in data:
                if key == 'full_names':
                    filtered_data[key] = np.array(filtered_full_names)
                else:
                    # Get indices of kept satellites
                    indices = [i for i, name in enumerate(full_names) if name in filtered_full_names]
                    filtered_data[key] = np.array(data[key])[indices]
            
            filtered_satellites[sat_key] = filtered_data
    
    if not filtered_satellites:
        print("No satellites to plot after applying exclusions")
        return
    
    # Print excluded satellites info
    if excluded_names_list:
        print(f"Excluding satellite patterns: {', '.join(exclude_names)}")
        print(f"Excluded satellites:")
        for name in sorted(set(excluded_names_list)):
            print(f"  - {name}")
        print(f"Plotting remaining data points")
    
    # Define colors: X=blue, Y=green, Z=red
    colors = {
        'XP': '#4DA6FF',  # Light blue
        'XM': '#0033CC',  # Dark blue
        'YP': '#66FF66',  # Light green
        'YM': '#006600',  # Dark green
        'ZP': '#FF6666',  # Light red
        'ZM': '#CC0000',  # Dark red
    }
    
    # Create 4 subplots
    fig, axes = plt.subplots(2, 2, figsize=PLOT_DIM_4SUBPLOT)
    axes = axes.flatten()
    
    # Collect all unique SK intervals for custom x-axis labels
    all_sk_displays = []
    all_sk_hours = []
    for sat_key in filtered_satellites.keys():
        all_sk_displays.extend(filtered_satellites[sat_key]['sk_display'].tolist())
        all_sk_hours.extend(filtered_satellites[sat_key]['sk_hours'].tolist())
    
    # Get unique SK intervals (preserving order)
    unique_sk_pairs = list(dict.fromkeys(zip(all_sk_hours, all_sk_displays)))
    unique_sk_hours_sorted = sorted(unique_sk_pairs, key=lambda x: x[0])
    
    # Prepare x-axis data and labels in days
    x_plot_data = np.array([sk_hours / 24.0 for sk_hours, _ in unique_sk_hours_sorted])
    x_tick_labels = [sk_display.replace('SK', '') for _, sk_display in unique_sk_hours_sorted]
    
    plot_configs = [
        ('max_x_dev', 'X Deviation (m)', axes[0]),
        ('max_y_dev', 'Y Deviation (m)', axes[1]),
        ('max_z_dev', 'Z Deviation (m)', axes[2]),
        ('max_mag_dev', 'Magnitude Deviation (m)', axes[3])
    ]
    
    for data_key, ylabel, ax in plot_configs:
        # Plot each satellite (only non-excluded ones)
        for sat_key in sorted(filtered_satellites.keys()):
            data = filtered_satellites[sat_key]
            color = colors.get(sat_key, '#000000')
            
            # Convert SK hours to days
            sk_days = np.array(data['sk_hours']) / 24.0
            
            # Convert deviations to meters
            y_values = np.array(data[data_key]) * 1000
            
            ax.plot(sk_days, y_values,
                    marker='o', label=sat_key, color=color, linewidth=2, markersize=8)
        
        # Formatting
        ax.set_xlabel('Station Keeping Interval', fontsize=11, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(ncol=2, loc='best', fontsize=9, framealpha=0.9)
        
        # Set x-axis to log scale and use custom tick labels
        if x_log:
            ax.set_xscale('log')
            ax.set_xticks(x_plot_data)
            ax.set_xticklabels(x_tick_labels, ha='center')
        if y_log:
            ax.set_yscale('log')
    
    fig.suptitle('Maximum Position Deviations from Intended Offset\n(Octahedron Constellation)', 
                 fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    # Save figure
    current_dir = Path(__file__).resolve().parent
    plots_dir = current_dir / "results"
    plots_dir.mkdir(exist_ok=True)
    
    # Add scale info to filename
    scale_suffix = ""
    if x_log:
        scale_suffix += "_xlog"
    if y_log:
        scale_suffix += "_ylog"
    if excluded_names_list:
        exclude_suffix = "_exclude_" + "_".join([name.split('_')[1] for name in excluded_names_list]).lower()
        scale_suffix += exclude_suffix
    
    filename = f"position_deviations_vs_sk{scale_suffix}.png"
    fig.savefig(plots_dir / filename, dpi=600, bbox_inches='tight')
    print(f"Plot saved to: {plots_dir / filename}")
    
    plt.show()
def plot_deviations_over_time(satellite_name, sk_interval=None, x_axis_days=False):
    """
    Plot position deviations (X, Y, Z, and Magnitude) over time for a specified satellite.
    
    Parameters:
    -----------
    satellite_name : str
        Satellite name (e.g., "Octahedron_SK7d_Xp1000m")
    sk_interval : str, optional
        SK interval to filter (e.g., "SK7d"). If None, uses the satellite_name as-is.
        (default: None)
    x_axis_days : bool, optional
        If True, show x-axis in days.
        If False, show x-axis in hours from start. (default: False)
    
    Example:
    --------
    # Plot specific satellite with time in hours
    plot_deviations_over_time("Octahedron_SK7d_Xp1000m")
    
    # Plot with x-axis in days
    plot_deviations_over_time("Octahedron_SK7d_Xp1000m", x_axis_days=True)
    
    # Or search by SK interval and satellite type
    plot_deviations_over_time("Xp1000m", sk_interval="SK7d", x_axis_days=True)
    """
    # Enable interactive mode for zooming/panning
    plt.ion()
    
    current_dir = Path(__file__).resolve().parent
    deviations_dir = current_dir / "data-export" / "deviations"
    
    # Build the filename
    if sk_interval:
        # Search mode: construct filename from components
        deviation_filename = f"Octahedron_{sk_interval}_{satellite_name}_deviations.csv"
    else:
        # Direct mode: use satellite_name as full filename
        deviation_filename = f"{satellite_name}_deviations.csv"
    
    deviation_path = deviations_dir / deviation_filename
    
    if not deviation_path.exists():
        print(f"✗ File not found: {deviation_path}")
        print(f"\nAvailable files in {deviations_dir}:")
        available = list(deviations_dir.glob("*.csv"))
        for f in sorted(available)[:10]:  # Show first 10
            print(f"  - {f.name}")
        if len(available) > 10:
            print(f"  ... and {len(available) - 10} more")
        return
    
    # Read deviation data
    try:
        df = pd.read_csv(deviation_path)
    except Exception as e:
        print(f"✗ Error reading file: {str(e)}")
        return
    
    # Extract the satellite info from filename for title
    title_name = deviation_path.stem.replace('_deviations', '')
    
    # Create figure with 4 subplots
    fig, axes = plt.subplots(4, 1, figsize=PLOT_DIM_TIMESERIES)
    
    # Prepare x-axis data
    if x_axis_days:
        # Convert hours to days (using 10-minute time steps from export)
        time_step_hours = 10.0 / 60.0  # 10 minutes = 0.1667 hours
        x_axis_data = np.arange(len(df)) * time_step_hours / 24.0
        x_label = 'Time (days from start)'
    else:
        # Time in hours from start
        x_axis_data = np.arange(len(df))
        x_label = 'Time (hours from start)'
    
    # Plot configurations
    plot_configs = [
        ('x_deviation (km)', r'$\Delta x$ (m)', axes[0], '#4DA6FF'),
        ('y_deviation (km)', r'$\Delta y$ (m)', axes[1], '#66FF66'),
        ('z_deviation (km)', r'$\Delta z$ (m)', axes[2], '#FF6666'),
        ('magnitude_deviation (km)', r'Magnitude (m)', axes[3], '#FF9900')
    ]
    
    for col_name, ylabel, ax, color in plot_configs:
        if col_name not in df.columns:
            print(f"✗ Column '{col_name}' not found in CSV")
            continue
        
        # Convert to meters
        y_values = df[col_name] * 1000
        
        ax.plot(x_axis_data, y_values, color=color, linewidth=1.5, alpha=0.8)
        ax.fill_between(x_axis_data, y_values, alpha=0.2, color=color)
        
        # Add statistics
        max_dev = y_values.max()
        min_dev = y_values.min()
        mean_dev = y_values.mean()
        std_dev = y_values.std()
        
        ax.axhline(mean_dev, color='red', linestyle='--', linewidth=1, alpha=0.5, label=f'Mean: {mean_dev:.3f}m')
        ax.axhline(max_dev, color='darkgreen', linestyle=':', linewidth=1, alpha=0.5, label=f'Max: {max_dev:.3f}m')
        
        # Formatting
        ax.set_ylabel(ylabel, fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='upper right', fontsize=9)
        
        # Add statistics text box
        stats_text = f'Max: {max_dev:.3f}m\nMin: {min_dev:.3f}m\nMean: {mean_dev:.3f}m\nStd: {std_dev:.3f}m'
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    axes[-1].set_xlabel(x_label, fontsize=11, fontweight='bold')
    
    axis_type = 'Days' if x_axis_days else 'Hours'
    fig.suptitle(f'Position Deviations Over {axis_type}\n{title_name}', 
                 fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    # Save figure
    plots_dir = current_dir / "results"
    plots_dir.mkdir(exist_ok=True)
    
    axis_suffix = '_vs_days' if x_axis_days else '_vs_hours'
    filename = f"deviations{axis_suffix}_{title_name}.png"
    fig.savefig(plots_dir / filename, dpi=600, bbox_inches='tight')
    print(f"\n✓ Plot saved to: {plots_dir / filename}")
    
    # Print summary
    print(f"\nDeviation Summary for {title_name}:")
    for col_name, ylabel, ax, color in plot_configs:
        if col_name in df.columns:
            y_values = df[col_name] * 1000
            print(f"  {ylabel}:")
            print(f"    Max: {y_values.max():.3f}m, Min: {y_values.min():.3f}m, Mean: {y_values.mean():.3f}m")
    
    plt.show()

def plot_magnitude_deviations(satellite_data, x_log=False, y_log=False, exclude_names=None):
    """
    Plot maximum magnitude deviations vs SK interval.
    
    Parameters:
    -----------
    satellite_data : dict
        Dictionary with deviation data organized by satellite
    x_log : bool, optional
        Use logarithmic scale for x-axis (SK interval) (default: False)
    y_log : bool, optional
        Use logarithmic scale for y-axis (deviation) (default: False)
    exclude_names : list, optional
        List of satellite name patterns to exclude from the plot.
        Matches against full satellite names using substring matching (case-insensitive).
        Examples:
            ['SK3d']              - Exclude all satellites with 'SK3d' in name
            ['Octahedron_SK1h_Ym1000m']  - Exclude specific satellite by full name
            ['SK3d', 'Ym']        - Exclude SK3d satellites OR Ym satellites
        If None, all satellites are plotted. (default: None)
    """
    if not satellite_data:
        print("No satellite data to plot")
        return
    
    # Initialize exclude list
    if exclude_names is None:
        exclude_names = []
    
    # Convert exclude list to uppercase for consistency
    exclude_names = [name.upper() for name in exclude_names]
    
    # Filter satellite data by name patterns
    filtered_satellites = {}
    excluded_names_list = []
    
    for sat_key, data in satellite_data.items():
        # Get full names for this satellite type
        full_names = data.get('full_names', [])
        
        # Keep only full names that don't match any exclusion pattern
        filtered_full_names = []
        
        for full_name in full_names:
            should_exclude_this = False
            
            for pattern in exclude_names:
                if pattern in full_name.upper():
                    should_exclude_this = True
                    excluded_names_list.append(full_name)
                    break
            
            if not should_exclude_this:
                filtered_full_names.append(full_name)
        
        # Only include satellite type if it still has data points after filtering
        if filtered_full_names:
            # Create a copy of data with filtered entries
            filtered_data = {}
            for key in data:
                if key == 'full_names':
                    filtered_data[key] = np.array(filtered_full_names)
                else:
                    # Get indices of kept satellites
                    indices = [i for i, name in enumerate(full_names) if name in filtered_full_names]
                    filtered_data[key] = np.array(data[key])[indices]
            
            filtered_satellites[sat_key] = filtered_data
    
    if not filtered_satellites:
        print("No satellites to plot after applying exclusions")
        return
    
    # Print excluded satellites info
    if excluded_names_list:
        print(f"Excluding satellite patterns: {', '.join(exclude_names)}")
        print(f"Excluded satellites:")
        for name in sorted(set(excluded_names_list)):
            print(f"  - {name}")
        print(f"Plotting remaining data points")
    
    # Define colors: X=blue, Y=green, Z=red
    colors = {
        'XP': '#4DA6FF',  # Light blue
        'XM': '#0033CC',  # Dark blue
        'YP': '#66FF66',  # Light green
        'YM': '#006600',  # Dark green
        'ZP': '#FF6666',  # Light red
        'ZM': '#CC0000',  # Dark red
    }
    
    # Create single subplot for magnitude only
    fig, ax = plt.subplots(figsize=PLOT_DIM_SINGLE)
    
    # Collect all unique SK intervals for custom x-axis labels
    all_sk_displays = []
    all_sk_hours = []
    for sat_key in filtered_satellites.keys():
        all_sk_displays.extend(filtered_satellites[sat_key]['sk_display'].tolist())
        all_sk_hours.extend(filtered_satellites[sat_key]['sk_hours'].tolist())
    
    # Get unique SK intervals (preserving order)
    unique_sk_pairs = list(dict.fromkeys(zip(all_sk_hours, all_sk_displays)))
    unique_sk_hours_sorted = sorted(unique_sk_pairs, key=lambda x: x[0])
    
    # Prepare x-axis data and labels in days
    x_plot_data = np.array([sk_hours / 24.0 for sk_hours, _ in unique_sk_hours_sorted])
    x_tick_labels = [sk_display.replace('SK', '') for _, sk_display in unique_sk_hours_sorted]
    
    # Plot each satellite (only non-excluded ones)
    for sat_key in sorted(filtered_satellites.keys()):
        data = filtered_satellites[sat_key]
        color = colors.get(sat_key, '#000000')
        
        # Convert SK hours to days
        sk_days = np.array(data['sk_hours']) / 24.0
        
        # Convert deviations to meters
        y_values = np.array(data['max_mag_dev']) * 1000
        
        ax.plot(sk_days, y_values,
                marker='o', label=sat_key, color=color, linewidth=2, markersize=8)
    
    # Formatting
    ax.set_xlabel('Station Keeping Interval', fontsize=12, fontweight='bold')
    ax.set_ylabel(r'$\Delta r$ (m)', fontsize=12, fontweight='bold')
    ax.set_title('Maximum Magnitude Deviation from Intended Offset\n(Octahedron Constellation)', 
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(ncol=2, loc='best', fontsize=10, framealpha=0.9)
    
    # Set x-axis to log scale and use custom tick labels
    if x_log:
        ax.set_xscale('log')
        ax.set_xticks(x_plot_data)
        ax.set_xticklabels(x_tick_labels, ha='center')
    if y_log:
        ax.set_yscale('log')
    
    plt.tight_layout()
    
    # Save figure
    current_dir = Path(__file__).resolve().parent
    plots_dir = current_dir / "results"
    plots_dir.mkdir(exist_ok=True)
    
    # Add scale info to filename
    scale_suffix = ""
    if x_log:
        scale_suffix += "_xlog"
    if y_log:
        scale_suffix += "_ylog"
    if excluded_names_list:
        exclude_suffix = "_exclude_" + "_".join([name.split('_')[1] for name in excluded_names_list]).lower()
        scale_suffix += exclude_suffix
    
    filename = f"magnitude_deviation_vs_sk{scale_suffix}.png"
    fig.savefig(plots_dir / filename, dpi=600, bbox_inches='tight')
    print(f"Plot saved to: {plots_dir / filename}")
    
    plt.show()

def plot_delta_v_vs_max_deviation(satellite_data, delta_v_data=None, x_log=False, y_log=False, exclude_names=None):
    """
    Plot Delta V vs Maximum Magnitude Deviation, with different colors for each SK interval.
    Data points are averaged across satellites for each SK interval.
    
    Parameters:
    -----------
    satellite_data : dict
        Dictionary with deviation data organized by satellite (from calculate_max_deviations)
    delta_v_data : dict, optional
        Pre-calculated Delta V data. If None, will be calculated from CSV files. (default: None)
    x_log : bool, optional
        Use logarithmic scale for x-axis (deviation). (default: False)
    y_log : bool, optional
        Use logarithmic scale for y-axis (Delta V). (default: False)
    exclude_names : list, optional
        List of satellite name patterns to exclude from the plot.
        Matches against full satellite names using substring matching (case-insensitive).
        Examples:
            ['SK3d']              - Exclude all satellites with 'SK3d' in name
            ['SK3d', 'Ym']        - Exclude SK3d satellites OR Ym satellites
        If None, all satellites are plotted. (default: None)
    """
    if not satellite_data:
        print("No satellite data to plot")
        return
    
    # Initialize exclude list
    if exclude_names is None:
        exclude_names = []
    
    # Convert exclude list to uppercase for consistency
    exclude_names = [name.upper() for name in exclude_names]
    
    # If delta_v_data not provided, calculate it from CSV files
    if delta_v_data is None:
        delta_v_data = {}
        csv_files = list(summaries_dir.glob("Octahedron_*.csv"))
        
        for csv_file in csv_files:
            filename = csv_file.stem
            delta_v = extract_delta_v_from_header(csv_file)
            if delta_v is not None:
                delta_v_data[filename] = delta_v
    
    # Build a mapping of satellite to SK interval and Delta V
    sat_to_sk_and_dv = {}
    
    for sat_key, data in satellite_data.items():
        full_names = data.get('full_names', [])
        sk_displays = data.get('sk_display', [])
        max_mag_devs = data.get('max_mag_dev', [])
        
        for i, full_name in enumerate(full_names):
            # Check if should exclude
            should_exclude = False
            for pattern in exclude_names:
                if pattern in full_name.upper():
                    should_exclude = True
                    break
            
            if not should_exclude:
                sk_interval = sk_displays[i]
                max_dev = max_mag_devs[i]
                delta_v = delta_v_data.get(full_name, None)
                
                if delta_v is not None:
                    sat_to_sk_and_dv[full_name] = {
                        'sk_interval': sk_interval,
                        'max_dev': max_dev,
                        'delta_v': delta_v
                    }
    
    if not sat_to_sk_and_dv:
        print("No valid data after applying exclusions")
        return
    
    # Group by SK interval and calculate averages
    sk_groups = defaultdict(lambda: {'max_devs': [], 'delta_vs': []})
    
    for sat_name, info in sat_to_sk_and_dv.items():
        sk_interval = info['sk_interval']
        sk_groups[sk_interval]['max_devs'].append(info['max_dev'])
        sk_groups[sk_interval]['delta_vs'].append(info['delta_v'])
    
    # Calculate means for each SK interval
    sk_interval_data = {}
    for sk_interval, values in sk_groups.items():
        mean_dev = np.mean(values['max_devs'])
        mean_dv = np.mean(values['delta_vs'])
        sk_interval_data[sk_interval] = {
            'mean_dev': mean_dev,
            'mean_dv': mean_dv,
            'n_points': len(values['max_devs'])
        }
    
    # Sort SK intervals by hours for consistent coloring
    sk_hours_map = {}
    for sk_interval in sk_interval_data.keys():
        try:
            sk_hours, _ = parse_sk_interval(sk_interval)
            sk_hours_map[sk_interval] = sk_hours
        except ValueError:
            sk_hours_map[sk_interval] = float('inf')
    
    sorted_sk_intervals = sorted(sk_interval_data.keys(), key=lambda x: sk_hours_map[x])
    
    # Define color palette for SK intervals
    num_sk = len(sorted_sk_intervals)
    colors_sk = plt.cm.tab20(np.linspace(0, 1, num_sk))
    
    # Create figure
    fig, ax = plt.subplots(figsize=PLOT_DIM_SINGLE)
    
    # Plot each SK interval as a point
    for idx, sk_interval in enumerate(sorted_sk_intervals):
        data = sk_interval_data[sk_interval]
        color = colors_sk[idx]
        
        # Clean up SK interval label (remove 'SK' prefix)
        label = sk_interval.replace('SK', '')
        
        ax.scatter(data['mean_dev'] * 1000,  # Convert to meters
                   data['mean_dv'] * 1000,   # Convert to mm/s
                   s=200, color=color, label=label, alpha=0.7, edgecolors='black', linewidth=1.5)
    
    # Formatting
    ax.set_xlabel('Mean Maximum Deviation (m)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Mean Delta V (mm/s/orbit)', fontsize=12, fontweight='bold')
    ax.set_title('Delta V vs Maximum Deviation by Station Keeping Interval\n(Octahedron Constellation)', 
                 fontsize=14, fontweight='bold')
    
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(title='SK Interval', ncol=1, loc='best', fontsize=10, framealpha=0.9, title_fontsize=11)
    
    # Set scales based on parameters
    if x_log:
        ax.set_xscale('log')
    if y_log:
        ax.set_yscale('log')
    
    plt.tight_layout()
    
    # Save figure
    current_dir = Path(__file__).resolve().parent
    plots_dir = current_dir / "results"
    plots_dir.mkdir(exist_ok=True)
    
    # Add scale info to filename
    scale_suffix = ""
    if x_log:
        scale_suffix += "_xlog"
    if y_log:
        scale_suffix += "_ylog"
    if exclude_names:
        exclude_suffix = "_exclude_" + "_".join(exclude_names).lower()
        scale_suffix += exclude_suffix
    
    filename = f"delta_v_vs_max_deviation{scale_suffix}.png"
    fig.savefig(plots_dir / filename, dpi=600, bbox_inches='tight')
    print(f"Plot saved to: {plots_dir / filename}")
    
    plt.show()

# %% Run
excluded_sats_for_delta_v_plot = [
    'SK3d',      # These display noise issues (100s of m vibrations in 0.001s)
    'SK1h_Yp',   # Manoeuver optimisation did not apply correctly, uses same dv for each maneuver and diverges
    'SK1h_Ym',   # Manoeuver optimisation did not apply correctly, uses same dv for each maneuver and diverges
    'SK1h_Zp',   # Manoeuver optimisation did not apply correctly, uses same dv for each maneuver and diverges
    'SK1h_Zm',   # Manoeuver optimisation did not apply correctly, uses same dv for each maneuver and diverges
    'SK0p5h_Zp', # not simulated yet
    'SK0p5h_Zm', # not simulated yet
    'SK0p5h_Yp', # Manoeuver optimisation did not apply correctly, uses same dv for each maneuver and diverges
    'SK0p5h_Ym', # not simulated yet
    ]
plot_delta_v_vs_sk_duration(
                            exclude_names=excluded_sats_for_delta_v_plot,
                            y_log=True,
                            x_axis_days=True,
                            )

# %% Run deviation analysis
satellite_data = calculate_max_deviations()

# %% Plot deviations
excluded_sats = [
    'SK3d',      # These display noise issues (100s of m vibrations in 0.001s)
    'SK1d_Xm',   # Unknown issue causing oscillation at 170 days
    'SK1d_Zm',   # Unknown issue causing oscillation at 170 days
    'SK1h_Yp',   # Manoeuver optimisation did not apply correctly, uses same dv for each maneuver and diverges
    'SK1h_Ym',   # Manoeuver optimisation did not apply correctly, uses same dv for each maneuver and diverges
    'SK1h_Zp',   # Manoeuver optimisation did not apply correctly, uses same dv for each maneuver and diverges
    'SK1h_Zm',   # Manoeuver optimisation did not apply correctly, uses same dv for each maneuver and diverges
    'SK0p5h_Zp', # not simulated yet
    'SK0p5h_Zm', # not simulated yet
    'SK0p5h_Yp', # Manoeuver optimisation did not apply correctly, uses same dv for each maneuver and diverges
    'SK0p5h_Ym', # not simulated yet
    ]
plot_max_deviations(satellite_data,
                    x_log=True,
                    y_log=True,
                    exclude_names = excluded_sats,
                    )
# %% Plot magnitude deviations only
plot_magnitude_deviations(satellite_data,
                         x_log=True,
                         y_log=True,
                         exclude_names=excluded_sats)
# %%
plot_deviations_over_time(
                          "Ym1000m", # Example satellite
                          sk_interval="SK1h",
                        #   "Ym1000m",
                        #   sk_interval="SK6h",
                          x_axis_days=True,
                          )

# %% Plot deviations over time for multiple SK intervals
for interval in [
    # 'SK0p5h',
    # 'SK1h',
    'SK3h',
    'SK6h',
    'SK12h',
    'SK1d',
    'SK3d',
    'SK7d',
    'SK14d',
    'SK28d',
    ]:
    plot_deviations_over_time(
                              "Xp1000m", # Example satellite
                              sk_interval=interval,
                              x_axis_days=True,
                              )
# %%
plot_delta_v_vs_max_deviation(satellite_data,
                             x_log=True,
                             y_log=True,
                             exclude_names=excluded_sats)
# %%
plot_delta_v_vs_max_deviation(satellite_data,
                             x_log=True,
                             y_log=False,
                             exclude_names=excluded_sats)
# %%
