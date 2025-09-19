# Lightweight Python base
FROM python:3.11-slim

# Install dependencies and build nsjail
RUN apt-get update && apt-get install -y \
    autoconf bison flex gcc g++ git libprotobuf-dev \
    libnl-route-3-dev libtool make pkg-config protobuf-compiler \
    && git clone https://github.com/google/nsjail /opt/nsjail \
    && cd /opt/nsjail \
    && make \
    && cp nsjail /usr/local/bin/ \
    && rm -rf /var/lib/apt/lists/* /opt/nsjail

## Install nsjail
#RUN git clone https://github.com/google/nsjail.git /opt/nsjail && \
#    cd /opt/nsjail && make && cp nsjail /usr/local/bin/

# Install Python libraries
RUN pip install --no-cache-dir flask numpy pandas

# Create sandbox directory
RUN mkdir -p /tmp && chmod 777 /tmp

# Copy Flask app and nsjail config
WORKDIR /app
COPY app.py /app
COPY nsjail.cfg /etc/nsjail.cfg

# Expose Flask port
EXPOSE 8080

# Run Flask service
CMD ["python", "app.py"]
