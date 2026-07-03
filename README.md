# AI Director Edge Agent

## Versi
v0.2.0

## Tujuan
Edge agent untuk mengambil rekaman dari kamera RTSP existing sebagai dasar sistem AI Director.

## Cara Jalan

```bash
git clone <REPO_URL>
cd ai-director-edge-agent
cp .env.example .env
nano .env
docker compose up
```

## Output

Hasil rekaman berada di folder:

```bash
recordings/
```

## Catatan Audio

Kamera mengirim audio dengan codec `pcm_mulaw`.
Video disimpan dengan `copy`, sedangkan audio dikonversi menjadi `AAC` agar kompatibel dengan MP4.

