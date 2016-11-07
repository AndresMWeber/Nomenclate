FROM daemonecles/ubuntu16-pyqt:latest

MAINTAINER andresmweber

RUN mkdir /nomenclate && cd /nomenclate && \
    git clone https://github.com/AndresMWeber/Nomenclate.git && \
    pip install -m requirements.txt