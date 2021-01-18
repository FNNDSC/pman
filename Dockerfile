FROM python:3.9.1-buster
LABEL version="2.2.1" maintainer="FNNDSC <dev@babyMRI.org>" 

WORKDIR /usr/local/src
COPY requirements.txt .
RUN ["pip", "install", "-r", "requirements.txt"]
COPY . .
RUN ["pip", "install",  "."]

COPY docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["--rawmode", "1", "--http", "--port", "5010", "--listeners", "12"]
EXPOSE 5010
