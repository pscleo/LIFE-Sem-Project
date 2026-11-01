import csv
from datetime import datetime
from pathlib import Path
import pandas as pd

def export_maneuver_summary_report(stkRoot, sat_name, verbose=False):
    """
    Export maneuver summary report for a satellite.
    
    Parameters:
    -----------
    stkRoot : STK Root object
        The STK root object
    sat_name : str
        Name of the satellite to export report for
    verbose : bool, optional
        Print status messages (default: False)
    
    Returns:
    --------
    file_path_str : str
        Absolute path where the report was saved
    """
    # Get the absolute path to the data-export/temp directory
    # Navigate from this helper file up to automation, then to data-export/temp
    current_file = Path(__file__).resolve()
    helpers_dir = current_file.parent
    automation_dir = helpers_dir.parent
    export_dir = automation_dir / "data-export" / "temp"
    
    # Create the directory if it doesn't exist
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # Create file path
    file_path = export_dir / f"{sat_name}.txt"
    file_path_str = str(file_path.absolute())
    
    try:
        # Execute the command
        stkRoot.ExecuteCommand(f'ReportCreate */Satellite/{sat_name} Style "Maneuver-Summary-Detailed" Type Save File "{file_path_str}"')
        
        if verbose:
            print(f'✓ Maneuver summary report exported for {sat_name}')
            print(f'  Saved to: {file_path_str}')
        
        return file_path_str
    
    except Exception as e:
        if verbose:
            print(f'✗ Failed to export report for {sat_name}: {str(e)}')
        raise

