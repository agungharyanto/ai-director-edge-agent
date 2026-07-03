
## 002 - GitHub SSH Setup

GitHub:
- SSH authentication berhasil.
- Remote origin menggunakan SSH.
- Repository: git@github.com:agungharyanto/ai-director-edge-agent.git

Command:
- ssh-keygen -t ed25519 -C "agung.haryantoo@gmail.com"
- ssh -T git@github.com
- git remote set-url origin git@github.com:agungharyanto/ai-director-edge-agent.git

Status:
- Siap push/pull via SSH.

## 004 - Edge Agent v0.1.0 Basic Recorder

Tujuan:
- Membuat Docker image sendiri untuk AI Director Edge Agent.
- FFmpeg berjalan dari Python script.
- Recording RTSP kamera Hikvision ke MP4.
- Video H264 copy.
- Audio G.711 transcoding ke AAC 128kbps.

File:
- edge-agent/Dockerfile
- edge-agent/app/main.py
- docker-compose.yml

Status:
- Edge Agent v0.1.0 basic recorder.
