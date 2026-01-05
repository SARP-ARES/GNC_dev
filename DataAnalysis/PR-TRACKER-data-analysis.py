import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime

# Haversine distance (meters) between successive GPS points
def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    lat1_r = np.radians(lat1)
    lat2_r = np.radians(lat2)
    dlat = lat2_r - lat1_r
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

# Load the test launch CSV as a pandas DataFrame
data = pd.read_csv('data/PR-Tracker_05-24-2025_14_21_22.csv')

print(data.head())

# TRACKER,DATE,TIME,GS Lat,GS Lon,GS Alt asl,TRACKER Lat,TRACKER Lon,TRACKER Alt asl,FIX,HORZV,VERTV,HEAD,FLAGS,#TOT,>40,>32,>24,RSSI Down,RSSI Up,Horizontal range (ft),Alt AGL (ft),Total range (ft),LoRa Max Range (kft),LoRa Success Rate,BATT,GS_batt_v,Down Sent,Down Rcvd,Found Sent,Up Sent,Up Rccvd,Found rocket ID,Found rocket lat,Found rocket lon,Found rocket altitude,Found rocket fix,Found rocket batt_v,Found RSSI,GS_ASL_offset

# Remove garbage data: keep only rows where TIME is after the first non-negative altitude and altitude is non-negative
# Also exclude rows where lat or lon are zero
first_valid_idx = data[data['Alt AGL (ft)'] >= 0].index[0]
cleaned_data = data.loc[first_valid_idx:]
cleaned_data = cleaned_data[(cleaned_data['Alt AGL (ft)'] >= 0) &
                            (cleaned_data['TRACKER Lat'] != 0) &
                            (cleaned_data['TRACKER Lon'] != 0)]

# Convert TIME (hh:mm:ss.sss) to seconds since apogee
def time_to_seconds(tstr):
    # Handles both 'hh:mm:ss.sss' and 'h:mm:ss.sss'
    try:
        dt = datetime.strptime(tstr, '%H:%M:%S.%f')
    except ValueError:
        dt = datetime.strptime(tstr, '%H:%M:%S')
    return dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1e6

# Compute seconds for all rows
cleaned_data = cleaned_data.copy()
cleaned_data['time_in_seconds'] = cleaned_data['TIME'].apply(time_to_seconds)

# Find apogee (max altitude)
apogee_idx = cleaned_data['Alt AGL (ft)'].idxmax()
apogee_time = cleaned_data.loc[apogee_idx, 'time_in_seconds']

cleaned_data['ctrl_time_seconds'] = cleaned_data['time_in_seconds'] - (apogee_time + 20)

# 2D Trajectory Plot on a Map using Plotly Express
fig2d = px.scatter_mapbox(
    cleaned_data,
    lat='TRACKER Lat',
    lon='TRACKER Lon',
    color='Alt AGL (ft)',
    color_continuous_scale='Viridis',
    zoom=12,
    height=500,
    title='2D Trajectory on Map'
)
fig2d.update_layout(mapbox_style="open-street-map")
fig2d.show()

# Ensure cleaned data is sorted by time
sorted_data = cleaned_data.sort_values(by='TIME')
# Convert lat/lon to local East/North distances (ft) from the starting position
R = 6371000.0
start_lat = np.radians(sorted_data['TRACKER Lat'].iloc[0])
start_lon = np.radians(sorted_data['TRACKER Lon'].iloc[0])
lat_r = np.radians(sorted_data['TRACKER Lat'].astype(float))
lon_r = np.radians(sorted_data['TRACKER Lon'].astype(float))

# Differences in radians
dlat = lat_r - start_lat
dlon = lon_r - start_lon

# Local tangent-plane approximation
east_m = R * dlon * np.cos((lat_r + start_lat) / 2.0)
north_m = R * dlat

# Convert to feet
east_ft = east_m * 3.28084
north_ft = north_m * 3.28084

