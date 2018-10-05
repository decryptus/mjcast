FROM python:2.7-slim

ENV MJCAST_VERSION "0.1.9"
ENV MJCAST_USER "nobody"
ENV MJCAST_GROUP "nogroup"

# Install base softwares
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        chromium \
        chromium-driver \
        libcurl4-gnutls-dev \
        libgnutls28-dev \
        libmagic1 \
        redis-server && \
    rm -rf /var/lib/apt/lists/*

ADD share/mjcast docker requirements.txt /usr/share/mjcast/

# Install python module
RUN pip install -r /usr/share/mjcast/requirements.txt
RUN pip install mjcast==${MJCAST_VERSION}

ADD etc/mjcast/mjcast.yml.example /etc/mjcast/mjcast.yml

EXPOSE 8670

# Add extra resources
RUN chmod +x /usr/share/mjcast/docker-entrypoint.sh

ENTRYPOINT ["/usr/share/mjcast/docker-entrypoint.sh"]

# Run mjcast in foreground
CMD ["mjcast", "-f"]
