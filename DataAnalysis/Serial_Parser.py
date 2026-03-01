import serial
import time

def catch_data_dump(port_name, baud_rate):
    with open("data/ARES_CarTest/***.csv", "w") as file:
        try:
            # Initialize serial with a longer timeout to catch the start
            ser = serial.Serial(port_name, baud_rate, timeout=2)
            print(f"Connected to ARES on {port_name}.")

            # 1. Send Shutdown & Dump Commands
            # Using \n or \r\n depending on what your ARES parser expects
            print(">>> SENDING: sensors_off")
            ser.write(b'sensors_off\n')
            time.sleep(0.5) 

            print(">>> SENDING: logging_off")
            ser.write(b'logging_off\n')
            time.sleep(0.5)

            print(">>> SENDING: dump")
            ser.write(b'dump\n')
            time.sleep(0.2)

            # 2. Synchronization: Wait for the "Dumping" header
            print("Waiting for data stream...")
            started = False
            while not started:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if "Dumping" in line:
                        print(">>> START SIGNAL RECEIVED. CATCHING DUMP...")
                        file.write(f"--- DUMP START: {time.ctime()} ---\n")
                        started = True

            # 3. Capture Loop
            while True:
                if ser.in_waiting > 0:
                    line_bytes = ser.readline()
                    decoded_line = line_bytes.decode('utf-8', errors='ignore').strip()
                    
                    if decoded_line:
                        # Optional: Print to console so you can see progress
                        print(decoded_line) 
                        
                        # timestamp = time.strftime("%H:%M:%S", time.localtime())
                        file.write(f"{decoded_line}\n")
                        file.flush() 
                        
        except serial.SerialException as e:
            print(f"Serial error: {e}")
        except KeyboardInterrupt:
            print("\nCapture stopped by user.")
        finally:
            if 'ser' in locals() and ser.is_open:
                ser.close()

if __name__ == '__main__':
    # For your Pi 4 or laptop: check if it's '/dev/ttyACM0' or 'COM4'
    # SERIAL_PORT = 'COM4' # for windows
    SERIAL_PORT = '/dev/cu.usbmodem01234567891' # for mac
    BAUD_RATE = 115200 

    catch_data_dump(SERIAL_PORT, BAUD_RATE)