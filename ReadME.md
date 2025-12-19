# /dev/SDB — Software Defined Boot

**/dev/SDB** is a novel **software-defined, diskless boot standard** that allows users to securely boot into **role-specific operating systems from anywhere** — over **wired, Wi-Fi, or cellular networks** — without relying on persistent local storage.

This project rethinks traditional PXE and network booting by extending it beyond wired enterprise LANs into a **true work-from-anywhere model**, while enforcing **pre-boot authentication and per-user OS policies**.

---

## 🚀 Key Idea

> Treat operating systems as **software-defined policies**, not machine-bound installations.

Instead of installing multiple OSes on shared machines:
- Users authenticate **before the OS boots**
- The system provisions **only the OS they are authorized to use**
- The OS runs **entirely in memory** (diskless)
- No persistent storage → **reduced attack surface**

---

## 🧠 Core Features

- 🔐 **Pre-boot user authentication**
- 🧩 **Per-user OS assignment**
- 💾 **Diskless, in-memory OS boot**
- 🌍 **Works over Wi-Fi, Ethernet, and cellular**
- 🔄 **Stateless clients (malware flushed on shutdown)**
- 🖥️ **Supports heterogeneous OS environments**
- 📜 **Centralized logging & auditing (MAC-based)**

---

## 🏗️ System Architecture

/dev/SDB is composed of **two tightly integrated modules**:

### 1️⃣ Hardware Module (Pre-Boot Network Enabler)

A lightweight **Single Board Computer (SBC)** that:
- Runs a minimal Linux distro (e.g., Alpine)
- Bridges the target PC and upstream network
- Provides:
  - DHCP / Proxy DHCP
  - DNS interception
  - TFTP server
  - iPXE bootloader
- Enables network connectivity **before** the target OS exists

📌 This module lives **inside or alongside the target machine**, mitigating PXE poisoning risks.

---

### 2️⃣ Cloud Module (OS & Policy Controller)

A centralized cloud service that:
- Authenticates users
- Stores OS images and metadata
- Assigns OSes based on **roles**
- Logs all boot attempts (successful & failed)

**Tech stack:**
- Flask (Python)
- SQLite (users & OS metadata)
- File storage / optional NFS

---

## 🔄 Boot Workflow (High Level)

1. Target PC powers on → enters PXE
2. Hardware module intercepts DHCP
3. iPXE bootloader is served
4. Network connectivity established (Wi-Fi / Cellular if needed)
5. User is prompted for credentials
6. Cloud module authenticates user
7. Assigned OS is streamed into RAM
8. System boots into the authorized OS

---

## 🧪 Experimental Setup

- Simulated using **GNS3**
- Diskless QEMU target PCs
- Minimal RAM footprint (≈256MB)
- Multiple OS profiles tested:
  - Alpine Linux
  - Tiny Core Linux
  - Kolibri OS

All scenarios successfully booted with **consistent results**.

---

## 🔐 Threat Model & Security Advantages

| Threat | Mitigation |
|------|-----------|
| PXE Proxy DHCP poisoning | Hardware module is internal |
| Persistent malware | No local storage |
| Unauthorized OS access | OS served only after auth |
| Credential reuse | Centralized authentication |

---

## 📌 Use Cases

- Enterprise shared workstations
- Secure remote work environments
- Role-based OS provisioning
- Diskless thin clients
- Zero-trust endpoint models
- Education & labs
- Incident-response or forensic boot environments

---

## 🛣️ Future Scope

- Physical hardware module implementation
- Enterprise-scale stress testing
- TPM / Secure Boot integration
- Public & private cloud deployments
- Satellite network support
- Performance benchmarking in real-world networks

---

## 📄 Research Background

This repository is based on the academic paper:

> **“/dev/SDB: Software Defined Boot – A novel standard for diskless booting anywhere and everywhere”**  
> CyberMACS, Kadir Has University, Turkey

📚 Full paper included in this repository  
:contentReference[oaicite:0]{index=0}

---

## 👥 Authors

- Aditya Mitra  
- Hamza Haroon  
- Amaan Rais Shah
- Mohammad Elham Rasooli  
- Bogdan Itsam Dorantes Nikolaev  

---

## 📜 License

> _License to be added_  
(Recommended: Apache 2.0 or GPL-v3 depending on enterprise adoption goals)

---

## 🤝 Contributions

This project is currently **research-driven**.  
Contributions, discussions, and design critiques are welcome via Issues.

---

## ⭐ Why /dev/SDB Matters

/dev/SDB demonstrates how operating systems can be:
- **User-centric**
- **Policy-driven**
- **Stateless**
- **Location-agnostic**

> It establishes a foundation for treating OS booting as a **cloud-native service**, not a local artifact.
