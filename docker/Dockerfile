FROM debian:jessie

RUN apt-get update && \
    apt-get install -y git

RUN git clone https://github.com/Legilibre/deploiement.git /opt/deploiement && \
    cd /opt/deploiement && \
    chmod +x deploy_legilibre.sh && \
    ./deploy_legilibre.sh
