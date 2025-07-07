import streamlit as st
import os
import json
import glob
import pandas as pd

def show():
    st.title("📑 BootLoader Overview")
    st.markdown("This table displays all metadata from archived firmware JSON files.")

    archive_dir = "/home/ubuntu/Fleet_Management/JSONS"
    json_files = sorted(glob.glob(os.path.join(archive_dir, "firmware_v*.json")), key=os.path.getmtime, reverse=True)

    records = []

    for file in json_files:
        try:
            with open(file, "r") as f:
                data = json.load(f)
                data["source_file"] = os.path.basename(file)
                records.append(data)
        except Exception as e:
            st.error(f"Failed to load {file}: {e}")

    if records:
        df = pd.DataFrame(records)
        st.dataframe(df)
    else:
        st.warning("No JSON metadata files found in archive.")

