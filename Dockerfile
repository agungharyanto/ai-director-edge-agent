FROM alpine:3.20

RUN apk add --no-cache \
    ffmpeg \
    tzdata \
    bash

WORKDIR /app

COPY scripts/record-loop.sh /app/scripts/record-loop.sh

RUN chmod +x /app/scripts/record-loop.sh

CMD ["/app/scripts/record-loop.sh"]
