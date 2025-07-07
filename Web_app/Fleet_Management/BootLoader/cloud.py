import os
import json
import joblib
import pandas as pd
import math
import string
from collections import Counter
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
import sys
import warnings
from datetime import datetime
import shutil

# Suppress scikit-learn warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
warnings.filterwarnings("ignore", category=Warning, module="sklearn")

# Fixed absolute paths
BASE_DIR = "/home/ubuntu/Fleet_Management"
ARCHIVE_DIR = os.path.join(BASE_DIR, "JSONS")
os.makedirs(ARCHIVE_DIR, exist_ok=True)

# ---------------------------
# Feature Extraction
# ---------------------------

def load_binary(path):
    with open(path, "rb") as f:
        return f.read()

def entropy(data):
    if not data:
        return 0.0
    counter = Counter(data)
    total = len(data)
    return -sum((count / total) * math.log2(count / total) for count in counter.values())

def byte_histogram(data):
    histogram = [0] * 256
    for b in data:
        histogram[b] += 1
    total = len(data)
    return [round(h / total, 5) for h in histogram] if total > 0 else [0] * 256

def extract_strings(data, min_length=4):
    result = []
    current = ''
    for byte in data:
        c = chr(byte)
        if c in string.printable and c != '\x00':
            current += c
        else:
            if len(current) >= min_length:
                result.append(current)
            current = ''
    if len(current) >= min_length:
        result.append(current)
    return result

def extract_byte_ngrams(data, n=2, top_k=10):
    ngrams = [data[i:i+n] for i in range(len(data) - n + 1)]
    freq = Counter(ngrams)
    total = sum(freq.values())
    normalized = {k: round(v / total, 5) for k, v in freq.items()} if total > 0 else {}
    top = dict(Counter(normalized).most_common(top_k))
    return {f'ngram_{k.hex()}': v for k, v in top.items()}

def extract_opcodes(data, base_addr=0x08000000):
    try:
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        instructions = md.disasm(data, base_addr)
        opcodes = [insn.mnemonic for insn in instructions]
        freq = Counter(opcodes)
        return {f'op_{op}': freq[op] for op in freq}
    except Exception:
        return {}

def extract_features_from_bin(file_path):
    data = load_binary(file_path)
    features = {
        "file_name": os.path.basename(file_path),
        "size": len(data),
        "entropy": entropy(data)
    }
    byte_hist = byte_histogram(data)
    features.update({f'byte_{i}': val for i, val in enumerate(byte_hist)})

    strings = extract_strings(data)
    string_count = len(strings)
    total_len = sum(len(s) for s in strings)
    features["string_count"] = string_count
    features["avg_string_len"] = total_len / string_count if string_count > 0 else 0
    features["max_string_len"] = max((len(s) for s in strings), default=0)
    features["min_string_len"] = min((len(s) for s in strings), default=0)
    features["total_string_len"] = total_len

    features.update(extract_byte_ngrams(data, n=2, top_k=10))
    features.update(extract_opcodes(data))

    return features, data, strings

# ---------------------------
# Prediction
# ---------------------------

def preprocess_features(features, expected_columns):
    df = pd.DataFrame([features])
    for col in expected_columns:
        if col not in df.columns:
            df[col] = 0
    df = df[expected_columns]
    return df.to_numpy()

def get_next_version_number():
    versions = []
    for fname in os.listdir(ARCHIVE_DIR):
        if fname.startswith("firmware_v") and fname.endswith(".json"):
            try:
                number = int(fname.split("firmware_v")[1].split(".")[0])
                versions.append(number)
            except:
                continue
    return max(versions, default=0) + 1

def process_bin_file(file_path, model_path, encoder_path, features_csv_path):
    model = joblib.load(model_path)
    label_encoder = joblib.load(encoder_path)
    df_ref = pd.read_csv(features_csv_path, nrows=1)
    expected_columns = [col for col in df_ref.columns if col not in ("file_name", "label")]

    features, binary_data, strings = extract_features_from_bin(file_path)
    input_data = preprocess_features(features, expected_columns)

    prediction = model.predict(input_data)
    label = label_encoder.inverse_transform(prediction)[0]
    print(f"\nPrediction: {label.upper()}")

    probs = model.predict_proba(input_data)[0]
    for i, prob in enumerate(probs):
        print(f"   {label_encoder.classes_[i]}: {prob:.4f}")

    #  Clear old files from BASE_DIR (not delete — just move)
    for f in os.listdir(BASE_DIR):
        if f.startswith("firmware_v") and (f.endswith(".json") or f.endswith(".bin")):
            src = os.path.join(BASE_DIR, f)
            dst = os.path.join(ARCHIVE_DIR, f)
            shutil.move(src, dst)

    # Version number
    version = get_next_version_number()

    # Metadata
    json_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Car_ID": 101,
        "file_name": os.path.basename(file_path),
        "Board": "telematics",
        "label": label
    }

    # Save new files to BASE_DIR
    json_filename = os.path.join(BASE_DIR, f"firmware_v{version}.json")
    with open(json_filename, "w") as f:
        json.dump(json_data, f, indent=4)

    bin_filename = os.path.join(BASE_DIR, f"firmware_v{version}.bin")
    with open(bin_filename, "wb") as f:
        f.write(binary_data)

    print(f"\n📄 Generated '{json_filename}' with metadata.")
    print(f"📦 Saved input binary as '{bin_filename}'.")

    # Copy JSON to archive (retain history)
    shutil.copy(json_filename, os.path.join(ARCHIVE_DIR, f"firmware_v{version}.json"))

# ---------------------------
# Run
# ---------------------------

def run(file_path):
    if not os.path.exists(file_path):
        print(f"The file at {file_path} does not exist.")
        return

    print(f"Processing file: {file_path}")
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "malware_detector_model.pkl")
    encoder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "label_encoder.pkl")
    features_csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "features.csv")

    process_bin_file(
        file_path=file_path,
        model_path=model_path,
        encoder_path=encoder_path,
        features_csv_path=features_csv_path
    )

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("No .bin file path provided.")
    else:
        file_path = sys.argv[1]
        run(file_path)
