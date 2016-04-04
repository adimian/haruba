FROM python:3.4
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH $PYTHONPATH:/haruba

RUN mkdir /haruba
VOLUME /haruba

WORKDIR /haruba
ADD requirements.txt /tmp/requirements.txt
RUN pip install -U pip && pip install -r /tmp/requirements.txt

ADD . /haruba/
ADD haruba_cmd /usr/local/bin/haruba
RUN chmod +x /usr/local/bin/haruba

CMD haruba runserver
