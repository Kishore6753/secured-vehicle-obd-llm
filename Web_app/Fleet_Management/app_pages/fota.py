import streamlit as st
import os
import subprocess

def show():
    st.title("FOTA Updates")

    uploaded_file = st.file_uploader("Upload Firmware Update (Choose a .bin file)", type="bin")

    if uploaded_file:
        # Define the save path
        save_path = os.path.join("Bootloader", uploaded_file.name)
        os.makedirs("Bootloader", exist_ok=True)

        # Save the uploaded file
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"Firmware update uploaded successfully! File saved to: {save_path}")

        # Define the path to cloud.py
        cloud_script_path = os.path.join(os.getcwd(), 'Bootloader', 'cloud.py')

        # Run the cloud.py script after uploading, passing the uploaded file path
        try:
            result = subprocess.run(
                ['python3', cloud_script_path, save_path],  # Pass the uploaded file path
                capture_output=True,
                text=True
            )

            # Output the result of the script
            st.text(result.stdout)
            st.error(result.stderr)

            if os.path.exists(save_path):
                os.remove(save_path)
        except Exception as e:
            st.error(f"Error running cloud.py: {e}")

