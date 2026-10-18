"""
Visualization utilities for trajectory analysis.

This module provides plotting functions for:
- Time series plots of offset components
- 3D trajectory plots with projections
- Relative trajectory comparisons
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def title_to_filename(title, ext="png"):
    """
    Convert a plot title string to a valid Windows filename.
    
    Args:
        title: Plot title string
        ext: File extension (default: "png")
    
    Returns:
        str: Safe filename
    """
    s = (title or "").strip()
    # Replace invalid characters with underscores
    s = ''.join(c if c.isalnum() or c in (' ', '-', '_', '.') else '_' for c in s)
    # Collapse whitespace to single underscores
    s = '_'.join(s.split())
    # Trim leading/trailing dots/underscores
    s = s.strip('._')
    if not s:
        s = "plot"
    # Avoid Windows reserved device names
    reserved = {
        'CON','PRN','AUX','NUL',
        'COM1','COM2','COM3','COM4','COM5','COM6','COM7','COM8','COM9',
        'LPT1','LPT2','LPT3','LPT4','LPT5','LPT6','LPT7','LPT8','LPT9'
    }
    if s.upper() in reserved:
        s = f"_{s}"
    # Limit length
    s = s[:120]
    return f"{s}.{ext}"


def plot_delta_movement(times, offsets_dict, save_path=None,
                        colors=None, labels=None, plot_settings=None,
                        title=None):
    """
    Create 2×2 plots showing rate of change (Δx/Δt, Δy/Δt, Δz/Δt) and magnitude.
    
    Plots the velocity/movement delta of satellites relative to base satellite.
    This shows how fast the satellites are drifting apart in each direction.
    
    Args:
        times: Time array (epoch seconds)
        offsets_dict: Dict of {sat_name: offset_positions (N, 3)}
        save_path: Path to save figure
        colors: Dict of {sat_name: color}
        labels: Dict of {sat_name: display_label}
        plot_settings: Dict with plot customization settings
        title: Optional custom plot title (None to hide title)
    
    Returns:
        matplotlib.figure.Figure: The created figure
    """
    # Default settings
    if plot_settings is None:
        plot_settings = {
            'figsize': (16, 12),
            'dpi': 300,
            'linewidth': 2.0,
            'alpha': 0.8,
            'title_fontsize': 16,
            'subtitle_fontsize': 14,
            'label_fontsize': 14,
            'legend_fontsize': 11,
            'tick_fontsize': 12,
            'left': 0.08,
            'bottom': 0.08,
            'right': 0.98,
            'top': 0.93,
            'hspace': 0.30,
            'wspace': 0.25,
            'xlabel': 'Time (days)',
            'ylabel_delta': 'Movement Rate (km/day)',
        }
    
    # Convert times to days since start
    times_days = (times - times[0]) / 86400
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=plot_settings['figsize'])
    
    # Compute and plot deltas for each satellite
    for sat_name, offsets in offsets_dict.items():
        color = colors.get(sat_name, 'black') if colors else None
        label = labels.get(sat_name, sat_name) if labels else sat_name
        
        # Compute time differences (in days)
        dt = np.diff(times_days)
        dt = np.append(dt, dt[-1])  # Repeat last dt to maintain array size
        
        # Compute position differences (in km)
        dx = np.diff(offsets[:, 0])
        dy = np.diff(offsets[:, 1])
        dz = np.diff(offsets[:, 2])
        
        # Append last value to maintain size
        dx = np.append(dx, dx[-1])
        dy = np.append(dy, dy[-1])
        dz = np.append(dz, dz[-1])
        
        # Compute rates (km/day)
        dx_dt = dx / dt
        dy_dt = dy / dt
        dz_dt = dz / dt
        
        # Compute magnitude of velocity vector
        dmag_dt = np.sqrt(dx_dt**2 + dy_dt**2 + dz_dt**2)
        
        # Plot X component rate
        ax1.plot(times_days, dx_dt, 
                color=color, linewidth=plot_settings['linewidth'],
                alpha=plot_settings['alpha'], label=label)
        
        # Plot Y component rate
        ax2.plot(times_days, dy_dt,
                color=color, linewidth=plot_settings['linewidth'],
                alpha=plot_settings['alpha'], label=label)
        
        # Plot Z component rate
        ax3.plot(times_days, dz_dt,
                color=color, linewidth=plot_settings['linewidth'],
                alpha=plot_settings['alpha'], label=label)
        
        # Plot magnitude of movement rate
        ax4.plot(times_days, dmag_dt,
                color=color, linewidth=plot_settings['linewidth'],
                alpha=plot_settings['alpha'], label=label)
    
    # Format X delta subplot
    ax1.set_xlabel(plot_settings['xlabel'], fontsize=plot_settings['label_fontsize'])
    ax1.set_ylabel('ΔX/Δt ' + plot_settings.get('ylabel_delta', 'Movement Rate (km/day)'), 
                   fontsize=plot_settings['label_fontsize'])
    ax1.set_title('X-Component Movement Rate (Toward Sun)', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax1.legend(fontsize=plot_settings['legend_fontsize'])
    ax1.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='k', linewidth=0.5, alpha=0.5)
    
    # Format Y delta subplot
    ax2.set_xlabel(plot_settings['xlabel'], fontsize=plot_settings['label_fontsize'])
    ax2.set_ylabel('ΔY/Δt ' + plot_settings.get('ylabel_delta', 'Movement Rate (km/day)'), 
                   fontsize=plot_settings['label_fontsize'])
    ax2.set_title('Y-Component Movement Rate', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax2.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='k', linewidth=0.5, alpha=0.5)
    
    # Format Z delta subplot
    ax3.set_xlabel(plot_settings['xlabel'], fontsize=plot_settings['label_fontsize'])
    ax3.set_ylabel('ΔZ/Δt ' + plot_settings.get('ylabel_delta', 'Movement Rate (km/day)'), 
                   fontsize=plot_settings['label_fontsize'])
    ax3.set_title('Z-Component Movement Rate (Ecliptic North)', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax3.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax3.grid(True, alpha=0.3)
    ax3.axhline(y=0, color='k', linewidth=0.5, alpha=0.5)
    
    # Format magnitude subplot
    ax4.set_xlabel(plot_settings['xlabel'], fontsize=plot_settings['label_fontsize'])
    ax4.set_ylabel('|Δr|/Δt ' + plot_settings.get('ylabel_delta', 'Movement Rate (km/day)'), 
                   fontsize=plot_settings['label_fontsize'])
    ax4.set_title('Total Movement Rate Magnitude', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax4.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax4.grid(True, alpha=0.3)
    
    # Add title
    if title:
        plt.suptitle(f'{title}', 
                     fontsize=plot_settings['title_fontsize'], fontweight='bold', y=0.98)
    else:
        plt.suptitle('Satellite Movement Rates Relative to Base (SEM-L2 Frame)', 
                     fontsize=plot_settings['title_fontsize'], fontweight='bold', y=0.98)
    
    plt.subplots_adjust(
        left=plot_settings['left'],
        bottom=plot_settings['bottom'],
        right=plot_settings['right'],
        top=plot_settings['top'],
        hspace=plot_settings['hspace'],
        wspace=plot_settings['wspace']
    )
    
    if save_path:
        plt.savefig(save_path, dpi=plot_settings['dpi'], bbox_inches='tight')
        print(f"Saved delta movement plot to: {save_path}")
    
    return fig


def plot_offsets_vs_time(times, offsets_dict, save_path=None, 
                         colors=None, labels=None, plot_settings=None, 
                         log_scale=True, title=None):
    """
    Create 2×2 time series plots showing offset components and magnitude.
    
    Args:
        times: Time array (epoch seconds)
        offsets_dict: Dict of {sat_name: offset_positions (N, 3)}
        save_path: Path to save figure
        colors: Dict of {sat_name: color}
        labels: Dict of {sat_name: display_label}
        plot_settings: Dict with plot customization settings
        log_scale: If True, use logarithmic y-axis
        title: Optional custom plot title (None to hide title)
    
    Returns:
        matplotlib.figure.Figure: The created figure
    """
    # Default settings
    if plot_settings is None:
        plot_settings = {
            'figsize': (16, 12),
            'dpi': 300,
            'linewidth': 2.0,
            'alpha': 0.8,
            'title_fontsize': 16,
            'subtitle_fontsize': 14,
            'label_fontsize': 14,
            'legend_fontsize': 11,
            'tick_fontsize': 12,
            'left': 0.08,
            'bottom': 0.08,
            'right': 0.98,
            'top': 0.93,
            'hspace': 0.30,
            'wspace': 0.25,
            'xlabel': 'Time (days)',
            'ylabel_offset': 'Offset (km)',
        }
    
    # Convert times to days since start
    times_days = (times - times[0]) / 86400
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=plot_settings['figsize'])
    
    # Plot each satellite's offsets
    for sat_name, offsets in offsets_dict.items():
        color = colors.get(sat_name, 'black') if colors else None
        label = labels.get(sat_name, sat_name) if labels else sat_name
        
        if log_scale:
            # Use absolute values for log scale
            ax1.plot(times_days, np.abs(offsets[:, 0]), 
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], label=label)
            ax2.plot(times_days, np.abs(offsets[:, 1]),
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], label=label)
            ax3.plot(times_days, np.abs(offsets[:, 2]),
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], label=label)
        else:
            # Linear scale - can show negative values
            ax1.plot(times_days, offsets[:, 0], 
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], label=label)
            ax2.plot(times_days, offsets[:, 1],
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], label=label)
            ax3.plot(times_days, offsets[:, 2],
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], label=label)
        
        # Total magnitude (always positive)
        magnitude = np.linalg.norm(offsets, axis=1)
        ax4.plot(times_days, magnitude,
                color=color, linewidth=plot_settings['linewidth'],
                alpha=plot_settings['alpha'], label=label)
    
    # Y-axis label prefix
    ylabel_prefix = '|X|' if log_scale else 'X'
    ylabel_prefix_y = '|Y|' if log_scale else 'Y'
    ylabel_prefix_z = '|Z|' if log_scale else 'Z'
    
    # Format X offset subplot
    ax1.set_xlabel(plot_settings['xlabel'], fontsize=plot_settings['label_fontsize'])
    ax1.set_ylabel(f'{ylabel_prefix} ' + plot_settings['ylabel_offset'], fontsize=plot_settings['label_fontsize'])
    ax1.set_title('X-Component (Toward Sun)', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax1.legend(fontsize=plot_settings['legend_fontsize'])
    ax1.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax1.grid(True, alpha=0.3, which='both' if log_scale else 'major')
    if log_scale:
        ax1.set_yscale('log')
    else:
        ax1.axhline(y=0, color='k', linewidth=0.5, alpha=0.5)
    
    # Format Y offset subplot
    ax2.set_xlabel(plot_settings['xlabel'], fontsize=plot_settings['label_fontsize'])
    ax2.set_ylabel(f'{ylabel_prefix_y} ' + plot_settings['ylabel_offset'], fontsize=plot_settings['label_fontsize'])
    ax2.set_title('Y-Component', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax2.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax2.grid(True, alpha=0.3, which='both' if log_scale else 'major')
    if log_scale:
        ax2.set_yscale('log')
    else:
        ax2.axhline(y=0, color='k', linewidth=0.5, alpha=0.5)
    
    # Format Z offset subplot
    ax3.set_xlabel(plot_settings['xlabel'], fontsize=plot_settings['label_fontsize'])
    ax3.set_ylabel(f'{ylabel_prefix_z} ' + plot_settings['ylabel_offset'], fontsize=plot_settings['label_fontsize'])
    ax3.set_title('Z-Component (Ecliptic North)', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax3.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax3.grid(True, alpha=0.3, which='both' if log_scale else 'major')
    if log_scale:
        ax3.set_yscale('log')
    else:
        ax3.axhline(y=0, color='k', linewidth=0.5, alpha=0.5)
    
    # Format magnitude subplot
    ax4.set_xlabel(plot_settings['xlabel'], fontsize=plot_settings['label_fontsize'])
    ax4.set_ylabel('Magnitude ' + plot_settings['ylabel_offset'], fontsize=plot_settings['label_fontsize'])
    ax4.set_title('Total Offset Magnitude', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax4.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax4.grid(True, alpha=0.3, which='both' if log_scale else 'major')
    if log_scale:
        ax4.set_yscale('log')
    
    # Update title to indicate scale type
    scale_text = "(Log Scale)" if log_scale else "(Linear Scale)"
    if title:
        plt.suptitle(f'{title} {scale_text}', 
                     fontsize=plot_settings['title_fontsize'], fontweight='bold', y=0.98)
    else:
        plt.suptitle(f'Satellite Offsets Relative to Base (SEM-L2 Frame) {scale_text}', 
                     fontsize=plot_settings['title_fontsize'], fontweight='bold', y=0.98)
    
    plt.subplots_adjust(
        left=plot_settings['left'],
        bottom=plot_settings['bottom'],
        right=plot_settings['right'],
        top=plot_settings['top'],
        hspace=plot_settings['hspace'],
        wspace=plot_settings['wspace']
    )
    
    if save_path:
        plt.savefig(save_path, dpi=plot_settings['dpi'], bbox_inches='tight')
        print(f"Saved time series plot to: {save_path}")
    
    return fig


def plot_relative_trajectories_3d(offsets_dict, save_path=None,
                                   colors=None, labels=None, plot_settings=None, 
                                   log_scale=False, title=None,
                                   base_satellite_name="Base", base_color="#FF00FF"):
    """
    Plot 3D offset trajectories with projections.
    Origin (0,0,0) represents Base satellite position.
    
    Args:
        offsets_dict: Dict of {sat_name: offset_positions (N, 3)}
        save_path: Path to save figure
        colors: Dict of {sat_name: color}
        labels: Dict of {sat_name: display_label}
        plot_settings: Dict with plot customization settings
        log_scale: If True, use logarithmic axes for 2D projections
        title: Optional custom plot title (None to hide title)
        base_satellite_name: Name to use in legend for base satellite
        base_color: Color for base satellite marker
    
    Returns:
        matplotlib.figure.Figure: The created figure
    """
    # Default settings
    if plot_settings is None:
        plot_settings = {
            'figsize': (16, 12),
            'dpi': 300,
            'linewidth': 1.5,
            'alpha': 0.7,
            'title_fontsize': 16,
            'subtitle_fontsize': 14,
            'label_fontsize': 14,
            'legend_fontsize': 11,
            'tick_fontsize': 12,
            'label_fontsize_3d': 11,
            'tick_fontsize_3d': 10,
            'left': 0.07,
            'bottom': 0.07,
            'right': 0.994,
            'top': 0.92,
            'hspace': 0.24,
            'wspace': 0.25,
            'base_marker_size': 150,
            'base_marker_size_3d': 200,
        }
    
    fig = plt.figure(figsize=plot_settings['figsize'])
    
    # Create 4 subplots: 3D, XY, XZ, YZ
    ax1 = fig.add_subplot(221, projection='3d')
    ax2 = fig.add_subplot(222)  # XY plane
    ax3 = fig.add_subplot(223)  # XZ plane
    ax4 = fig.add_subplot(224)  # YZ plane
    
    # Plot each satellite's offset trajectory
    for sat_name, offsets in offsets_dict.items():
        color = colors.get(sat_name, 'black') if colors else None
        label = labels.get(sat_name, sat_name) if labels else sat_name
        
        # 3D plot (always linear - log scale not well supported in 3D)
        ax1.plot(offsets[:, 0], offsets[:, 1], offsets[:, 2],
                color=color, linewidth=plot_settings['linewidth'],
                alpha=plot_settings['alpha'], zorder=2)
        
        if log_scale:
            # Use absolute values for log scale projections
            ax2.plot(np.abs(offsets[:, 0]), np.abs(offsets[:, 1]),
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], label=label, zorder=2)
            ax3.plot(np.abs(offsets[:, 0]), np.abs(offsets[:, 2]),
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], zorder=2)
            ax4.plot(np.abs(offsets[:, 1]), np.abs(offsets[:, 2]),
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], zorder=2)
        else:
            # XY projection (labeled)
            ax2.plot(offsets[:, 0], offsets[:, 1],
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], label=label, zorder=2)
            # XZ projection
            ax3.plot(offsets[:, 0], offsets[:, 2],
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], zorder=2)
            # YZ projection
            ax4.plot(offsets[:, 1], offsets[:, 2],
                    color=color, linewidth=plot_settings['linewidth'],
                    alpha=plot_settings['alpha'], zorder=2)
    
    # Base satellite at origin (only labeled in XY plot)
    ax1.scatter([0], [0], [0], c=base_color, 
               s=plot_settings['base_marker_size_3d'],
               marker='o', edgecolors='black', linewidths=2, zorder=1000)
    
    if not log_scale:
        # Only show origin marker in linear scale
        ax2.scatter([0], [0], c=base_color,
                   s=plot_settings['base_marker_size'], marker='o',
                   label=base_satellite_name, edgecolors='black', linewidths=2, zorder=1000)
        ax3.scatter([0], [0], c=base_color,
                   s=plot_settings['base_marker_size'], marker='o',
                   edgecolors='black', linewidths=2, zorder=1000)
        ax4.scatter([0], [0], c=base_color,
                   s=plot_settings['base_marker_size'], marker='o',
                   edgecolors='black', linewidths=2, zorder=1000)
    
    # Format 3D plot
    ax1.set_xlabel('X Offset (km)\n← Toward Sun', fontsize=plot_settings['label_fontsize_3d'])
    ax1.set_ylabel('Y Offset (km)', fontsize=plot_settings['label_fontsize_3d'])
    ax1.set_zlabel('Z Offset (km)\nEcliptic North →', fontsize=plot_settings['label_fontsize_3d'])
    ax1.set_title('3D View', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax1.tick_params(labelsize=plot_settings['tick_fontsize_3d'])
    ax1.grid(True, alpha=0.3)
    
    # Set equal aspect ratio for 3D
    all_offsets = np.vstack(list(offsets_dict.values()))
    max_range = max(
        np.ptp(all_offsets[:, 0]),
        np.ptp(all_offsets[:, 1]),
        np.ptp(all_offsets[:, 2])
    ) / 2
    mid_x = np.mean([all_offsets[:, 0].min(), all_offsets[:, 0].max()])
    mid_y = np.mean([all_offsets[:, 1].min(), all_offsets[:, 1].max()])
    mid_z = np.mean([all_offsets[:, 2].min(), all_offsets[:, 2].max()])
    ax1.set_xlim(mid_x - max_range, mid_x + max_range)
    ax1.set_ylim(mid_y - max_range, mid_y + max_range)
    ax1.set_zlim(mid_z - max_range, mid_z + max_range)
    
    # Axis label prefixes for log/linear scale
    x_prefix = '|X|' if log_scale else 'X'
    y_prefix = '|Y|' if log_scale else 'Y'
    z_prefix = '|Z|' if log_scale else 'Z'
    
    # Format XY plot
    ax2.set_xlabel(f'{x_prefix} Offset (km) ← Toward Sun', fontsize=plot_settings['label_fontsize'])
    ax2.set_ylabel(f'{y_prefix} Offset (km)', fontsize=plot_settings['label_fontsize'])
    ax2.set_title('XY Plane (Ecliptic)', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax2.legend(fontsize=plot_settings['legend_fontsize'])
    ax2.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax2.grid(True, alpha=0.3, which='both' if log_scale else 'major')
    if log_scale:
        ax2.set_xscale('log')
        ax2.set_yscale('log')
    else:
        ax2.axis('equal')
        ax2.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
        ax2.axvline(x=0, color='k', linewidth=0.5, alpha=0.3)
    
    # Format XZ plot
    ax3.set_xlabel(f'{x_prefix} Offset (km) ← Toward Sun', fontsize=plot_settings['label_fontsize'])
    ax3.set_ylabel(f'{z_prefix} Offset (km) Ecliptic North →', fontsize=plot_settings['label_fontsize'])
    ax3.set_title('XZ Plane', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax3.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax3.grid(True, alpha=0.3, which='both' if log_scale else 'major')
    if log_scale:
        ax3.set_xscale('log')
        ax3.set_yscale('log')
    else:
        ax3.axis('equal')
        ax3.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
        ax3.axvline(x=0, color='k', linewidth=0.5, alpha=0.3)
    
    # Format YZ plot
    ax4.set_xlabel(f'{y_prefix} Offset (km)', fontsize=plot_settings['label_fontsize'])
    ax4.set_ylabel(f'{z_prefix} Offset (km) Ecliptic North →', fontsize=plot_settings['label_fontsize'])
    ax4.set_title('YZ Plane', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax4.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax4.grid(True, alpha=0.3, which='both' if log_scale else 'major')
    if log_scale:
        ax4.set_xscale('log')
        ax4.set_yscale('log')
    else:
        ax4.axis('equal')
        ax4.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
        ax4.axvline(x=0, color='k', linewidth=0.5, alpha=0.3)
    
    # Update title to indicate scale type
    scale_text = "(2D Projections: Log Scale)" if log_scale else "(Linear Scale)"
    if title:
        plt.suptitle(f'{title} {scale_text}', 
                     fontsize=plot_settings['title_fontsize'], fontweight='bold', y=0.98)
    else:
        plt.suptitle(f'Relative Trajectories (SEM-L2 Frame, Base at Origin) {scale_text}', 
                     fontsize=plot_settings['title_fontsize'], fontweight='bold', y=0.98)
    
    plt.subplots_adjust(
        left=plot_settings['left'],
        bottom=plot_settings['bottom'],
        right=plot_settings['right'],
        top=plot_settings['top'],
        hspace=plot_settings['hspace'],
        wspace=plot_settings['wspace']
    )
    
    if save_path:
        plt.savefig(save_path, dpi=plot_settings['dpi'], bbox_inches='tight')
        print(f"Saved 3D trajectory plot to: {save_path}")
    
    return fig


def plot_trajectories_3d(trajectories_dict, earth_pos=None, 
                         title="JWST Trajectories in SEM-L2 Frame", 
                         save_path=None,
                         colors=None,
                         labels=None,
                         plot_settings=None,
                         lock_scale_to_jwst=True):
    """
    Plot multiple trajectories in 3D with special handling for JWST reference trajectory.
    
    Args:
        trajectories_dict: Dict of {name: positions} where positions is (N, 3) array
        earth_pos: Earth position trajectory in SEM-L2 (N, 3) array
        title: Main plot title
        save_path: Path to save figure
        colors: Dict of {trajectory_name: color}
        labels: Dict of {trajectory_name: display_label}
        plot_settings: Dict with plot customization settings
        lock_scale_to_jwst: If True, scale axes based on JWST trajectory only
    
    Returns:
        matplotlib.figure.Figure: The created figure
    """
    # Default settings
    if plot_settings is None:
        plot_settings = {
            'figsize': (16, 12),
            'dpi': 300,
            'linewidth': 1.5,
            'alpha': 0.7,
            'jwst_linewidth': 8,
            'jwst_alpha': 0.3,
            'jwst_centerline_width': 1.0,
            'jwst_centerline_alpha': 0.8,
            'jwst_zorder': 1,
            'jwst_centerline_zorder': 3,
            'other_zorder': 2,
            'title_fontsize': 16,
            'subtitle_fontsize': 14,
            'label_fontsize': 14,
            'legend_fontsize': 11,
            'tick_fontsize': 12,
            'label_fontsize_3d': 11,
            'tick_fontsize_3d': 10,
            'left': 0.07,
            'bottom': 0.07,
            'right': 0.994,
            'top': 0.92,
            'hspace': 0.24,
            'wspace': 0.25,
            'l2_marker_size': 150,
            'l2_marker_size_3d': 200,
            'earth_marker_size': 100,
        }
    
    fig = plt.figure(figsize=plot_settings['figsize'])
    
    # Create 4 subplots: 3D, XY, XZ, YZ
    ax1 = fig.add_subplot(221, projection='3d')
    ax2 = fig.add_subplot(222)  # XY plane
    ax3 = fig.add_subplot(223)  # XZ plane
    ax4 = fig.add_subplot(224)  # YZ plane
    
    # If locking scale to JWST, compute bounds first
    if lock_scale_to_jwst and 'JWST' in trajectories_dict:
        jwst_pos = trajectories_dict['JWST']
        jwst_x = jwst_pos[:, 0] / 1e6
        jwst_y = jwst_pos[:, 1] / 1e6
        jwst_z = jwst_pos[:, 2] / 1e6
        
        # Include Earth position in bounds calculation for 3D
        all_x_3d = list(jwst_x)
        all_y_3d = list(jwst_y)
        all_z_3d = list(jwst_z)
        
        if earth_pos is not None:
            all_x_3d.append(earth_pos[0, 0] / 1e6)
            all_y_3d.append(earth_pos[0, 1] / 1e6)
            all_z_3d.append(earth_pos[0, 2] / 1e6)
        
        max_range_3d = max(
            max(all_x_3d) - min(all_x_3d),
            max(all_y_3d) - min(all_y_3d),
            max(all_z_3d) - min(all_z_3d)
        ) / 2
        
        mid_x_3d = (max(all_x_3d) + min(all_x_3d)) / 2
        mid_y_3d = (max(all_y_3d) + min(all_y_3d)) / 2
        mid_z_3d = (max(all_z_3d) + min(all_z_3d)) / 2
        
        # 2D scales (in 1000 km)
        jwst_x_2d = jwst_pos[:, 0] / 1000
        jwst_y_2d = jwst_pos[:, 1] / 1000
        jwst_z_2d = jwst_pos[:, 2] / 1000
        
        all_x_xy = list(jwst_x_2d)
        all_y_xy = list(jwst_y_2d)
        all_x_xz = list(jwst_x_2d)
        all_z_xz = list(jwst_z_2d)
        all_y_yz = list(jwst_y_2d)
        all_z_yz = list(jwst_z_2d)
        
        if earth_pos is not None:
            all_x_xy.append(earth_pos[0, 0] / 1000)
            all_y_xy.append(earth_pos[0, 1] / 1000)
            all_x_xz.append(earth_pos[0, 0] / 1000)
            all_z_xz.append(earth_pos[0, 2] / 1000)
            all_y_yz.append(earth_pos[0, 1] / 1000)
            all_z_yz.append(earth_pos[0, 2] / 1000)
        
        max_range_xy = max(
            max(all_x_xy) - min(all_x_xy),
            max(all_y_xy) - min(all_y_xy)
        ) / 2
        mid_x_xy = (max(all_x_xy) + min(all_x_xy)) / 2
        mid_y_xy = (max(all_y_xy) + min(all_y_xy)) / 2
        
        max_range_xz = max(
            max(all_x_xz) - min(all_x_xz),
            max(all_z_xz) - min(all_z_xz)
        ) / 2
        mid_x_xz = (max(all_x_xz) + min(all_x_xz)) / 2
        mid_z_xz = (max(all_z_xz) + min(all_z_xz)) / 2
        
        max_range_yz = max(
            max(all_y_yz) - min(all_y_yz),
            max(all_z_yz) - min(all_z_yz)
        ) / 2
        mid_y_yz = (max(all_y_yz) + min(all_y_yz)) / 2
        mid_z_yz = (max(all_z_yz) + min(all_z_yz)) / 2
    
    # Plot JWST first as thick transparent background (if present)
    if 'JWST' in trajectories_dict:
        pos = trajectories_dict['JWST']
        color = colors.get('JWST', 'black') if colors else 'black'
        label = labels.get('JWST', 'JWST') if labels else 'JWST'
        
        # 3D plot - thick transparent highlight
        ax1.plot(pos[:, 0]/1e6, pos[:, 1]/1e6, pos[:, 2]/1e6, 
                color=color, alpha=plot_settings['jwst_alpha'], 
                linewidth=plot_settings['jwst_linewidth'],
                solid_capstyle='round',
                zorder=plot_settings['jwst_zorder'])
        
        # 2D projections - thick transparent highlight
        ax2.plot(pos[:, 0]/1000, pos[:, 1]/1000, label=label, color=color, 
                alpha=plot_settings['jwst_alpha'], 
                linewidth=plot_settings['jwst_linewidth'],
                solid_capstyle='round',
                zorder=plot_settings['jwst_zorder'])
        ax3.plot(pos[:, 0]/1000, pos[:, 2]/1000, color=color, 
                alpha=plot_settings['jwst_alpha'], 
                linewidth=plot_settings['jwst_linewidth'],
                solid_capstyle='round',
                zorder=plot_settings['jwst_zorder'])
        ax4.plot(pos[:, 1]/1000, pos[:, 2]/1000, color=color, 
                alpha=plot_settings['jwst_alpha'], 
                linewidth=plot_settings['jwst_linewidth'],
                solid_capstyle='round',
                zorder=plot_settings['jwst_zorder'])
    
    # Plot other trajectories on top
    for name, pos in trajectories_dict.items():
        if name == 'JWST':
            continue  # Already plotted (will add centerline later)
            
        color = colors.get(name, 'black') if colors else None
        label = labels.get(name, name) if labels else name
        
        # 3D plot
        ax1.plot(pos[:, 0]/1e6, pos[:, 1]/1e6, pos[:, 2]/1e6, 
                color=color, alpha=plot_settings['alpha'], 
                linewidth=plot_settings['linewidth'],
                zorder=plot_settings['other_zorder'])
        
        # 2D projections (only XY gets labels)
        ax2.plot(pos[:, 0]/1000, pos[:, 1]/1000, label=label, color=color, 
                alpha=plot_settings['alpha'], 
                linewidth=plot_settings['linewidth'],
                zorder=plot_settings['other_zorder'])
        ax3.plot(pos[:, 0]/1000, pos[:, 2]/1000, color=color, 
                alpha=plot_settings['alpha'], 
                linewidth=plot_settings['linewidth'],
                zorder=plot_settings['other_zorder'])
        ax4.plot(pos[:, 1]/1000, pos[:, 2]/1000, color=color, 
                alpha=plot_settings['alpha'], 
                linewidth=plot_settings['linewidth'],
                zorder=plot_settings['other_zorder'])
    
    # Plot JWST centerline on top (if present)
    if 'JWST' in trajectories_dict:
        pos = trajectories_dict['JWST']
        color = colors.get('JWST', 'black') if colors else 'black'
        
        # 3D plot - thin centerline
        ax1.plot(pos[:, 0]/1e6, pos[:, 1]/1e6, pos[:, 2]/1e6, 
                color=color, alpha=plot_settings['jwst_centerline_alpha'], 
                linewidth=plot_settings['jwst_centerline_width'],
                solid_capstyle='round',
                zorder=plot_settings['jwst_centerline_zorder'])
        
        # 2D projections - thin centerline
        ax2.plot(pos[:, 0]/1000, pos[:, 1]/1000, color=color, 
                alpha=plot_settings['jwst_centerline_alpha'], 
                linewidth=plot_settings['jwst_centerline_width'],
                solid_capstyle='round',
                zorder=plot_settings['jwst_centerline_zorder'])
        ax3.plot(pos[:, 0]/1000, pos[:, 2]/1000, color=color, 
                alpha=plot_settings['jwst_centerline_alpha'], 
                linewidth=plot_settings['jwst_centerline_width'],
                solid_capstyle='round',
                zorder=plot_settings['jwst_centerline_zorder'])
        ax4.plot(pos[:, 1]/1000, pos[:, 2]/1000, color=color, 
                alpha=plot_settings['jwst_centerline_alpha'], 
                linewidth=plot_settings['jwst_centerline_width'],
                solid_capstyle='round',
                zorder=plot_settings['jwst_centerline_zorder'])
    
    # L2 at origin (only labeled in XY plot)
    ax1.scatter([0], [0], [0], c='gold', s=plot_settings['l2_marker_size_3d'], 
               marker='*', edgecolors='orange', linewidths=2, zorder=1000)
    ax2.scatter([0], [0], c='gold', s=plot_settings['l2_marker_size'], marker='*', 
               label='L2', edgecolors='orange', linewidths=2, zorder=1000)
    ax3.scatter([0], [0], c='gold', s=plot_settings['l2_marker_size'], marker='*', 
               edgecolors='orange', linewidths=2, zorder=1000)
    ax4.scatter([0], [0], c='gold', s=plot_settings['l2_marker_size'], marker='*', 
               edgecolors='orange', linewidths=2, zorder=1000)
    
    # Earth position (if provided)
    if earth_pos is not None:
        ax1.scatter([earth_pos[0, 0]/1e6], [earth_pos[0, 1]/1e6], [earth_pos[0, 2]/1e6],
                   c='darkblue', s=plot_settings['earth_marker_size'], marker='o', 
                   edgecolors='blue', linewidths=2, zorder=900)
        ax2.scatter([earth_pos[0, 0]/1000], [earth_pos[0, 1]/1000],
                   c='darkblue', s=plot_settings['earth_marker_size'], marker='o', 
                   label='Earth', edgecolors='blue', linewidths=2, zorder=900)
        ax3.scatter([earth_pos[0, 0]/1000], [earth_pos[0, 2]/1000],
                   c='darkblue', s=plot_settings['earth_marker_size'], marker='o', 
                   edgecolors='blue', linewidths=2, zorder=900)
        ax4.scatter([earth_pos[0, 1]/1000], [earth_pos[0, 2]/1000],
                   c='darkblue', s=plot_settings['earth_marker_size'], marker='o', 
                   edgecolors='blue', linewidths=2, zorder=900)
    
    # Format 3D plot
    ax1.set_xlabel('X (10⁶ km)\n← Toward Sun', fontsize=plot_settings['label_fontsize_3d'])
    ax1.set_ylabel('Y (10⁶ km)', fontsize=plot_settings['label_fontsize_3d'])
    ax1.set_zlabel('Z (10⁶ km)\nEcliptic North →', fontsize=plot_settings['label_fontsize_3d'])
    ax1.set_title('3D View', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax1.tick_params(labelsize=plot_settings['tick_fontsize_3d'])
    ax1.grid(True, alpha=0.3)
    
    # Set axis limits
    if lock_scale_to_jwst and 'JWST' in trajectories_dict:
        ax1.set_xlim(mid_x_3d - max_range_3d, mid_x_3d + max_range_3d)
        ax1.set_ylim(mid_y_3d - max_range_3d, mid_y_3d + max_range_3d)
        ax1.set_zlim(mid_z_3d - max_range_3d, mid_z_3d + max_range_3d)
        
        ax2.set_xlim(mid_x_xy - max_range_xy, mid_x_xy + max_range_xy)
        ax2.set_ylim(mid_y_xy - max_range_xy, mid_y_xy + max_range_xy)
        
        ax3.set_xlim(mid_x_xz - max_range_xz, mid_x_xz + max_range_xz)
        ax3.set_ylim(mid_z_xz - max_range_xz, mid_z_xz + max_range_xz)
        
        ax4.set_xlim(mid_y_yz - max_range_yz, mid_y_yz + max_range_yz)
        ax4.set_ylim(mid_z_yz - max_range_yz, mid_z_yz + max_range_yz)
    
    # Format XY plot
    ax2.set_xlabel('X (1000 km) ← Toward Sun', fontsize=plot_settings['label_fontsize'])
    ax2.set_ylabel('Y (1000 km)', fontsize=plot_settings['label_fontsize'])
    ax2.set_title('XY Plane (Ecliptic)', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax2.legend(fontsize=plot_settings['legend_fontsize'])
    ax2.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
    ax2.axvline(x=0, color='k', linewidth=0.5, alpha=0.3)
    ax2.axis('equal')
    if lock_scale_to_jwst and 'JWST' in trajectories_dict:
        ax2.set_xlim(mid_x_xy - max_range_xy, mid_x_xy + max_range_xy)
        ax2.set_ylim(mid_y_xy - max_range_xy, mid_y_xy + max_range_xy)
    
    # Format XZ plot
    ax3.set_xlabel('X (1000 km) ← Toward Sun', fontsize=plot_settings['label_fontsize'])
    ax3.set_ylabel('Z (1000 km) Ecliptic North →', fontsize=plot_settings['label_fontsize'])
    ax3.set_title('XZ Plane', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax3.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax3.grid(True, alpha=0.3)
    ax3.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
    ax3.axvline(x=0, color='k', linewidth=0.5, alpha=0.3)
    ax3.axis('equal')
    if lock_scale_to_jwst and 'JWST' in trajectories_dict:
        ax3.set_xlim(mid_x_xz - max_range_xz, mid_x_xz + max_range_xz)
        ax3.set_ylim(mid_z_xz - max_range_xz, mid_z_xz + max_range_xz)
    
    # Format YZ plot
    ax4.set_xlabel('Y (1000 km)', fontsize=plot_settings['label_fontsize'])
    ax4.set_ylabel('Z (1000 km) Ecliptic North →', fontsize=plot_settings['label_fontsize'])
    ax4.set_title('YZ Plane', fontsize=plot_settings['subtitle_fontsize'], fontweight='bold')
    ax4.tick_params(labelsize=plot_settings['tick_fontsize'])
    ax4.grid(True, alpha=0.3)
    ax4.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
    ax4.axvline(x=0, color='k', linewidth=0.5, alpha=0.3)
    ax4.axis('equal')
    if lock_scale_to_jwst and 'JWST' in trajectories_dict:
        ax4.set_xlim(mid_y_yz - max_range_yz, mid_y_yz + max_range_yz)
        ax4.set_ylim(mid_z_yz - max_range_yz, mid_z_yz + max_range_yz)
    
    # Add title if provided
    if title is not None and str(title).strip():
        plt.suptitle(title, fontsize=plot_settings['title_fontsize'], fontweight='bold', y=0.98)
    
    # Set custom subplot spacing
    plt.subplots_adjust(
        left=plot_settings['left'], 
        bottom=plot_settings['bottom'], 
        right=plot_settings['right'], 
        top=plot_settings['top'], 
        hspace=plot_settings['hspace'], 
        wspace=plot_settings['wspace']
    )
    
    if save_path:
        plt.savefig(save_path, dpi=plot_settings['dpi'], bbox_inches='tight')
        print(f"Figure saved to {save_path}")
    
    return fig
