import serial

ser = serial.Serial("/dev/ttyAMA0", 115200)
ser.reset_input_buffer()

def get_rri():
    """
    유효한 RRI(200~2000ms)가 들어올 때까지 blocking 방식으로 기다림.
    """
    while True:
        try:
            line = ser.readline().decode().strip()
            if line.isdigit():
                rri = int(line)
                if 200 < rri < 2000:
                    return rri
        except:
            continue
