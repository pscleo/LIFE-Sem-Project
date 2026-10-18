# %% Beginning
%matplotlib tk

# %% Beginning
import pandas as pd
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# Get the path to the data directory
current_dir = Path(__file__).resolve().parent
deviations_dir = current_dir / "data-export" / "deviations"
results_dir = current_dir / "results"
results_dir.mkdir(exist_ok=True)

# Global plot dimensions configuration
scaler = 0.75
PLOT_DIM_SINGLE = (15 * scaler, 7 * scaler)      # Single plot


def plot_x_deviation_over_time(satellite_name, sk_interval=None, x_axis_days=False, 
                                csv_dir=None, parse_from_txt=False):
    """
    Plot x-deviation over time for a specified satellite (simplified version).
    
    Parameters:
    -----------
    satellite_name : str
        Satellite name or partial name:
        - "Octahedron_SK7d_Xp1000m" (full name)
        - "Xp1000m" (partial, use with sk_interval)
    sk_interval : str, optional
        SK interval to filter (e.g., "SK7d"). Only used with partial satellite_name.
        (default: None)
    x_axis_days : bool, optional
        If True, show x-axis in days. If False, show x-axis in hours. (default: False)
    csv_dir : Path or str, optional
        Directory containing CSV files. If None, uses debugging folder.
        (default: None)
    parse_from_txt : bool, optional
        If True, parse from .txt files first. If False, look for existing CSV.
        (default: False)
    
    Examples:
    ---------
    # Plot by full name (using existing CSV)
    plot_x_deviation_over_time("Octahedron_SK28d_Xm1000m", x_axis_days=True)
    
    # Plot by partial name with SK interval
    plot_x_deviation_over_time("Xm1000m", sk_interval="SK28d", x_axis_days=True)
    
    # Parse from .txt first, then plot
    plot_x_deviation_over_time("Xm1000m", sk_interval="SK28d", 
                               parse_from_txt=True, x_axis_days=True)
    """
    
    # Set default CSV directory
    if csv_dir is None:
        csv_dir = current_dir / "data-export" / "debugging"
    else:
        csv_dir = Path(csv_dir)
    
    csv_dir.mkdir(parents=True, exist_ok=True)
    
    # Build the filename
    if sk_interval:
        # Search mode: construct filename from components
        csv_filename = f"Octahedron_{sk_interval}_{satellite_name}.csv"
    else:
        # Direct mode: use satellite_name as full filename
        csv_filename = f"{satellite_name}.csv"
    
    csv_path = csv_dir / csv_filename
    
    # Parse from .txt if requested or if CSV doesn't exist
    if parse_from_txt or not csv_path.exists():
        if parse_from_txt and not csv_path.exists():
            print(f"CSV not found, parsing from .txt...")
        
        # Build the .txt filename
        if sk_interval:
            txt_filename = f"Octahedron_{sk_interval}_{satellite_name}.txt"
        else:
            txt_filename = f"{satellite_name}.txt"
        
        txt_path = current_dir / "data-export" / "temp" / "position" / txt_filename
        
        if not txt_path.exists():
            print(f"✗ .txt file not found: {txt_path}")
            print(f"\nTrying to find available files...")
            txt_dir = current_dir / "data-export" / "temp" / "position"
            available = list(txt_dir.glob("*.txt"))
            if available:
                for f in sorted(available)[:10]:
                    print(f"  - {f.name}")
                if len(available) > 10:
                    print(f"  ... and {len(available) - 10} more")
            return
        
        # Parse the .txt file
        df = parse_stk_position_txt(txt_path, output_dir=csv_dir, verbose=True)
        if df is None:
            return
    else:
        # Read existing CSV
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"✗ Error reading CSV: {str(e)}")
            return
    
    # Check if required columns exist
    if 'x (km)' not in df.columns:
        print(f"✗ Column 'x (km)' not found in CSV")
        print(f"Available columns: {list(df.columns)}")
        return
    
    # For now, plot x vs time (we'll calculate deviations separately)
    title_name = csv_filename.replace('.csv', '')
    
    # Prepare x-axis data (time)
    if x_axis_days:
        # Assume 10-minute time steps from export
        time_step_minutes = 10.0
        time_step_hours = time_step_minutes / 60.0
        x_axis_data = np.arange(len(df)) * time_step_hours / 24.0  # Convert to days
        x_label = 'Time (days from start)'
    else:
        # Time in hours from start (assuming 10-minute steps)
        time_step_minutes = 10.0
        time_step_hours = time_step_minutes / 60.0
        x_axis_data = np.arange(len(df)) * time_step_hours
        x_label = 'Time (hours from start)'
    
    # Convert position from km to meters
    y_values = df['x (km)'] * 1000
    
    # Calculate statistics
    max_dev = y_values.max()
    min_dev = y_values.min()
    mean_dev = y_values.mean()
    std_dev = y_values.std()
    
    # Create figure
    fig, ax = plt.subplots(figsize=PLOT_DIM_SINGLE)
    
    # Plot the x position
    ax.plot(x_axis_data, y_values, color='#4DA6FF', linewidth=1.5, alpha=0.8, label='X position')
    ax.fill_between(x_axis_data, y_values, alpha=0.2, color='#4DA6FF')
    
    # Add reference lines for mean and extremes
    ax.axhline(mean_dev, color='red', linestyle='--', linewidth=1.5, alpha=0.6, label=f'Mean: {mean_dev:.3f}m')
    ax.axhline(max_dev, color='darkgreen', linestyle=':', linewidth=1.5, alpha=0.6, label=f'Max: {max_dev:.3f}m')
    ax.axhline(min_dev, color='darkred', linestyle=':', linewidth=1.5, alpha=0.6, label=f'Min: {min_dev:.3f}m')
    
    # Formatting
    ax.set_xlabel(x_label, fontsize=12, fontweight='bold')
    ax.set_ylabel('X Position (m)', fontsize=12, fontweight='bold')
    ax.set_title(f'X Position Over Time\n{title_name}', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', fontsize=10, framealpha=0.9)
    
    # Add statistics text box
    stats_text = f'Max: {max_dev:.3f}m\nMin: {min_dev:.3f}m\nMean: {mean_dev:.3f}m\nStd: {std_dev:.3f}m'
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))
    
    plt.tight_layout()
    
    # Save figure
    axis_suffix = '_vs_days' if x_axis_days else '_vs_hours'
    filename = f"x_position{axis_suffix}_{title_name}.png"
    fig.savefig(results_dir / filename, dpi=600, bbox_inches='tight')
    print(f"✓ Plot saved to: {results_dir / filename}")
    
    # Print summary statistics
    print(f"\nStatistics for {title_name}:")
    print(f"  X Position:")
    print(f"    Max:  {max_dev:8.3f} m")
    print(f"    Min:  {min_dev:8.3f} m")
    print(f"    Mean: {mean_dev:8.3f} m")
    print(f"    Std:  {std_dev:8.3f} m")
    print(f"    Range: {max_dev - min_dev:.3f} m")
    
    plt.show()


