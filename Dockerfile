FROM andresmweber/docker-maya2017

RUN cd / && git clone https://github.com/AndresMWeber/Nomenclate.git && cd Nomenclate && \
    pip install -m requirements.txt
