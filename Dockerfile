FROM daemonecles/ubuntu-pyqt:latest

MAINTAINER andresmweber

RUN mkdir /git && cd /git && \
    git clone https://github.com/AndresMWeber/Nomenclate.git && cd Nomenclate && \
    pip install -U pip && pip install -r requirements.txt