from GPS import GPS, State, PositionECEFr, PositionLTP
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# Load the test launch (brothers) CSV as a pandas DataFrame
data = pd.read_csv('DataAnalysis/data/PocketRocket_ARES_Flight_5-24-2025.csv')

# Start at zero seconds
data['timestamp_utc'] = data['timestamp_utc'] - data['timestamp_utc'][0]

print(f"Lat Lon: {data['latitude_deg'][0]}, {data['longitude_deg'][0]}")


# initialize GPS and set origin
lat_start = data['latitude_deg'][0]
lon_start = data['longitude_deg'][0]
alt_start = data['altitude_m'][0]
state = State(lat=lat_start, lon=lon_start, alt=alt_start)
origin = PositionECEFr()
pos = PositionLTP()
gps = GPS(state, origin, pos)
gps.setOriginECEFr()

east_list = []
north_list = []
up_list = []

plt.figure()

# loop through the position at each time step of the test flight data
for i in range(len(data)):
    lat = data['latitude_deg'][i]
    lon = data['longitude_deg'][i]
    alt = data['altitude_m'][i] 

    # update state with lat, lon, alt
    gps.state = State(lat=lat, lon=lon, alt=alt)
    gps.updatePosLTP()  # Update LTP position based on new state
    
    east_list.append(gps.posLTP.e)
    north_list.append(gps.posLTP.n)
    up_list.append(gps.posLTP.u)
    
    plt.scatter(gps.posLTP.e, gps.posLTP.n, c='blue', s=1)  # Plot LTP position

plt.axis('equal')
plt.xlabel('East (m)')
plt.ylabel('North (m)')

#3D Trajectory Plot using Plotly
fig3d = go.Figure(data=[go.Scatter3d(
    x=east_list,
    y=north_list,
    z=up_list,
    mode='markers',
    marker=dict(size=3, color='blue', opacity=0.8)
)])

fig3d.update_layout(
    scene=dict(
        xaxis_title='East (m)',
        yaxis_title='North (m)',
        zaxis_title='Up (m)'
    ),
    title='3D Trajectory (East-North-Up)'
)
fig3d.show()

plt.show()