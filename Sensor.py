import serial

# 시리얼 포트 설정 (환경에 따라 수정)
ser = serial.Serial("COM6", 115200)
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
                    return rri  # ✅ 유효한 값이면 바로 반환
        except:
            continue  # 에러 발생 시 무시하고 계속 대기
