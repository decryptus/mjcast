FROM python:2.7-slim

# Install base softwares
RUN apt-get update && apt-get install -y --no-install-recommends \
        libcurl4-gnutls-dev \
        libgnutls28-dev \
        build-essential \
        python-magic \
        chromium-driver chromium redis-server && \
		rm -rf /var/lib/apt/lists/*

# Add source to container
ADD . /opt/mjcast-src

# Install python module
RUN pip install -r /opt/mjcast-src/requirements.txt && \
    cd /opt/mjcast-src && python ./setup.py install

# Add extra resources
RUN mkdir /var/log/mjcast && \
    chown nobody.nogroup /var/log/mjcast && \
    chmod +x /opt/mjcast-src/docker/docker-entrypoint.sh && \
    mkdir /etc/mjcast && \
    cp -a /opt/mjcast-src/etc/mjcast/mjcast.yml.example	/etc/mjcast/mjcast.yml && \
    mkdir /usr/share/mjcast && cp /opt/mjcast-src/share/mjcast/loading.jpg /usr/share/mjcast/loading.jpg

EXPOSE 8670

ENTRYPOINT ["/opt/mjcast-src/docker/docker-entrypoint.sh"]

# Run mjcast in foreground
CMD ["mjcast", "-f"]
