import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime


# Load the test launch CSV as a pandas DataFrame
data = pd.read_csv('DataAnalysis/data/PR-Tracker_05-24-2025_14_21_22.csv')


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

# 3D Trajectory Plot using Plotly Graph Objects with time in hover
fig3d = go.Figure(data=[go.Scatter3d(
    x=sorted_data['TRACKER Lon'],
    y=sorted_data['TRACKER Lat'],
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
    hovertemplate='Ctrl Sequence Time (s): %{text}<br>Lat: %{y}<br>Lon: %{x}<br>Alt(ft): %{z}<extra></extra>'
)])
fig3d.update_layout(
    title='3D Trajectory',
    scene=dict(
        xaxis_title='Longitude',
        yaxis_title='Latitude',
        zaxis_title='Altitude (AGL, ft)',
        aspectmode='auto'
    ),
)
fig3d.show()
