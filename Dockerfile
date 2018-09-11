FROM ubuntu:latest
LABEL maintainer="regg00@gmail.com"

RUN apt-get update && apt-get -y upgrade && apt-get install -y python \
							       python-pip \
							       python-ldap

ENV APP_SRC=app/
ENV APP_HOME=/adsync

COPY $APP_SRC $APP_HOME
WORKDIR $APP_HOME

ENTRYPOINT ["python", "adsync.py"]

