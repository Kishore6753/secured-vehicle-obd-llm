import streamlit as st

# Import all app modules
import app_pages.introduction as introduction
import app_pages.obd_overview as obd_overview
import app_pages.lsm_overview as lsm_overview
#import app_pages.bootloader_overview as bootloader_overview
import app_pages.someip_overview as someip_overview
import app_pages.network_overview as network_overview
import app_pages.fota as fota
import app_pages.bootloader_cloud as bootloader_cloud

# Configure page
st.set_page_config(page_title="Fleet Management", layout="wide")
st.sidebar.title("🚗 Fleet Navigation")

# Navigation options
page = st.sidebar.radio("Select a page:", [
    "🏁 Introduction",
    "🚘 OBD Overview",
    "🛠️ LSM Overview",
#    "🧩 Bootloader Overview",
    "📡 SomeIP Overview",
    "🌐 Network Overview",
    "📤 FOTA Updates",
    "☁️ BootLoader_Cloud"
])

# Page routing
if page == "🏁 Introduction":
    introduction.show()
elif page == "🚘 OBD Overview":
    obd_overview.show()
elif page == "🛠️ LSM Overview":
    lsm_overview.show()
#elif page == "🧩 Bootloader Overview":
#    bootloader_overview.show()
elif page == "📡 SomeIP Overview":
    someip_overview.show()
elif page == "🌐 Network Overview":
    network_overview.show()
elif page == "📤 FOTA Updates":
    fota.show()
elif page == "☁️ BootLoader_Cloud":
    bootloader_cloud.show()
