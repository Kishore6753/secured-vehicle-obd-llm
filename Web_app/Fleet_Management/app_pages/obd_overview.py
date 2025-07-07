import streamlit as st
import os
import json
import glob
import pandas as pd

def show():
    st.title("🚗 Live OBD Error Dashboard")
    if st.button("🔄 Refresh Table"):
        st.rerun()


    archive_dir = "/home/ubuntu/Flask_Server/received_jsons"
    json_files = sorted(glob.glob(os.path.join(archive_dir, "*.json")), key=os.path.getmtime, reverse=True)

    records = []

    for file in json_files:
        try:
            with open(file, "r") as f:
                data = json.load(f)
                # Handle list of records
                if isinstance(data, list):
                    for entry in data:
                        if isinstance(entry, dict):
                            entry["source_file"] = os.path.basename(file)
                            records.append(entry)
                # Handle single dictionary
                elif isinstance(data, dict):
                    data["source_file"] = os.path.basename(file)
                    records.append(data)
                else:
                    st.warning(f"⚠️ Unsupported JSON format in {file}")
        except Exception as e:
            st.error(f"Failed to load {file}: {e}")

    if records:
        df = pd.DataFrame(records)
        if "source_file" in df.columns:
            df = df.drop(columns=["source_file"])
        st.dataframe(df)
    else:
        st.warning("No JSON metadata files found in archive.")