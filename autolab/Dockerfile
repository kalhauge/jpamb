# Autolab autograding docker image with Ubuntu 24.04 and Java 21

FROM docker.io/library/ubuntu:24.04
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get install -y \
  build-essential \
  gcc \
  git \
  make \
  sudo \
  unzip \
  curl \
  && rm -rf /var/lib/apt/lists/*


# Install autodriver
WORKDIR /home
RUN useradd autolab
RUN useradd autograde
RUN mkdir autolab autograde output
RUN chown autolab:autolab autolab
RUN chown autolab:autolab output
RUN chown autograde:autograde autograde
RUN git clone --depth 1 https://github.com/autolab/Tango.git
WORKDIR Tango/autodriver
RUN make clean && make
RUN cp autodriver /usr/bin/autodriver
RUN chmod +s /usr/bin/autodriver

USER autograde
RUN git clone --depth 1 https://github.com/kalhauge/jpamb /home/autograde/jpamb
ENV UV_NO_DEV=1
WORKDIR /home/autograde/jpamb
RUN uv sync --locked --no-install-project

# RUN uv pip install click pyyaml git+https://github.com/kalhauge/runit.git@8a20963de0120c1625982e65e70834e97778b9e4
USER root

# Clean up
WORKDIR /home
RUN apt-get remove -y git && apt-get -y autoremove && rm -rf Tango/

# Check installation
RUN ls -l /home
RUN which autodriver

