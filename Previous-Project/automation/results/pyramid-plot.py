import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_pyramid_sk_data(csv_file_path):
    """
    Plot pyramid SK burns data with dV on left Y-axis and max displacement on right Y-axis.
    
    Args:
        csv_file_path (str): Path to the CSV file containing the data
    """
    # Read the CSV file
    df = pd.read_csv(csv_file_path)
    
    # Debug: Print column names to see actual format
    print("Column names in CSV:", df.columns.tolist())
    
    # Create figure and primary axis
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # Plot dV data on left Y-axis
    x = df['SK interval [days]']
    colors = ['blue', 'red', 'green', 'orange']
    satellites = ['Sat A', 'Sat B', 'Sat C', 'Sat D']
    
    # Use the actual column names from the CSV
    dv_columns = ['dV Sat A [m/s]', 'dV Sat B [m/s]', 'dV Sat C [m/s]', 'dV Sat D [m/s]']
    
    for i, (sat, col_name) in enumerate(zip(satellites, dv_columns)):
        ax1.plot(x, df[col_name], color=colors[i], marker='o', label=f'dV {sat}', linewidth=2)
    
    ax1.set_xlabel('SK Interval [days]')
    ax1.set_ylabel('Delta-V [m/s]', color='black')
    ax1.tick_params(axis='y', labelcolor='black')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    
    # Create secondary Y-axis for max displacement
    ax2 = ax1.twinx()
    ax2.plot(x, df['max deviation magnitude [m]'], color='purple', marker='s', 
             linewidth=2, markersize=8, label='Max Displacement')
    ax2.set_ylabel('Max Displacement [m]', color='purple')
    ax2.tick_params(axis='y', labelcolor='purple')
    ax2.legend(loc='upper right')
    
    # Set title and adjust layout
    plt.title('Pyramid SK Burns: Delta-V and Maximum Displacement vs SK Interval')
    plt.tight_layout()
    
    # Show the plot
    plt.show()

# Example usage
if __name__ == "__main__":
    plot_pyramid_sk_data('D:\\Max\\Uni\\03-SpaceSystems\\03-3. Semester\\Semesterarbeit\\code\\automation\\results\\pyramid-SK-burns-dv.csv')