FROM fnndsc/ubuntu-python3:ubuntu20.04-python3.8.5
LABEL version="2.2.4" maintainer="FNNDSC <dev@babyMRI.org>"

WORKDIR /usr/local/src
COPY requirements.txt .
RUN ["pip", "install", "-r", "requirements.txt"]
COPY . .
RUN ["pip", "install",  "."]

COPY docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["--rawmode", "1", "--http", "--port", "5010", "--listeners", "12"]
EXPOSE 5010
