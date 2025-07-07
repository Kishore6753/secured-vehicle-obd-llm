# 🚗 Secured Vehicle's On-Board Diagnostics LLM-Based System (2024–2025)

A comprehensive IoT-based automotive diagnostics and fleet management system developed as a graduation project.

## 📌 Project Overview

This system integrates embedded devices, cloud services, machine learning, and Android Automotive OS to provide secure, scalable, and smart vehicle diagnostics.

### 🔧 Key Components

| Component        | Description |
|------------------|-------------|
| **Android Apps** | Chatbot for LLM-based OBD diagnostics + Simulated OBD device |
| **Cloud**        | C++ apps securely pushing logs to AWS IoT Core, logged in Timestream |
| **Web App**      | Streamlit-based fleet management + FOTA + malware detector |
| **FOTA**         | Secure firmware updates for STM32 via MQTT |
| **LLM**          | Diagnostic chatbot embedded into Android Automotive |

---

## 📁 Folder Structure
secured-vehicle-obd-llm/
├── android/
├── cloud/
├── web_app/
└── Summary Table.pdf



## 🚀 Tech Stack

- **Embedded**: raspberry pi 3&5, STM32, C++, MQTT
- **Cloud**: AWS IoT Core, AWS Timestream, AWS IAM, EC2
- **Web**: Streamlit, Flask
- **Machine Learning**: Pickle-based ML model for binary safety
- **Android**: Android Automotive OS, LLM chatbot integration, OBD app integration

---

## 🛠️ Deployment Guide

Each folder includes its own README with setup and deployment instructions:
- [`android/`](./android/) – Chatbot and OBD simulation apps
- [`cloud/`](./cloud/) – Logs transmission and AWS IoT integration
- [`web_app/`](./web_app/) – Visualization, Flask API, Bootloader malware scanner

