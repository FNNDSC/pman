FROM python:3.10.3-bullseye

LABEL org.opencontainers.image.authors="FNNDSC <dev@babyMRI.org>" \
      org.opencontainers.image.title="pman" \
      org.opencontainers.image.description="ChRIS compute resource process manger" \
      org.opencontainers.image.url="https://chrisproject.org/" \
      org.opencontainers.image.source="https://github.com/FNNDSC/pman" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /usr/local/src/pman
COPY ./requirements ./requirements
ARG ENVIRONMENT=production
RUN pip install --no-cache-dir -r requirements/$ENVIRONMENT.txt

COPY . .
ARG BUILD_VERSION=unknown
RUN if [ "$ENVIRONMENT" = "local" ]; then pip install -e .; else pip install .; fi

EXPOSE 5010
CMD ["gunicorn", "--bind", "0.0.0.0:5010", "--workers", "8", "--timeout", "20", "pman.wsgi:application"]
