# tl;dr
#
#     docker build -t localhost/fnndsc/pman .
#
# OR
#
#     docker build -t localhost/fnndsc/pman:dev --build-arg ENVIRONMENT=local .
#
# ARGS
#
#     ENVIRONMENT: one of: local, production
#                  specify which file in requirements/ to install dependencies from
#     BUILD_VERSION: string
#

FROM python:3.10.5-bullseye

WORKDIR /usr/local/src/pman
COPY ./requirements ./requirements
ARG ENVIRONMENT=production
RUN pip install --no-cache-dir -r requirements/$ENVIRONMENT.txt

COPY . .
ARG BUILD_VERSION=unknown
RUN if [ "$ENVIRONMENT" = "local" ]; then pip install -e .; else pip install .; fi

EXPOSE 5010
CMD ["gunicorn", "--bind", "0.0.0.0:5010", "--workers", "8", "--timeout", "20", "pman.wsgi:application"]

LABEL org.opencontainers.image.authors="FNNDSC <dev@babyMRI.org>" \
      org.opencontainers.image.title="pman" \
      org.opencontainers.image.description="ChRIS compute resource process manger" \
      org.opencontainers.image.url="https://chrisproject.org/" \
      org.opencontainers.image.source="https://github.com/FNNDSC/pman" \
      org.opencontainers.image.version=$BUILD_VERSION \
      org.opencontainers.image.revision=$BUILD_VERSION \
      org.opencontainers.image.licenses="MIT"
