from pathlib import Path

# Get paths
current_dir = Path(__file__).resolve().parent
summaries_dir = current_dir / "data-export" / "maneuver-summaries"
temp_dir = current_dir / "data-export" / "temp"

def rename_files_in_directory(directory):
    """Rename all Octahedron files from current format to: Octahedron_SK{days}d_{direction}1000m"""
    if not directory.exists():
        print(f"Directory not found: {directory}")
        return
    
    print(f"\nRenaming files in: {directory}")
    rename_count = 0
    
    # Process all Octahedron files
    for file_path in directory.glob("Octahedron_*.csv"):
        filename = file_path.stem
        # Current format: Octahedron_Xm_SK14d_1000m
        # Target format: Octahedron_SK14d_Xm1000m
        
        parts = filename.split('_')
        # parts[0] = 'Octahedron'
        # parts[1] = direction (Xm, Xp, Ym, etc.)
        # parts[2] = 'SK14d'
        # parts[3] = '1000m'
        
        if len(parts) == 4 and parts[0] == 'Octahedron':
            direction = parts[1]  # Xm, Xp, Ym, etc.
            sk_interval = parts[2]  # SK14d, SK7d, etc.
            distance = parts[3]  # 1000m
            
            new_name = f"Octahedron_{sk_interval}_{direction}{distance}"
            new_file_path = file_path.parent / f"{new_name}.csv"
            
            file_path.rename(new_file_path)
            print(f"  ✓ {filename}.csv → {new_name}.csv")
            rename_count += 1
    
    # Process all txt files
    for file_path in directory.glob("Octahedron_*.txt"):
        filename = file_path.stem
        
        parts = filename.split('_')
        
        if len(parts) == 4 and parts[0] == 'Octahedron':
            direction = parts[1]
            sk_interval = parts[2]
            distance = parts[3]
            
            new_name = f"Octahedron_{sk_interval}_{direction}{distance}"
            new_file_path = file_path.parent / f"{new_name}.txt"
            
            file_path.rename(new_file_path)
            print(f"  ✓ {filename}.txt → {new_name}.txt")
            rename_count += 1
    
    print(f"Total files renamed: {rename_count}")

# Run renaming
print("="*80)
print("RENAMING OCTAHEDRON FILES TO NEW FORMAT")
print("="*80)

rename_files_in_directory(summaries_dir)
rename_files_in_directory(temp_dir)

print("\n" + "="*80)
print("Renaming complete!")
print("="*80)