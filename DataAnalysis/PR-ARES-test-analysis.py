import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

# Load the test launch CSV as a pandas DataFrame
data = pd.read_csv('DataAnalysis/data/PocketRocket_ARES_Flight_5-24-2025.csv')

# Start at zero seconds and zero altitude (AGL)
data['timestamp_utc'] = data['timestamp_utc'] - data['timestamp_utc'][0] 
data['altitude_m'] = data['altitude_m'] - data['altitude_m'][0]

# Normalize GPS and barometric altitudes to start at zero
data['altitude_gps_m_AGL'] = data['altitude_gps_m'] - data['altitude_gps_m'][0]
data['altitude_bmp_m_AGL'] = data['altitude_bmp_m'] - data['altitude_bmp_m'][0]

print(f"Lat Lon: {data['latitude_deg'][0]}, {data['longitude_deg'][0]}")
print(f"Apogee Altitude: {data['altitude_m'].max()} m")

def moving_average_same_length(data, window_size):
    # Pad data symmetrically at both ends
    pad_size = window_size // 2
    padded = np.pad(data, (pad_size, pad_size), mode='reflect')
    
    # Apply convolution with a uniform window
    weights = np.ones(window_size) / window_size
    smoothed = np.convolve(padded, weights, mode='valid')
    
    return smoothed

data['smoothed_altitude'] = moving_average_same_length(data['altitude_m'], window_size=5)


## Make Altitude Plot with Events
plt.figure()
# plt.plot(data['timestamp_utc'], data['altitude_m'], 'b-', label='Altitude')
plt.plot(data['timestamp_utc'], data['smoothed_altitude'], 'b-', label='Smoothed Altitude')


# Identify key events
launch_time = data['timestamp_utc'][data['altitude_m'] > data['altitude_m'][0] + 10].iloc[0]  # First non-zero altitude
apogee_time = data['timestamp_utc'][data['altitude_m'].idxmax()]    # Time of maximum altitude
apogee_detected_time = data['timestamp_utc'][data['fsm_mode'] == 1].iloc[0]
time_ctrl = data['timestamp_utc'] - (apogee_detected_time + 20)

# Calculate descent rate (negative of altitude derivative)
descent_rate = -data['smoothed_altitude'].diff()
descent_rate_noisy = -data['altitude_m'].diff()
main_deployment = data['timestamp_utc'][(descent_rate < 12) & (data['apogee_detected'] == 1)].iloc[0]  # First instance of descent rate change
grounded_time = data['timestamp_utc'][(descent_rate < 1) & (data['apogee_detected'] == 1)].iloc[0]  # First instance of ground contact

# Plot altitude graph with vertical lines
plt.vlines(launch_time, ymin=data['altitude_m'].min(), ymax=data['altitude_m'].max(), color='r', linestyle='--', label=f'Launch ({int(launch_time)}s)')
plt.vlines(apogee_time, ymin=data['altitude_m'].min(), ymax=data['altitude_m'].max(), color='orange', linestyle='--', label=f'Apogee ({int(apogee_time)}s)')
plt.vlines(apogee_detected_time, ymin=data['altitude_m'].min(), ymax=data['altitude_m'].max(), color='gold', linestyle='--', label=f'Apogee Detected ({int(apogee_detected_time)}s)')

# Add labels and legend
plt.xlabel('Time (s)')
plt.ylabel('Altitude (m)')
plt.legend()
plt.grid()
plt.title('Altitude vs Time with Key Events')


## Make Descent Rate Plot
plt.figure()
descent_times = data
plt.plot(data['timestamp_utc'][data['timestamp_utc'] > apogee_time], descent_rate[data['timestamp_utc'] > apogee_time], 'b-', label='Descent Rate')
# ymin, ymax = plt.ylim()
# plt.yticks(np.arange(np.floor(ymin), np.ceil(ymax)+1, 20))  # Tick every 2 units
plt.grid()
plt.title('Descent Rate vs Time')
plt.xlabel('Time (s)')
plt.ylabel('Descent Rate (m/s)')


## Make Heading Plot
plt.figure()
unwrapped_heading = np.unwrap(np.deg2rad(data['heading_deg']))
plt.plot(data['timestamp_utc'], unwrapped_heading, 'b-', label='Heading')
plt.xlabel('Time (s)')
plt.ylabel('Heading (degrees)')
plt.title('Heading vs Time')
plt.grid()


## Compare GPS vs Barometric Altitude (Unfiltered)
plt.figure()
plt.plot(data['timestamp_utc'][data['altitude_bmp_m_AGL'] > 0], data['altitude_gps_m_AGL'][data['altitude_bmp_m_AGL'] > 0], 'b-', label='GPS Altitude', linewidth=1.5)
plt.plot(data['timestamp_utc'][data['altitude_bmp_m_AGL'] > 0], data['altitude_bmp_m_AGL'][data['altitude_bmp_m_AGL'] > 0], 'r-', label='Barometric Altitude', linewidth=1.5)
plt.xlabel('Time (s)')
plt.ylabel('Altitude (m)')
plt.title('GPS vs Barometric Altitude (Unfiltered)')
plt.legend()
plt.grid()


# Extract lat, lon, alt from the DataFrame
latitudes = data['latitude_deg'].tolist()
longitudes = data['longitude_deg'].tolist()
altitudes = data['altitude_m'].tolist()

# Create the 3D scatter plot
fig = go.Figure(data=[go.Scatter3d(
    x=longitudes,
    y=latitudes,
    z=altitudes,
    mode='markers+lines',  # Show both markers and lines
    marker=dict(
        size=5,
        color=altitudes,  # Color points by altitude
        colorscale='Viridis'  # Choose a colorscale
    ),
    line=dict(
        width=2
    ),
    text=time_ctrl,
    hovertemplate='Ctrl Sequence Time (s): %{text}'
)])

# Update layout for better visualization
fig.update_layout(
    title='3D Trajectory',
    # scene=dict(
    #     xaxis_title='Longitude',
    #     yaxis_title='Latitude',
    #     zaxis_title='Altitude (m)',
    #     aspectmode='auto' # automatically adjusts axes to data range
    # ),
    margin=dict(l=0, r=0, b=0, t=40)
)

fig.show()
plt.show()


