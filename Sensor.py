import serial

# 시리얼 포트 연결 (환경에 따라 COM 포트 변경)
ser = serial.Serial("COM6", 115200)
ser.reset_input_buffer()

def get_rri():
    """
    센서에서 RRI(ms 단위) 값을 읽어 반환.
    유효 범위 (200~2000ms)가 아닐 경우 None 반환.
    """
    if ser.in_waiting:
        try:
            line = ser.readline().decode().strip()
            if line.isdigit():
                rri = int(line)
                if 200 < rri < 2100:  # ✅ 유효한 심박 범위 (BPM 30~300)
                    return rri
        except:
            pass  # 디코딩 오류 등 무시
    return None

