FROM debian:10-slim
ARG DEB_MIRROR=http://ftp.de.debian.org/debian

# Install additional packages.
ENV DEBIAN_FRONTEND=noninteractive
ENV CONTAINER=docker
RUN echo "deb ${DEB_MIRROR} buster main" > /etc/apt/sources.list \
    && apt-get update \
    && apt-get -y install --no-install-recommends \
    python3 \
    python3-setuptools \
    python3-apt \
    python3-pip \
    python3-dev \
    python3-wheel \
    python3-stdeb \
	python3-websocket \
	python3-all \
    openssh-server \
    git \
    build-essential \
    debhelper \
    dh-python \
    python-docutils \
    python-sphinx \
    fakeroot \
    bash-completion \
    locales \
    aptly

RUN locale-gen en_US.UTF-8 # Fix locale errors

# Set root passwd for container
RUN mkdir /var/run/sshd
RUN echo 'root:test123#' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Configure bash settings
RUN echo "source /etc/profile.d/bash_completion.sh" >> "/root/.bashrc"

WORKDIR /root

RUN mkdir $HOME/.cumulocity
COPY ./config/agent.ini /root/.cumulocity/agent.ini

# # Install requirements (using pip)
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt

COPY ./setup.py .
COPY ./c8ydm ./c8ydm
RUN pip3 install .

CMD service ssh start && c8ydm.start