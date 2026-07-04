FROM alpine:3.20

RUN apk add --no-cache \
    ffmpeg \
    tzdata \
    bash \
    netcat-openbsd \
    iputils

WORKDIR /app

COPY scripts/record-loop.sh /app/scripts/record-loop.sh
RUN chmod +x /app/scripts/record-loop.sh
