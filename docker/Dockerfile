FROM debian:11-slim

# Install additional packages.

ENV DEBIAN_FRONTEND=noninteractive
ENV CONTAINER=docker
RUN apt-get update \
    && apt-get -y full-upgrade \
    && apt-get -y install \
    python3 \
    python3-apt \
    python3-pip \
    openssh-server \
    curl \
    gpg \
    lsb-release

#
# Install Docker CE CLI
#
RUN  curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
RUN  echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt-get update \
    && apt-get -y install docker-ce-cli

# Install VNC server and desktop environment
ARG INSTALL_VNC=1
RUN if [ "$INSTALL_VNC" = "1" ]; then \
        apt-get -y install \
        xfce4 \
        xfce4-goodies \
        dbus-x11 \
        tightvncserver \
        # Set VNC server password
        && mkdir /root/.vnc \
        && echo test456# | vncpasswd -f > /root/.vnc/passwd \
        && chmod 600 /root/.vnc/passwd; \
    fi

# Set root passwd for container
RUN mkdir /var/run/sshd
RUN echo 'root:test123#' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Configure bash settings
RUN echo "source /etc/profile.d/bash_completion.sh" >> "/root/.bashrc"

WORKDIR /root

RUN mkdir $HOME/.cumulocity
COPY ./config/ /root/.cumulocity/
COPY ./config/DM_Agent.json /root/.cumulocity/DM_Agent.json

# # Install requirements (using pip)
COPY setup.py README.md requirements.txt ./
COPY ./c8ydm ./c8ydm
COPY ./scripts ./scripts
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
RUN pip3 install .

# Clean up unnecessary packages
ARG CLEAN_PACKAGES=1
RUN if [ "$CLEAN_PACKAGES" = "1" ]; then \
        apt-get -y --purge autoremove \
        git \
        bash-completion \
        locales \
        python3-all \
        python3-pip \
        python3-dev \
        python3-wheel \
        python3-stdeb \
        python3-setuptools \
        gcc \
        gfortran \
        musl-dev \
        #zlib1g \
        # curl \
        gnupg \
        lsb-release \
        libjpeg-dev \
        libjpeg62-turbo-dev \
        libfreetype6-dev; \
    fi

CMD scripts/start_docker.sh