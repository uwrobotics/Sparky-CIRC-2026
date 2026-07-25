import serial
import sys

PORT = "/dev/ttyACM0"
BAUD = 115200
TIMEOUT = 1

def main():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=TIMEOUT)
        print(f"Listening on {PORT} @ {BAUD} baud")
        print("-" * 40)

        while True:
            line = ser.readline()
            if line:
                text = line.decode("utf-8", errors="replace").rstrip()
                print(text)

    except serial.SerialException as e:
        print(f"Serial error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        if "ser" in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()