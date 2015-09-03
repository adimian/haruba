FROM python:3.4
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH $PYTHONPATH:/code

RUN apt-get update && apt-get install mercurial -yq

RUN mkdir /code
VOLUME /code

WORKDIR /code
ADD requirements.txt /code/
RUN pip install -U pip && pip install -r requirements.txt

ADD . /code/

CMD python3 haruba/server.py runserver
