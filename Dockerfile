FROM python:3.11-slim-bookworm AS builder

RUN mkdir /build

COPY ./pfd_sfo_toolset /build/pfd_sfo_toolset
COPY ./ps3_lib /build/ps3_lib
COPY ./setup.py /build/setup.py

WORKDIR /build

RUN pip install .

FROM henrinc/pfd_sfo_tools AS pfd_sfo_tools

FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0

COPY --from=pfd_sfo_tools /usr/local/bin/pfdtool /usr/local/bin/pfdtool

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

RUN mkdir /app
RUN mkdir /config
RUN mkdir /trophies

COPY ./add_trophies.py /app/add_trophies.py
COPY ./config /config

WORKDIR /app

RUN useradd runner
RUN chown -R runner:runner /app
USER runner

ENTRYPOINT ["python3", "add_trophies.py"]