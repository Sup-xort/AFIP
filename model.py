import onnxruntime as ort
import numpy as np

def normalize(seq):
    seq = np.array(seq, dtype=np.float32)
    seq = (seq - seq.mean(keepdims=True)) / (seq.std(keepdims=True) + 1e-6)
    return np.expand_dims(seq, axis=(0, 2))

def softmax(x):
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()

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

            outputs = session.run([output_name], {input_name: tensor})
            raw_output = outputs[0][0]

            # softmax 확률로 변환
            probs = softmax(raw_output)
            pred = int(np.argmax(probs))
            confidence = float(probs[pred])

            return pred, confidence

    return 0, 0.0