def parse_maneuver_summary_report(txt_file_path, delete_source=False, verbose=False):
    """
    Parse STK maneuver summary report from text format to CSV with metadata header.
    Uses column-based parsing to handle fixed-width formatted data.
    
    Parameters:
    -----------
    txt_file_path : str or Path
        Path to the .txt maneuver summary file
    delete_source : bool, optional
        Delete the source .txt file after parsing (default: False)
    verbose : bool, optional
        Print status messages (default: False)
    
    Returns:
    --------
    csv_file_path : str
        Absolute path where the CSV was saved
    """
    from pathlib import Path
    import re
    
    txt_path = Path(txt_file_path)
    
    # Read the text file
    with open(txt_path, 'r') as f:
        lines = f.readlines()
    
    # Extract satellite name and timestamp from header
    export_time = lines[0].strip()
    satellite_name = lines[1].strip().replace('Satellite-', '')
    
    # Find the maneuver data table and statistics section
    table_start_idx = None
    stats_start_idx = None
    
    for i, line in enumerate(lines):
        if 'Maneuver Number' in line:
            table_start_idx = i
        if 'Statistics' in line:
            stats_start_idx = i
            break
    
    if table_start_idx is None:
        raise ValueError("Could not find maneuver table in report")
    
    # Parse maneuver data rows (between table header and Statistics section)
    data_rows = []
    data_start = table_start_idx + 2  # Skip header and separator lines
    data_end = stats_start_idx if stats_start_idx else len(lines)
    
    for i in range(data_start, data_end):
        line = lines[i]
        if not line.strip() or line.strip() == '':
            continue
        
        # Use regex to extract the fixed columns
        # Format: Maneuver# | Segment | Start Time | Stop Time | Duration | Burn Duration | Delta V | Fuel
        match = re.search(r'(\d+)\s+(Sequence[^\d]*)\s+(\d+\s+\w+\s+\d+\s+\d+:\d+:\d+\.\d+)\s+(\d+\s+\w+\s+\d+\s+\d+:\d+:\d+\.\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', line)
        
        if match:
            maneuver_num, segment, start_time, stop_time, duration, burn_duration, delta_v, fuel = match.groups()
            
            data_rows.append({
                'Maneuver Number': maneuver_num,
                'Segment': segment.strip(),
                'Start Time (UTCG)': start_time.strip(),
                'Stop Time (UTCG)': stop_time.strip(),
                'Duration (sec)': duration,
                'Est./Act. Finite Burn Duration (sec)': burn_duration,
                'Delta V (m/sec)': delta_v,
                'Fuel Used (kg)': fuel
            })
    
    # Parse statistics section
    stats_dict = {}
    if stats_start_idx:
        for i in range(stats_start_idx + 2, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
            
            # Extract statistic name and value
            # Format: "Statistic Name    value"
            parts = line.split()
            if len(parts) >= 2:
                # Last part is the value, everything else is the name
                stat_name = ' '.join(parts[:-1])
                stat_value = parts[-1]
                stats_dict[stat_name] = stat_value
    
    # Create output directory
    current_file = Path(__file__).resolve()
    helpers_dir = current_file.parent
    automation_dir = helpers_dir.parent
    output_dir = automation_dir / "data-export" / "maneuver-summaries"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write CSV with metadata header
    csv_file_path = output_dir / f"{satellite_name}.csv"
    csv_file_str = str(csv_file_path.absolute())
    
    with open(csv_file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write metadata header
        writer.writerow(['Satellite Name', satellite_name])
        writer.writerow(['Export Time', export_time])
        writer.writerow([])  # Blank line
        
        # Write statistics section in header
        if stats_dict:
            writer.writerow(['Statistics'])
            # Map stat names to their units
            stat_units = {
                'Total Duration': 'sec',
                'Total Est./Act. Finite Burn Duration': 'sec',
                'Total Delta V': 'm/sec',
                'Total Fuel Used': 'kg'
            }
            for stat_name, stat_value in stats_dict.items():
                unit = stat_units.get(stat_name, '')
                if unit:
                    writer.writerow([f'{stat_name} ({unit})', stat_value])
                else:
                    writer.writerow([stat_name, stat_value])
            writer.writerow([])  # Blank line
        
        # Write header separator marker
        writer.writerow(['--- BEGIN DATA ---'])
        
        # Write maneuver data
        if data_rows:
            writer.writerow(list(data_rows[0].keys()))
            for row in data_rows:
                writer.writerow(list(row.values()))
    
    if verbose:
        print(f'✓ Parsed maneuver summary: {satellite_name}')
        print(f'  CSV saved to: {csv_file_str}')
        print(f'  Maneuvers parsed: {len(data_rows)}')
        print(f'  Statistics entries: {len(stats_dict)}')
    
    # Delete source file if requested
    if delete_source:
        txt_path.unlink()
        if verbose:
            print(f'  Deleted source file: {txt_path}')
    
    return csv_file_str

def export_relative_position_report(stkRoot, sat_name, time_period_start=None, time_period_end="UseAnalysisStopTime", time_step_seconds=3600, verbose=False):
    """
    Export relative position report for a satellite using the Relative-position-of-Base-Export style.
    The position is from the satellite to the "Base" satellite, therefore all position components are
    negative of the actual relative position vector.
    
    Parameters:
    -----------
    stkRoot : STK Root object
        The STK root object
    sat_name : str
        Name of the satellite to export report for
    time_period_start : str, optional
        Start time for report (format: 'DD MMM YYYY HH:MM:SS.ff').
        If None, uses analysis start time. (default: None)
    time_period_end : str, optional
        End time for report. Can be a time string or "UseAnalysisStopTime".
        (default: "UseAnalysisStopTime")
    time_step_seconds : int, optional
        Time step in seconds (default: 3600 = 1 hour)
    verbose : bool, optional
        Print status messages (default: False)
    
    Returns:
    --------
    file_path_str : str
        Absolute path where the report was saved
    """
    # Get the absolute path to the helpers directory for the .rst file
    current_file = Path(__file__).resolve()
    helpers_dir = current_file.parent
    automation_dir = helpers_dir.parent
    
    # Path to the report style file
    rst_file_path = helpers_dir / "Relative-position-of-Base-Export.rst"
    rst_file_str = str(rst_file_path.absolute())
    
    # Path to the data-export/temp/position directory
    export_dir = automation_dir / "data-export" / "temp" / "position"
    
    # Create the directory if it doesn't exist
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # Create file path
    file_path = export_dir / f"{sat_name}.txt"
    file_path_str = str(file_path.absolute())
    
    try:
        # Load the report style
        stkRoot.ExecuteCommand(f'ReportStyle * Load "{rst_file_str}"')
        
        # Build time period command
        if time_period_start is None:
            time_period_cmd = f'TimePeriod "UseAnalysisStartTime" "{time_period_end}" TimeStep {time_step_seconds}'
        else:
            time_period_cmd = f'TimePeriod "{time_period_start}" "{time_period_end}" TimeStep {time_step_seconds}'

        # Export the report with time period and step
        stkRoot.ExecuteCommand(f'ReportCreate */Satellite/{sat_name} Style "Relative-position-of-Base-Export" Type Save File "{file_path_str}" {time_period_cmd}')
        
        if verbose:
            print(f'✓ Relative position report exported for {sat_name}')
            print(f'  Style: {rst_file_str}')
            print(f'  Time period: {time_period_cmd}')
            print(f'  Saved to: {file_path_str}')
        
        return file_path_str
    
    except Exception as e:
        if verbose:
            print(f'✗ Failed to export relative position report for {sat_name}: {str(e)}')
        raise

def parse_stk_position_txt(txt_file_path, output_dir=None, start_time=None, trim_data=True, 
                           delete_source=False, verbose=False):
    """
    Parse STK position report .txt file using column positions from separator line.
    Converts from "position of Base relative to satellite" to "position of satellite relative to Base"
    by flipping sign of x, y, z coordinates and their derivatives.
    
    Parameters:
    -----------
    txt_file_path : Path or str
        Path to the .txt file
    output_dir : Path or str, optional
        Output directory for CSV file. If None, uses data-export/positions.
        (default: None)
    start_time : str, optional
        Start time for filtering data (format: 'DD MMM YYYY HH:MM:SS.fff').
        Data points before this time are discarded.
        Only used if trim_data=True. (default: None)
    trim_data : bool, optional
        If True, filters data using start_time parameter.
        If False, keeps all data regardless of start_time. (default: True)
    delete_source : bool, optional
        Delete the source .txt file after parsing (default: False)
    verbose : bool, optional
        Print parsing progress information. (default: False)
    
    Returns:
    --------
    csv_file_path : Path
        Absolute path where the CSV was saved
    """
    txt_file_path = Path(txt_file_path)
    
    if not txt_file_path.exists():
        print(f"✗ File not found: {txt_file_path}")
        return None
    
    # Default output directory
    if output_dir is None:
        current_file = Path(__file__).resolve()
        helpers_dir = current_file.parent
        automation_dir = helpers_dir.parent
        output_dir = automation_dir / "data-export" / "positions"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if verbose:
        print(f"Parsing: {txt_file_path.name}")
        print(f"  Trim data: {trim_data}")
        if trim_data and start_time:
            print(f"  Start time filter: {start_time}")
    
    # Read the file
    with open(txt_file_path, 'r') as f:
        lines = f.readlines()
    
    # Extract metadata from header
    export_time = lines[0].strip()
    satellite_name = lines[1].strip().replace('Satellite-', '')
    
    # Find header and separator lines
    header_line_idx = None
    separator_line_idx = None
    
    for i, line in enumerate(lines):
        if 'Time (UTCG)' in line:
            header_line_idx = i
            separator_line_idx = i + 1
            break
    
    if header_line_idx is None:
        print(f"✗ Could not find header in {txt_file_path.name}")
        return None
    
    if verbose:
        print(f"  Header found at line {header_line_idx}")
        print(f"  Separator at line {separator_line_idx}")
    
    # Parse the header and separator lines to get column positions
    header_line = lines[header_line_idx]
    separator_line = lines[separator_line_idx]
    
    # Find column start positions by looking for dashes in separator
    col_starts = []
    in_dashes = False
    
    for i, char in enumerate(separator_line):
        if char == '-' and not in_dashes:
            col_starts.append(i)
            in_dashes = True
        elif char != '-' and in_dashes:
            in_dashes = False
    
    if verbose:
        print(f"  Found {len(col_starts)} columns at positions: {col_starts}")
    
    # Get column names from header (trim whitespace)
    col_names = []
    for i, start_pos in enumerate(col_starts):
        if i + 1 < len(col_starts):
            end_pos = col_starts[i + 1]
        else:
            end_pos = len(header_line)
        
        col_name = header_line[start_pos:end_pos].strip()
        col_names.append(col_name)
    
    if verbose:
        print(f"  Column names: {col_names}")
    
    # Parse data rows using column positions
    data_rows = []
    data_start_idx = separator_line_idx + 1
    rows_checked = 0
    rows_filtered = 0
    rows_parsed = 0
    
    for i, line in enumerate(lines[data_start_idx:], start=data_start_idx):
        if not line.strip():
            continue  # Skip empty lines
        
        rows_checked += 1
        
        try:
            row = {}
            
            for col_idx, start_pos in enumerate(col_starts):
                if col_idx + 1 < len(col_starts):
                    end_pos = col_starts[col_idx + 1]
                else:
                    end_pos = len(line)
                
                col_name = col_names[col_idx]
                col_value = line[start_pos:end_pos].strip()
                
                if not col_value:
                    continue
                
                # Try to convert to float if it looks like a number
                if col_name in ['x (km)', 'y (km)', 'z (km)', 'Magnitude (km)', 
                               'Derivative x (km/sec)', 'Derivative y (km/sec)', 
                               'Derivative z (km/sec)', 'Derivative Magnitude (km/sec)']:
                    try:
                        row[col_name] = float(col_value)
                    except ValueError:
                        pass
                else:
                    # Keep as string (for time)
                    row[col_name] = col_value
            
            # Only add if we got the essential data
            if 'Time (UTCG)' not in row or 'x (km)' not in row:
                continue
            
            time_utcg = row['Time (UTCG)']
            
            # Filter by start_time only if trim_data is True
            if trim_data and start_time is not None:
                if time_utcg < start_time:
                    rows_filtered += 1
                    continue
            
            # Flip signs for coordinates and derivatives (not magnitude)
            if 'x (km)' in row:
                row['x (km)'] = -row['x (km)']
            if 'y (km)' in row:
                row['y (km)'] = -row['y (km)']
            if 'z (km)' in row:
                row['z (km)'] = -row['z (km)']
            if 'Derivative x (km/sec)' in row:
                row['Derivative x (km/sec)'] = -row['Derivative x (km/sec)']
            if 'Derivative y (km/sec)' in row:
                row['Derivative y (km/sec)'] = -row['Derivative y (km/sec)']
            if 'Derivative z (km/sec)' in row:
                row['Derivative z (km/sec)'] = -row['Derivative z (km/sec)']
            # Note: Magnitude and Derivative Magnitude are NOT flipped
            
            data_rows.append(row)
            rows_parsed += 1
            
        except (ValueError, IndexError) as e:
            if verbose and rows_checked <= 5:
                print(f"  Warning: Could not parse line {i}: {str(e)}")
            continue
    
    if verbose:
        print(f"  Rows checked: {rows_checked}")
        if trim_data:
            print(f"  Rows filtered (before start_time): {rows_filtered}")
        print(f"  Rows successfully parsed: {rows_parsed}")
    
    if len(data_rows) == 0:
        print(f"✗ No valid data rows found")
        return None
    
    # Create DataFrame
    df = pd.DataFrame(data_rows)
    
    # Write CSV with metadata header
    csv_filename = txt_file_path.stem + '.csv'
    csv_path = output_dir / csv_filename
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write metadata header
        writer.writerow(['Satellite Name', satellite_name])
        writer.writerow(['Export Time', export_time])
        if trim_data and start_time:
            writer.writerow(['Data Start Time (trimmed)', start_time])
        else:
            writer.writerow(['Data Trimming', 'Disabled'])
        writer.writerow(['Note', 'Position coordinates flipped (position of satellite relative to Base)'])
        writer.writerow([])  # Blank line
        
        # Write header separator marker
        writer.writerow(['--- BEGIN DATA ---'])
        
        # Write column headers
        writer.writerow(list(df.columns))
        
        # Write data rows
        for _, row in df.iterrows():
            writer.writerow(list(row.values))
    
    if verbose:
        print(f"✓ CSV saved to: {csv_path}")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Shape: {df.shape}")
        print(f"  First row:\n  {df.iloc[0].to_dict()}")
    
    # Delete source file if requested
    if delete_source:
        try:
            txt_file_path.unlink()
            if verbose:
                print(f"✓ Source .txt file deleted: {txt_file_path}")
        except Exception as e:
            if verbose:
                print(f"✗ Could not delete source file: {str(e)}")
    
    return str(csv_path.absolute())

def remove_position_spikes(csv_file_path, window_size=5, threshold_mad=3, verbose=False):
    """
    Remove position data spikes by detecting outliers and interpolating them.
    Uses median absolute deviation (MAD) for robust outlier detection that's 
    resistant to extreme outliers pulling the statistics.
    When a spike is detected in any coordinate, the entire row is recalculated
    using the mean of neighboring rows (assumes smooth curves).
    
    Parameters:
    -----------
    csv_file_path : str or Path
        Path to the CSV position file
    window_size : int, optional
        Window size for outlier detection (must be odd, 5 recommended).
        (default: 5)
    threshold_mad : float, optional
        Number of MAD (median absolute deviations) to consider as outlier.
        More robust than std. (default: 3)
    verbose : bool, optional
        Print status messages (default: False)
    
    Returns:
    --------
    csv_file_path : str
        Path to the cleaned CSV file
    """
    from pathlib import Path
    import csv
    import numpy as np
    
    csv_path = Path(csv_file_path)
    
    # Read the CSV file
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    # Find the data start (after "--- BEGIN DATA ---")
    data_start_idx = None
    for i, row in enumerate(rows):
        if row and row[0] == '--- BEGIN DATA ---':
            data_start_idx = i + 2  # Skip marker and header row
            break
    
    if data_start_idx is None:
        if verbose:
            print("Could not find data section in CSV")
        return str(csv_path)
    
    # Extract header
    header_row = rows[data_start_idx - 1]
    metadata_rows = rows[:data_start_idx - 2]
    
    # Extract and convert data
    data_rows = rows[data_start_idx:]
    
    # Column indices for position and derivative data
    x_idx = header_row.index('x (km)') if 'x (km)' in header_row else 1
    y_idx = header_row.index('y (km)') if 'y (km)' in header_row else 2
    z_idx = header_row.index('z (km)') if 'z (km)' in header_row else 3
    magnitude_idx = header_row.index('Magnitude (km)') if 'Magnitude (km)' in header_row else 4
    deriv_x_idx = header_row.index('Derivative x (km/sec)') if 'Derivative x (km/sec)' in header_row else 5
    deriv_y_idx = header_row.index('Derivative y (km/sec)') if 'Derivative y (km/sec)' in header_row else 6
    deriv_z_idx = header_row.index('Derivative z (km/sec)') if 'Derivative z (km/sec)' in header_row else 7
    deriv_magnitude_idx = header_row.index('Derivative Magnitude (km/sec)') if 'Derivative Magnitude (km/sec)' in header_row else 8
    
    # Convert to numpy arrays for easier processing
    positions = []
    derivatives = []
    magnitudes = []
    deriv_magnitudes = []
    
    for row in data_rows:
        try:
            x = float(row[x_idx])
            y = float(row[y_idx])
            z = float(row[z_idx])
            mag = float(row[magnitude_idx])
            deriv_x = float(row[deriv_x_idx])
            deriv_y = float(row[deriv_y_idx])
            deriv_z = float(row[deriv_z_idx])
            deriv_mag = float(row[deriv_magnitude_idx])
            
            positions.append([x, y, z])
            derivatives.append([deriv_x, deriv_y, deriv_z])
            magnitudes.append(mag)
            deriv_magnitudes.append(deriv_mag)
        except (ValueError, IndexError):
            continue
    
    positions = np.array(positions, dtype=float)
    derivatives = np.array(derivatives, dtype=float)
    magnitudes = np.array(magnitudes, dtype=float)
    deriv_magnitudes = np.array(deriv_magnitudes, dtype=float)
    
    original_count = len(positions)
    spikes_detected = 0
    spike_indices = set()
    
    # Detect spikes for each coordinate
    for coord_idx in range(3):  # x, y, z
        coord_data = positions[:, coord_idx].copy()
        
        for i in range(window_size // 2, len(coord_data) - window_size // 2):
            # Get window around current point
            window_start = i - window_size // 2
            window_end = i + window_size // 2 + 1
            window = coord_data[window_start:window_end]
            
            # Use median (robust to outliers) instead of mean
            window_median = np.median(window)
            
            # Calculate MAD (Median Absolute Deviation) - robust to outliers
            abs_deviations = np.abs(window - window_median)
            mad = np.median(abs_deviations)
            
            # Check if center point is an outlier using MAD
            current_val = coord_data[i]
            deviation = abs(current_val - window_median)
            
            # Avoid division by zero
            if mad > 1e-10:
                mad_score = deviation / mad
            else:
                mad_score = 0
            
            if mad_score > threshold_mad:
                spike_indices.add(i)
                spikes_detected += 1
                
                if verbose and spikes_detected <= 10:  # Show first few
                    print(f'  Spike detected at index {i} in coordinate {["x", "y", "z"][coord_idx]}: {current_val:.6e} (MAD score: {mad_score:.2f})')
    
    # Recalculate entire rows for spike indices using mean of neighbors
    for spike_idx in spike_indices:
        window_start = max(0, spike_idx - window_size // 2)
        window_end = min(len(positions), spike_idx + window_size // 2 + 1)
        
        # Get neighbors (excluding the spike)
        neighbors_pos = np.concatenate([
            positions[window_start:spike_idx],
            positions[spike_idx + 1:window_end]
        ])
        neighbors_deriv = np.concatenate([
            derivatives[window_start:spike_idx],
            derivatives[spike_idx + 1:window_end]
        ])
        neighbors_mag = np.concatenate([
            magnitudes[window_start:spike_idx],
            magnitudes[spike_idx + 1:window_end]
        ])
        neighbors_deriv_mag = np.concatenate([
            deriv_magnitudes[window_start:spike_idx],
            deriv_magnitudes[spike_idx + 1:window_end]
        ])
        
        # Interpolate using MEAN of neighbors for smooth curve continuity
        positions[spike_idx] = np.mean(neighbors_pos, axis=0)
        derivatives[spike_idx] = np.mean(neighbors_deriv, axis=0)
        magnitudes[spike_idx] = np.mean(neighbors_mag)
        deriv_magnitudes[spike_idx] = np.mean(neighbors_deriv_mag)
    
    if verbose:
        print(f'Spike detection and interpolation complete:')
        print(f'  Total data points: {original_count}')
        print(f'  Rows with spikes detected: {len(spike_indices)}')
        if original_count > 0:
            print(f'  Percentage removed: {100 * len(spike_indices) / original_count:.3f}%')
    
    # Write cleaned data back to CSV
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write metadata and header
        for row in metadata_rows:
            writer.writerow(row)
        writer.writerow([])  # Blank line
        writer.writerow(['--- BEGIN DATA ---'])
        writer.writerow(header_row)
        
        # Write cleaned data rows
        for i, original_row in enumerate(data_rows):
            if i < len(positions):
                # Replace all position and derivative values
                cleaned_row = original_row.copy()
                cleaned_row[x_idx] = f'{positions[i, 0]:.15e}'
                cleaned_row[y_idx] = f'{positions[i, 1]:.15e}'
                cleaned_row[z_idx] = f'{positions[i, 2]:.15e}'
                cleaned_row[magnitude_idx] = f'{magnitudes[i]:.15e}'
                cleaned_row[deriv_x_idx] = f'{derivatives[i, 0]:.15e}'
                cleaned_row[deriv_y_idx] = f'{derivatives[i, 1]:.15e}'
                cleaned_row[deriv_z_idx] = f'{derivatives[i, 2]:.15e}'
                cleaned_row[deriv_magnitude_idx] = f'{deriv_magnitudes[i]:.15e}'
                writer.writerow(cleaned_row)
            else:
                writer.writerow(original_row)
    
    if verbose:
        print(f'Cleaned CSV saved to: {csv_path}')
    
    return str(csv_path)