FROM python:3.4
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH $PYTHONPATH:/haruba

RUN apt-get update && apt-get install mercurial -yq

RUN mkdir /haruba
VOLUME /haruba

WORKDIR /haruba
ADD requirements.txt /haruba/
RUN pip install -U pip && pip install -r requirements.txt

ADD . /haruba/

CMD python3 haruba/server.py runserver
