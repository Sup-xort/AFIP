import onnxruntime as ort
import numpy as np

# 정규화 함수
def normalize(seq):
    seq = np.array(seq, dtype=np.float32)
    seq = (seq - seq.mean(keepdims=True)) / (seq.std(keepdims=True) + 1e-6)
    return np.expand_dims(seq, axis=(0, 2))  # (1, 20, 1)

# 부정맥 예측 함수
def get_pred(seq, model_path="model.onnx"):
    session = ort.InferenceSession(model_path)

    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    l = len(seq)
    cnt = 0

    for i in range(l):
        if 200 < seq[i] < 2100:
            cnt += 1
        else:
            cnt = 0

        if cnt >= 20:
            rri_window = seq[i - 19 : i + 1]

            tensor = normalize(rri_window)
            print(tensor)
            outputs = session.run([output_name], {input_name: tensor})
            if np.argmax(outputs[0]) == 1:
                return 1

    return 0
