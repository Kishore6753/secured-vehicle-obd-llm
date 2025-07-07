import streamlit as st

def show():
    st.title("🏁 Welcome to Fleet Management Dashboard")
    st.markdown("""
    This dashboard provides real-time monitoring and detailed insights into key components of connected vehicle systems.

    ### System Modules Covered:
    - **OBD Overview**: OBD and realtime data
    - **LSM Overview**: Linux security module 
    - **Bootloader Overview**: firmware malware detection
    - **SomeIP Overview**: IDS for Some IP
    - **Network Overview**: firewall with configuration
    - **FOTA Updates**: Firmware Over-The-Air update status

    ### How to Use:
    Use the sidebar to navigate between modules and explore real-time metrics and historical data across the fleet.

    ---
    🔧 This tool is ideal for engineers, analysts, and integrators working on modern vehicle software stacks.
    """)
