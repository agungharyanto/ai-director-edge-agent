# ADR-0003

## Judul

Device Inventory sebagai Source of Truth

---

## Status

Accepted

---

## Latar Belakang

Pada versi awal AI Director, Discovery menghasilkan daftar device sementara (discovery_result), kemudian user melakukan import menjadi Camera.

Arsitektur ini hanya cocok apabila AI Director menangani kamera.

Roadmap AI Director akan berkembang menjadi platform Edge Appliance yang mampu mengelola:

- IP Camera
- NVR
- PoE Switch
- Router
- NAS
- Mini PC
- VPN Gateway
- IoT Device
- AI Accelerator

Sehingga dibutuhkan satu database inventaris perangkat yang menjadi Source of Truth.

---

## Keputusan

Discovery hanya bertugas menemukan device.

Setelah ditemukan, device akan disinkronkan ke Device Inventory.

Seluruh modul lain menggunakan Device Inventory sebagai referensi utama.

Camera menjadi turunan (child entity) dari Device.

---

## Arsitektur

Cloud

↓

Edge Agent

↓

Discovery

↓

Device Inventory

↓

Camera

↓

Recorder

↓

AI Engine

↓

Monitoring

---

## Discovery Workflow

Discovery Job

↓

Discovery Result (Temporary)

↓

Inventory Sync

↓

Device Inventory

↓

Camera Adoption

---

## Device Identity

Prioritas identitas perangkat:

1. MAC Address
2. Serial Number
3. UUID Internal AI Director

IP Address bukan identitas permanen.

---

## Device Lifecycle

DISCOVERED

↓

IDENTIFIED

↓

ADOPTED

↓

MONITORED

↓

OFFLINE

↓

REMOVED

---

## Target Sprint

v0.4.x

