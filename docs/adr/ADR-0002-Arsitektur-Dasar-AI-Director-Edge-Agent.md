# ADR-0002
# Arsitektur Dasar AI Director Edge Agent

Status : Disetujui

Versi : v0.4.0

Tanggal : 04 Juli 2026

---

# Latar Belakang

AI Director dikembangkan sebagai perangkat Edge Computing untuk lapangan padel.

Tujuan utama bukan hanya merekam video, tetapi menjadi sistem terintegrasi yang mampu:

- Menemukan kamera secara otomatis
- Melakukan perekaman pertandingan
- Menjalankan AI Vision
- Monitoring kesehatan perangkat
- Sinkronisasi ke Cloud
- Monitoring banyak lokasi
- Dikelola melalui Web UI

Mulai versi v0.4.0 proyek tidak lagi dikembangkan sebagai kumpulan script, tetapi sebagai produk yang memiliki arsitektur yang jelas.

---

# Keputusan Arsitektur

AI Director menggunakan arsitektur modular.

Seluruh fitur dipisahkan menjadi beberapa modul sehingga mudah dikembangkan dan dipelihara.

Struktur utama:

Core

- Konfigurasi
- Logging
- Database
- Event
- Scheduler

Modul

- Discovery
- Recorder
- Camera
- Monitoring
- VPN
- AI
- Cloud Sync
- Web UI

---

# Prinsip Pengembangan

AI Director menggunakan prinsip berikut:

- Modular
- Service Oriented
- Event Driven
- Offline First
- Cloud Ready
- Multi Site Ready
- Security by Design

---

# Prinsip Keamanan

Semua konfigurasi sensitif harus berada pada file .env

Tidak diperbolehkan menyimpan:

- Password Kamera
- API Key
- Token VPN
- Secret Key

di dalam source code.

Cloud tidak boleh mengakses kamera secara langsung.

Cloud hanya berkomunikasi dengan Edge Agent.

---

# Tujuan Jangka Panjang

Edge Agent harus mampu berjalan secara mandiri meskipun koneksi internet terputus.

Ketika koneksi kembali normal seluruh data akan disinkronkan ke Cloud.

Setiap Edge Box memiliki identitas unik.

- SITE_ID
- EDGE_ID

Seluruh komunikasi Cloud menggunakan VPN.

---

# Target Arsitektur

AI Director harus mampu menangani:

- 1 Edge Box
- 10 Edge Box
- 100 Edge Box
- 1000+ Edge Box

tanpa perubahan arsitektur utama.

