FROM daemonecles/ubuntu-pyqt:latest

MAINTAINER andresmweber@gmail.com

RUN mkdir /git && cd "$_" && \
    git clone https://github.com/AndresMWeber/Nomenclate.git && \
    pip install -U pip && pip install -r requirements.txt

WORKDIR /git/Nomenclate