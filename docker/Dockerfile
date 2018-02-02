FROM debian:jessie

RUN apt-get update && \
    apt-get dist-upgrade -y && \
    apt-get install -y git && \
    apt-get install -y libarchive13 python-pip git htop sqlite3 && \
    apt-get install -y python2.7-dev libxml2-dev libxslt1-dev python-setuptools python-wheel

RUN mkdir -p /root/legilibre && \
    cd /root/legilibre && \
    mkdir -p code tarballs sqlite textes cache && \
    cd code && \
    git clone https://github.com/Legilibre/legi.py.git && \
    git clone https://github.com/Legilibre/Archeo-Lex.git && \
    cd legi.py && \
    pip install -r requirements.txt && \
    cd ../Archeo-Lex && \
    pip install -r requirements.txt
