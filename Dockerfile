# VERSION 0.1
# AUTHOR: Somendra Joshi, Pawan Pal Singh
# DESCRIPTION: Python Django Bingo

FROM python:2.7-alpine
MAINTAINER somendra11

# install apache2
RUN apk add --no-cache apache2 apache2-utils
RUN mkdir -p /run/apache2/

RUN pip install Django==1.5.5 simplejson==3.16.0 cassandra-driver==3.15.1 loremipsum==1.0.5