# %% Parser: Convert STK position .txt files to CSV (with helper functionalities)

import csv
import re

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
    pd.DataFrame
        DataFrame with columns: Time, x (km), y (km), z (km), Magnitude (km),
                               and optional derivative columns
    """
    txt_file_path = Path(txt_file_path)
    
    if not txt_file_path.exists():
        print(f"✗ File not found: {txt_file_path}")
        return None
    
    # Default output directory
    if output_dir is None:
        output_dir = current_dir / "data-export" / "positions"
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
    
    return df


def parse_all_position_files(txt_dir=None, output_dir=None, start_time=None, 
                            trim_data=True, delete_source=False, verbose=False):
    """
    Parse all .txt position files in a directory.
    
    Parameters:
    -----------
    txt_dir : Path or str, optional
        Directory containing .txt files. If None, uses data-export/temp.
        (default: None)
    output_dir : Path or str, optional
        Output directory for CSV files. If None, uses data-export/positions.
        (default: None)
    start_time : str, optional
        Start time for filtering data (format: 'DD MMM YYYY HH:MM:SS.fff').
        (default: None)
    trim_data : bool, optional
        If True, filters data using start_time parameter. (default: True)
    delete_source : bool, optional
        Delete the source .txt file after parsing (default: False)
    verbose : bool, optional
        Print parsing progress. (default: False)
    
    Returns:
    --------
    dict
        Dictionary mapping filename (stem) to DataFrame
    """
    if txt_dir is None:
        txt_dir = current_dir / "data-export" / "temp"
    else:
        txt_dir = Path(txt_dir)
    
    if not txt_dir.exists():
        print(f"✗ Directory not found: {txt_dir}")
        return {}
    
    if verbose:
        print(f"Parsing all .txt files in: {txt_dir}\n")
    
    txt_files = sorted(txt_dir.glob("Octahedron_*.txt"))
    
    if not txt_files:
        print(f"No .txt files found in {txt_dir}")
        return {}
    
    results = {}
    
    for txt_file in txt_files:
        df = parse_stk_position_txt(txt_file, output_dir=output_dir, start_time=start_time,
                                   trim_data=trim_data, delete_source=delete_source, 
                                   verbose=verbose)
        if df is not None:
            results[txt_file.stem] = df
    
    if verbose:
        print(f"\n✓ Parsed {len(results)} files successfully")
    
    return results


# %% Updated plot function to use CSV from debugging folder

def plot_x_deviation_over_time(satellite_name, sk_interval=None, x_axis_days=False, 
                                csv_dir=None, parse_from_txt=False):
    """
    Plot x-deviation over time for a specified satellite (simplified version).
    
    Parameters:
    -----------
    satellite_name : str
        Satellite name or partial name:
        - "Octahedron_SK7d_Xp1000m" (full name)
        - "Xp1000m" (partial, use with sk_interval)
    sk_interval : str, optional
        SK interval to filter (e.g., "SK7d"). Only used with partial satellite_name.
        (default: None)
    x_axis_days : bool, optional
        If True, show x-axis in days. If False, show x-axis in hours. (default: False)
    csv_dir : Path or str, optional
        Directory containing CSV files. If None, uses debugging folder.
        (default: None)
    parse_from_txt : bool, optional
        If True, parse from .txt files first. If False, look for existing CSV.
        (default: False)
    
    Examples:
    ---------
    # Plot by full name (using existing CSV)
    plot_x_deviation_over_time("Octahedron_SK28d_Xm1000m", x_axis_days=True)
    
    # Plot by partial name with SK interval
    plot_x_deviation_over_time("Xm1000m", sk_interval="SK28d", x_axis_days=True)
    
    # Parse from .txt first, then plot
    plot_x_deviation_over_time("Xm1000m", sk_interval="SK28d", 
                               parse_from_txt=True, x_axis_days=True)
    """
    
    # Set default CSV directory
    if csv_dir is None:
        csv_dir = current_dir / "data-export" / "debugging"
    else:
        csv_dir = Path(csv_dir)
    
    csv_dir.mkdir(parents=True, exist_ok=True)
    
    # Build the filename
    if sk_interval:
        # Search mode: construct filename from components
        csv_filename = f"Octahedron_{sk_interval}_{satellite_name}.csv"
    else:
        # Direct mode: use satellite_name as full filename
        csv_filename = f"{satellite_name}.csv"
    
    csv_path = csv_dir / csv_filename
    
    # Parse from .txt if requested or if CSV doesn't exist
    if parse_from_txt or not csv_path.exists():
        if parse_from_txt and not csv_path.exists():
            print(f"CSV not found, parsing from .txt...")
        
        # Build the .txt filename
        if sk_interval:
            txt_filename = f"Octahedron_{sk_interval}_{satellite_name}.txt"
        else:
            txt_filename = f"{satellite_name}.txt"
        
        txt_path = current_dir / "data-export" / "temp" / "position" / txt_filename
        
        if not txt_path.exists():
            print(f"✗ .txt file not found: {txt_path}")
            print(f"\nTrying to find available files...")
            txt_dir = current_dir / "data-export" / "temp" / "position"
            available = list(txt_dir.glob("*.txt"))
            if available:
                for f in sorted(available)[:10]:
                    print(f"  - {f.name}")
                if len(available) > 10:
                    print(f"  ... and {len(available) - 10} more")
            return
        
        # Parse the .txt file
        df = parse_stk_position_txt(txt_path, output_dir=csv_dir, verbose=True)
        if df is None:
            return
    else:
        # Read existing CSV
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"✗ Error reading CSV: {str(e)}")
            return
    
    # Check if required columns exist
    if 'x (km)' not in df.columns:
        print(f"✗ Column 'x (km)' not found in CSV")
        print(f"Available columns: {list(df.columns)}")
        return
    
    # For now, plot x vs time (we'll calculate deviations separately)
    title_name = csv_filename.replace('.csv', '')
    
    # Prepare x-axis data (time)
    if x_axis_days:
        # Assume 10-minute time steps from export
        time_step_minutes = 10.0
        time_step_hours = time_step_minutes / 60.0
        x_axis_data = np.arange(len(df)) * time_step_hours / 24.0  # Convert to days
        x_label = 'Time (days from start)'
    else:
        # Time in hours from start (assuming 10-minute steps)
        time_step_minutes = 10.0
        time_step_hours = time_step_minutes / 60.0
        x_axis_data = np.arange(len(df)) * time_step_hours
        x_label = 'Time (hours from start)'
    
    # Convert position from km to meters
    y_values = df['x (km)'] * 1000
    
    # Calculate statistics
    max_dev = y_values.max()
    min_dev = y_values.min()
    mean_dev = y_values.mean()
    std_dev = y_values.std()
    
    # Create figure
    fig, ax = plt.subplots(figsize=PLOT_DIM_SINGLE)
    
    # Plot the x position
    ax.plot(x_axis_data, y_values, color='#4DA6FF', linewidth=1.5, alpha=0.8, label='X position')
    ax.fill_between(x_axis_data, y_values, alpha=0.2, color='#4DA6FF')
    
    # Add reference lines for mean and extremes
    ax.axhline(mean_dev, color='red', linestyle='--', linewidth=1.5, alpha=0.6, label=f'Mean: {mean_dev:.3f}m')
    ax.axhline(max_dev, color='darkgreen', linestyle=':', linewidth=1.5, alpha=0.6, label=f'Max: {max_dev:.3f}m')
    ax.axhline(min_dev, color='darkred', linestyle=':', linewidth=1.5, alpha=0.6, label=f'Min: {min_dev:.3f}m')
    
    # Formatting
    ax.set_xlabel(x_label, fontsize=12, fontweight='bold')
    ax.set_ylabel('X Position (m)', fontsize=12, fontweight='bold')
    ax.set_title(f'X Position Over Time\n{title_name}', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', fontsize=10, framealpha=0.9)
    
    # Add statistics text box
    stats_text = f'Max: {max_dev:.3f}m\nMin: {min_dev:.3f}m\nMean: {mean_dev:.3f}m\nStd: {std_dev:.3f}m'
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))
    
    plt.tight_layout()
    
    # Save figure
    axis_suffix = '_vs_days' if x_axis_days else '_vs_hours'
    filename = f"x_position{axis_suffix}_{title_name}.png"
    fig.savefig(results_dir / filename, dpi=600, bbox_inches='tight')
    print(f"✓ Plot saved to: {results_dir / filename}")
    
    # Print summary statistics
    print(f"\nStatistics for {title_name}:")
    print(f"  X Position:")
    print(f"    Max:  {max_dev:8.3f} m")
    print(f"    Min:  {min_dev:8.3f} m")
    print(f"    Mean: {mean_dev:8.3f} m")
    print(f"    Std:  {std_dev:8.3f} m")
    print(f"    Range: {max_dev - min_dev:.3f} m")
    
    plt.show()


# %% Test the parser and plot
if __name__ == '__main__':
    # Test 1: Parse a single file
    print("=" * 80)
    print("TEST 1: Parse single .txt file to CSV")
    print("=" * 80)
    parse_stk_position_txt(
        current_dir / "data-export" / "temp" / "position" / "Octahedron_SK28d_Xm1000m.txt",
        verbose=True
    )
    
    print("\n" + "=" * 80)
    print("TEST 2: Plot from parsed CSV")
    print("=" * 80)
    plot_x_deviation_over_time(
        "Xm1000m",
        sk_interval="SK28d",
        x_axis_days=True,
        parse_from_txt=True
    )

# %%
