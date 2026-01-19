# Smart Door Lock System (IoT + AI)

![Python](https://img.shields.io/badge/Python-3.11-blue) ![Platform](https://img.shields.io/badge/Platform-Raspberry_Pi_5-red) ![Hardware](https://img.shields.io/badge/Hardware-Arduino_%7C_ESP32-green) ![Status](https://img.shields.io/badge/Status-In_Development-yellow)

A secure, biometric access control system capable of detecting faces and verifying identity against a local database, and physically unlocking a door mechanism. This project bridges **Computer Vision** models with **Embedded Systems**.

---

## Table of Contents
- [System Architecture](#-system-architecture)
- [Key Features](#-key-features)
- [Hardware Checklist](#-hardware-checklist)
- [Software Stack](#-software-stack)
- [Installation & Setup](#-installation--setup)
- [Project Roadmap](#-project-roadmap)

---

## System Architecture

The system operates on a **Master-Slave** architecture:
1.  **The Brain (Master):** A Raspberry Pi 5 running high-performance Python scripts for Liveness Detection and Face Recognition.
2.  **The Muscle (Slave):** An Arduino/ESP32 connected via **MQTT** that controls the servo motor and handles physical state (locking/unlocking).

```mermaid
graph LR
    A[Camera Input] -->|Video Feed| B(Raspberry Pi 5)
    B -->|Preprocessing| C{Liveness Check}
    C -- Real Face --> D[DeepFace Recognition]
    C -- Spoof/Photo --> E[Block Access]
    D -- Match Found --> F[MQTT 'OPEN' Command]
    F -->|MQTT| G[Arduino/ESP32]
    G -->|PWM Signal| H[Servo Motor]
    G -->|ACK Signal| B