# 3D Trajectory Plot using Plotly Graph Objects with time in hover
fig3d = go.Figure(data=[go.Scatter3d(
    x=east_ft,
    y=north_ft,
    z=sorted_data['Alt AGL (ft)'],
    mode='markers+lines',
    marker=dict(
        size=5,
        color=sorted_data['Alt AGL (ft)'],
        colorscale='Viridis',
        colorbar=dict(title='Altitude (AGL, ft)'),
        cmin=sorted_data['Alt AGL (ft)'].min(),
        cmax=sorted_data['Alt AGL (ft)'].max()
    ),
    line=dict(width=2),
    name='Trajectory',
    text=sorted_data['ctrl_time_seconds'],
    hovertemplate='Ctrl Sequence Time (s): %{text}<br>East (ft): %{x:.1f}<br>North (ft): %{y:.1f}<br>Alt(ft): %{z}<extra></extra>'
)])
fig3d.update_layout(
    title='3D Trajectory',
    scene=dict(
        xaxis_title='East (ft)',
        yaxis_title='North (ft)',
        zaxis_title='Altitude (AGL, ft)',
        aspectmode='data'
    ),
)
fig3d.show()

# --- Compute descent rate and forward (horizontal) speed, then plot ---
df = sorted_data.copy()

# Convert altitude from feet to meters and ensure time is numeric
df['alt_m'] = df['Alt AGL (ft)'] * 0.3048
df['time_s'] = df['time_in_seconds']

# Sort by time and compute differences
df = df.sort_values('time_s').reset_index(drop=True)
df['dt'] = df['time_s'].diff()
df['dalt'] = df['alt_m'].diff()

# Descent rate in m/s (positive when descending)
df['descent_rate_m_s'] = -df['dalt'] / df['dt']
df['descent_rate_m_s'] = df['descent_rate_m_s'].replace([np.inf, -np.inf], np.nan).fillna(0)

# Compute distance moved between rows and forward speed (m/s)
lat_prev = df['TRACKER Lat'].shift()
lon_prev = df['TRACKER Lon'].shift()
df['dist_m'] = haversine_m(lat_prev, lon_prev, df['TRACKER Lat'], df['TRACKER Lon'])
df['dist_m'] = df['dist_m'].fillna(0)
df['speed_m_s'] = df['dist_m'] / df['dt']
df['speed_m_s'] = df['speed_m_s'].replace([np.inf, -np.inf], np.nan).fillna(0)

# Smooth signals with a small rolling window
df['descent_rate_smooth'] = df['descent_rate_m_s'].rolling(window=5, min_periods=1, center=True).mean()
df['speed_smooth'] = df['speed_m_s'].rolling(window=5, min_periods=1, center=True).mean()

# calculate glide slope (ratio of forward speed to descent rate)
df['glide_slope'] = df['speed_smooth'] / df['descent_rate_smooth']

# Only plot data where ctrl_time_seconds >= 0 and <= 355
df_plot = df[(df['ctrl_time_seconds'] >= 0) & (df['ctrl_time_seconds'] <= 355)].copy()

# Plot descent rate and forward speed using matplotlib and save to figs/
import os
os.makedirs('figs', exist_ok=True)

fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
axes[0].plot(df_plot['ctrl_time_seconds'], df_plot['descent_rate_smooth'], label='Descent rate (m/s)')
axes[0].set_ylabel('Descent rate (m/s)')
axes[0].grid(True)
axes[0].legend()

axes[1].plot(df_plot['ctrl_time_seconds'], df_plot['speed_smooth'], color='orange', label='Forward speed (m/s)')
axes[1].set_ylabel('Forward speed (m/s)')
axes[1].grid(True)
axes[1].legend()

axes[2].plot(df_plot['ctrl_time_seconds'], df_plot['glide_slope'], color='magenta',label='Glide Slope')
axes[2].set_xlabel('Ctrl Time (s)')
axes[2].set_ylabel('Glide Slope')
axes[2].grid(True)
axes[2].legend()

plt.suptitle('Descent Rate, Fwd Speed, and Glide Slope')
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
outpath = os.path.join('figs', 'glide_slope.png')
plt.savefig(outpath, dpi=200)
print(f"Saved descent and forward speed plot to {outpath}")
plt.show()
