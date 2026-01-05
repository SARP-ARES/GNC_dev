import numpy as np

class GPS:
    def __init__(self, state, origin, posLTP):
        self.state = state
        self.origin = origin
        self.posLTP = posLTP
        
    def getPosECEFr(self):
        '''
        Convert the current position (latitude, longitude, altitude) to ECEF-r coordinates.
        '''
        # Convert latitude and longitude to radians
        lat_rad = self.state.lat * np.pi / 180
        lon_rad = self.state.lon * np.pi / 180

        a = 6378137.0  # Earth semi-major axis (m)
        b = 6356752.3142  # Earth semi-minor axis (m)
        f = (a - b) / a  # Ellipsoid flatness
        e = np.sqrt(f * (2 - f))  # Eccentricity

        # Distance from the earth's surface to the z-axis along the ellipsoid normal
        N = a / np.sqrt(1 - (e ** 2) * (np.sin(lat_rad) ** 2))

        h = self.state.alt
        x = (h + N) * np.cos(lat_rad) * np.cos(lon_rad)
        y = (h + N) * np.cos(lat_rad) * np.sin(lon_rad)
        z = (h + N * (1 - e ** 2)) * np.sin(lat_rad)
        
        return PositionECEFr(x, y, z)

    def setOriginECEFr(self):
        '''
        Set the origin of the local tangent plane to be the current ECEF-r coordinates
        '''
        self.origin = self.getPosECEFr()

    def updatePosLTP(self):
        # Convert latitude and longitude to radians
        lat_rad = np.deg2rad(self.state.lat)
        lon_rad = np.deg2rad(self.state.lon)

        a = 6378137.0  # Earth semi-major axis (m)
        b = 6356752.3142  # Earth semi-minor axis (m)
        f = (a - b) / a  # Ellipsoid flatness
        e = np.sqrt(f * (2 - f))  # Eccentricity

        # Distance from the earth's surface to the z-axis along the ellipsoid normal
        N = a / np.sqrt(1 - (e ** 2) * (np.sin(lat_rad) ** 2))

        h = self.state.alt
        x = (h + N) * np.cos(lat_rad) * np.cos(lon_rad)
        y = (h + N) * np.cos(lat_rad) * np.sin(lon_rad)
        z = (h + N * (1 - e ** 2)) * np.sin(lat_rad)

        # Subtract the origin ECEF-r coordinate to get relative position vector
        x_p = x - self.origin.x
        y_p = y - self.origin.y
        z_p = z - self.origin.z

        # Rotate to align y-axis with LTP
        x_pp = -x_p * np.sin(lon_rad) + y_p * np.cos(lon_rad)
        y_pp = x_p * np.cos(lon_rad) + y_p * np.sin(lon_rad)
        z_pp = z_p

        # Final rotation to align z-axis with up (commented out, as in your test code)
        self.posLTP.e = x_pp
        self.posLTP.n = -y_pp * np.sin(lat_rad) + z_pp * np.cos(lat_rad)
        self.posLTP.u = y_pp * np.cos(lat_rad) + z_pp * np.sin(lat_rad)

        # # TESTING RELATIVE POSITION IN ECEFr
        # self.pos = PositionLTP()
        # self.pos.e = x_p
        # self.pos.n = y_p
        # self.pos.u = z_p
        
        
class State:
    def __init__(self, lat=0.0, lon=0.0, alt=0.0):
        self.lat = lat # degrees
        self.lon = lon # degrees
        self.alt = alt # meters

class PositionECEFr:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x  # ECEFr X coordinate (meters)
        self.y = y  # ECEFr Y coordinate (meters)
        self.z = z  # ECEFr Z coordinate (meters)
        
        
class PositionLTP:
    def __init__(self, e=0.0, n=0.0, u=0.0):
        self.e = e  # East coordinate (meters)
        self.n = n  # North coordinate (meters)
        self.u = u  # Up coordinate (meters)
        

if __name__ == "__main__":
    # Example usage
    state = State(lat=37.7749, lon=-122.4194, alt=30)  # Example coordinates
    origin = PositionECEFr()
    pos = PositionLTP()

    gps = GPS(state, origin, pos)

    ecef = gps.getPosECEFr()
    print(f"Initial Position: (lat={gps.state.lat}, lon={gps.state.lon}, alt={gps.state.alt})")
    print(f"Initial ECEF-r Position: (x={ecef.x:.3f}, y={ecef.y:.3f}, z={ecef.z:.3f})")
    print(f"Initial LTP Position: (e={gps.posLTP.e:.3f}, n={gps.posLTP.n:.3f}, u={gps.posLTP.u:.3f})")
    print(f"Initial Origin (unset): (x={gps.origin.x:.3f}, y={gps.origin.y:.3f}, z={gps.origin.z:.3f})")
    
    print("Setting origin to current ECEF-r position...")
    gps.setOriginECEFr()
    
    print(f"Updated Origin ECEF-r Position: (x={gps.origin.x:.3f}, y={gps.origin.y:.3f}, z={gps.origin.z:.3f})")
    
    print("Updating lat and lon to simulate movement...")
    gps.state = State(lat=37.8, lon=-122.4, alt=30)  # Update state (increase lat, lon, alt)
    print(f"Updated Position: (lat={gps.state.lat}, lon={gps.state.lon}, alt={gps.state.alt})")
    
    gps.updatePosLTP()  # Update LTP position based on new state
    print(f"Updated LTP Position: (e={gps.posLTP.e:.3f}, n={gps.posLTP.n:.3f}, u={gps.posLTP.u:.3f})")
