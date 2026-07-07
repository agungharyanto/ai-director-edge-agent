# Sprint 25-30 — AI Director Edge Agent v0.4.x

## Ringkasan

Sprint ini membangun fondasi penting untuk AI Director sebagai Edge Video AI Platform.

## Fitur Selesai

- Credential Manager v1
- Encrypted credential profile
- Hikvision Driver refactor
- Base Driver Framework
- Driver Factory
- Camera Detail Page
- Snapshot Engine v1
- Hide OSD Hikvision
- Auto Provision saat Discovery Import
- AI Director Camera Profile
- AI Ready status
- Provision All Cameras

## Flow Saat Ini

Discovery
→ Credential Engine
→ Hikvision Driver
→ AI Director Profile
→ Hide OSD
→ Verify Snapshot
→ Generate RTSP
→ Import Camera
→ AI READY

## Catatan Teknis

- Password kamera tidak lagi ditulis langsung ke source code.
- Credential disimpan di SQLite dalam bentuk encrypted.
- MASTER_KEY disimpan di `.env`.
- Hikvision ISAPI digunakan untuk device info, snapshot, RTSP URL, dan OSD.
- OSD dimatikan untuk menghindari gangguan AI Vision.

## Status

Stable untuk 1 kamera Hikvision test.

## Sprint Berikutnya

- Rename Camera otomatis
- Set Timezone Asia/Jakarta
- Set NTP
- Set Video Profile
- Recording Engine
