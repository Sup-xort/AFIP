import serial
import time

# 아두이노 시리얼 포트 설정 (환경에 맞게 수정)
ser = serial.Serial('COM6', 115200, timeout=1.1)
time.sleep(2)  # 아두이노 재시작 대기

ser.reset_input_buffer() 

while True:
    try:
        line_raw = ser.readline().decode().strip()
        print(repr(line_raw))
        if line_raw.isdigit():
            rri = int(line_raw)
            print(rri)
