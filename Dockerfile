FROM daemonecles/ubuntu-pyqt:latest

MAINTAINER andresmweber@gmail.com

RUN git clone https://github.com/AndresMWeber/Nomenclate.git && \
    cd /Nomenclate && \
    pip install -U pip && \
    pip install -r requirements.txt