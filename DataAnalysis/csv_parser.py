import pandas as pd
from matplotlib import pyplot as plt
from enum import Enum
import io
import re
from shapely.geometry import LineString
import geopandas as gpd
import contextily as cx

FILE_PATH = 'data/ARES_CarTest/PASCO-LAUNCH-3-7-CLEAN.csv'

# MOTOR_POS_COEFICENT = 1.2
MAX_DEFLECTION = 30

class FlightAnalyzer():

  class FSM_MODE(Enum):
     IDLE     = 1
     SEEKING  = 2
     SPIRAL   = 3
  
  def __init__(self, flight_data_file_path):
    self.df = self.parse_rocket_log(flight_data_file_path)
  
  def plot(self):
     self.motor_analysis()
     self.state_analysis()
     self.control_analysis()
     plt.show()


  def parse_rocket_log(self, file_path):
    # 1. Read the lines and strip the [HH:MM:SS] prefix
    # We use a regex to replace '[XX:XX:XX] ' with nothing
    clean_lines = []
    with open(file_path, 'r') as f:
        for line in f:
            # Matches '[any digits:any digits:any digits] '
            clean_line = re.sub(r'^\[\d{2}:\d{2}:\d{2}\]\s*', '', line)
            clean_lines.append(clean_line)
    
    # 2. Convert the list of strings into a single string buffer
    csv_data = io.StringIO("".join(clean_lines))
    
    # 3. Load into Pandas
    # index_col=False ensures it doesn't try to use the first col as index
    df = pd.read_csv(csv_data, index_col=False)
    
    # 4. Data Cleanup
    # Remove the last empty column (caused by trailing commas)
    if 'Unnamed:' in df.columns[-1] or df.columns[-1] == '':
        df = df.iloc[:, :-1]
        
    # Strip any whitespace from column names
    df.columns = df.columns.str.strip()
    
    return df

  def motor_analysis(self):
    timestamps = self.df['timestamp_timer']
    cmd_deflection = self.df['fc_cmd']
    left_pos_measured = self.df['leftPosition']
    right_pos_measured = self.df['rightPosition']
    left_pos_cmd = self.df['leftPull']
    right_pos_cmd = self.df['rightPull']

    def fc_cmd_axis(ax):
      fc_color='green'
      fc_cmd_ax = ax.twinx()
      fc_cmd_ax.set_ylabel('FC Command', color=fc_color)
      fc_cmd_ax.plot(timestamps, cmd_deflection, color=fc_color, linestyle='--', label='Flight Computer Command')
      fc_cmd_ax.tick_params(axis='y', labelcolor=fc_color)
      fc_cmd_ax.legend()

    fig, (pull_ax, pos_ax) = plt.subplots(2, figsize=(10,6))

    pull_ax.set_title('Control Distributor -- delta_a and motor commands')
    pull_ax.set_xlabel('Time (s)')
    pull_ax.set_ylabel('Commanded Position (in)')
    pull_ax.plot(timestamps, left_pos_cmd, color='blue', linestyle='-', label='Left Command')
    pull_ax.plot(timestamps, right_pos_cmd, color='red', linestyle='-', label='Right Command')
    pull_ax.tick_params(axis='y', labelcolor='blue')
    pull_ax.legend()
    # Add the FC command on the same plot but with a different y-axis
    fc_cmd_axis(pull_ax)

    fig.tight_layout()

    fig, (left_ax, right_ax) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # Top subplot: Left motor
    left_ax.set_title('Left Motor - Commanded vs. Measured Position')
    left_ax.set_ylabel('Position (in)')
    left_ax.plot(timestamps, MAX_DEFLECTION * left_pos_cmd, color='blue', linestyle='-', label='Commanded Position')
    left_ax.plot(timestamps, left_pos_measured, color='purple', linestyle='-', label='Measured Position')
    left_ax.tick_params(axis='y')
    left_ax.legend(loc='best')
    left_ax.grid(True, alpha=0.3)

    # Bottom subplot: Right motor
    right_ax.set_title('Right Motor - Commanded vs. Measured Position')
    right_ax.set_xlabel('Time (s)')
    right_ax.set_ylabel('Position (in)')
    right_ax.plot(timestamps, MAX_DEFLECTION * right_pos_cmd, color='red', linestyle='-', label='Commanded Position')
    right_ax.plot(timestamps, right_pos_measured, color='orange', linestyle='-', label='Measured Position')
    right_ax.tick_params(axis='y')
    right_ax.legend(loc='best')
    right_ax.grid(True, alpha=0.3)

    fig.tight_layout()

  def state_analysis(self):
    timestamps = self.df['timestamp_timer']
    altitude   = self.df['altitude_m']
    apog_detec = self.df['apogee_detected']
    pos_east   = self.df['pos_east_m']
    pos_north  = self.df['pos_north_m']
    d_to_targ  = self.df['distance_to_target_m']
    fsm_mode   = self.df['fsm_mode']

    mask = pos_east.notna() & pos_north.notna()

    fig2      = plt.figure(figsize=(10,8))
    flight_ax = fig2.add_subplot(111, projection='3d')
    scatter = flight_ax.scatter(pos_east[mask], pos_north[mask], 
                  altitude[mask], c=fsm_mode[mask], 
                  cmap='viridis', s=10)
    flight_ax.set_title('Position Plot')
    flight_ax.set_xlabel('Position East (m)')
    flight_ax.set_ylabel('Position North (m)')
    flight_ax.set_zlabel('Altitude (m)')

    cbar = fig2.colorbar(scatter, ax=flight_ax, pad=0.1)
    cbar.set_label('FSM Mode ID')

    # Combined figure: altitude (with apogee detected), apogee_counter, and vertical speed
    fig3, (alt_ax, ac_ax, vs_ax) = plt.subplots(3, 1, figsize=(10,8), sharex=True)

    # Top: altitude with apogee detected (twin y-axis)
    alt_ax.set_title('Altitude & Apogee Detection vs Time')
    alt_ax.set_ylabel('Altitude (m)')
    alt_ax.plot(timestamps[1:], altitude[1:], color='blue', linestyle='-', label='Altitude')
    alt_ax.tick_params(axis='y', color='blue')
    apo_ax = alt_ax.twinx()
    apo_ax.set_ylabel('Apogee Detected')
    apo_ax.plot(timestamps[1:], apog_detec[1:], color='red', linestyle='-', label='Apogee Detected')
    apo_ax.tick_params(axis='y', color='red')
    apo_ax.set_ylim((0,1))
    alt_ax.legend(loc='upper left')
    apo_ax.legend(loc='upper right')

    # Middle: apogee counter
    ac_ax.set_title('Apogee Counter vs Time')
    ac_ax.set_ylabel('Apogee Counter')
    ac_ax.plot(timestamps, self.df['apogee_counter'], color='magenta', linestyle='-')
    ac_ax.legend(['Apogee Counter'])

    # Bottom: vertical speed
    vs_ax.set_title('Vertical Speed vs Time')
    vs_ax.set_xlabel('Time (s)')
    vs_ax.set_ylabel('v_speed_m_s')
    vs_ax.plot(timestamps, self.df['v_speed_m_s'], color='cyan', linestyle='-')
    vs_ax.set_ylim(-5, 5)
    vs_ax.legend(['v_speed_m_s'])

    fig3.tight_layout()

    # 1. Clean and Prepare Data
    df_clean = self.df.dropna(subset=['latitude_deg', 'longitude_deg'])
    route_points = list(zip(df_clean['longitude_deg'], df_clean['latitude_deg']))
    route_geom = LineString(route_points)
    
    # 2. Create GeoDataFrame in GPS coordinates (4326)
    gdf_route = gpd.GeoDataFrame(index=[0], geometry=[route_geom], crs="EPSG:4326")
    
    # 3. CONVERT TO WEB MERCATOR (Mandatory for contextily)
    gdf_route = gdf_route.to_crs(epsg=3857)

    # 4. Plotting
    fig, ax = plt.subplots(figsize=(12, 12))
    
    # Plot the line (using a bright color like yellow or cyan to stand out against satellite)
    gdf_route.plot(ax=ax, color='cyan', linewidth=3, alpha=0.8, zorder=2)

    # 5. Add the Satellite Imagery
    # Esri.WorldImagery is usually the highest quality for flight paths
    cx.add_basemap(ax, source=cx.providers.Esri.WorldImagery, zorder=1)

    # 6. Final Polish
    ax.set_title("Flight Plot", fontsize=15, pad=20)
    ax.axis('off') # Hide the Mercator meter coordinates for a cleaner look

  def control_analysis(self):
    timestamps = self.df['timestamp_timer']
    cmd_deflection = self.df['fc_cmd']
    heading_deg = self.df['heading_deg']
    target_heading_deg = self.df['target_heading_deg']
    heading_err = self.df['heading_error_deg']

    fig, (err_ax, head_ax) = plt.subplots(2, figsize=(10,6))

    # Err vs FC CMD
    err_ax.set_title('Heading Err vs FC Cmd')
    err_ax.set_xlabel('Time (s)')
    err_ax.set_ylabel('Heading Error')
    err_ax.plot(timestamps, heading_err, color='blue', linestyle='-', label='Heading Error')
    err_ax.tick_params(axis='y', labelcolor='blue')
    fc_ax = err_ax.twinx()

    err_ax.legend()

    fc_ax.set_ylabel('FC CMD')
    fc_ax.plot(timestamps, cmd_deflection, color='green', linestyle='--', label='Left FC command')
    fc_ax.tick_params(axis='y', labelcolor='green')

    fc_ax.legend()

    # Target vs Heading
    head_ax.set_title('Target Heading Vs Measured Heading')
    head_ax.set_xlabel('Time (s)')
    head_ax.set_ylabel('Degrees')
    head_ax.plot(timestamps, heading_deg, color='blue', linestyle='-', label='Measured')
    head_ax.plot(timestamps, target_heading_deg, color='red', linestyle='--', label='Target')
    head_ax.legend()

    fig.tight_layout() 


def main():
   flight_analyzer = FlightAnalyzer(FILE_PATH)
   flight_analyzer.plot()

if __name__ == '__main__':
   main()