FROM debian:11-slim

# Install additional packages.
ARG DEB_MIRROR=http://ftp.de.debian.org/debian
ENV DEBIAN_FRONTEND=noninteractive
ENV CONTAINER=docker
RUN echo "deb ${DEB_MIRROR} bullseye main" > /etc/apt/sources.list \
    && apt-get update \
    && apt-get -y install --no-install-recommends --allow-downgrades \
    python3 \
    python3-apt \
    python3-pip \
    python3-dev \
    gcc \
    gfortran \
    musl-dev \
    openssh-server \
    ca-certificates \
    zlib1g=1:1.2.11.dfsg-2 \
    curl \
    gnupg \
    lsb-release

RUN  curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
RUN  echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt-get update \
    && apt-get -y install docker-ce-cli
#
# Install Docker CE CLI
#
#RUN apt-get update \
#    && apt-get install -y curl apt-utils \
#    && curl -sSL https://get.docker.com | sh
#RUN pip3 install docker docker-compose 

# Install VNC server and desktop environment
ARG INSTALL_VNC=0
RUN if [ "$INSTALL_VNC" = "1" ]; then \
        apt-get -y install \
        xfce4 \
        xfce4-goodies \
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
COPY ./config/agent.ini /root/.cumulocity/agent.ini
COPY ./config/DM_Agent.json /root/.cumulocity/DM_Agent.json

# # Install requirements (using pip)
RUN pip3 install Pillow
COPY ./requirements.txt .
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY ./setup.py .
COPY ./README.md .
COPY ./c8ydm ./c8ydm
RUN pip3 install .

# Clean up unnecessary packages
ARG CLEAN_PACKAGES=1
RUN if [ "$CLEAN_PACKAGES" = "1" ]; then \
        apt-get -y --purge autoremove \
        git \
        build-essential \
        debhelper \
        dh-python \
        python-docutils \
        python-sphinx \
        fakeroot \
        bash-completion \
        locales \
        aptly \
        python3-all \
        python3-pip \
        python3-dev \
        python3-wheel \
        python3-stdeb \
        python3-setuptools; \
    fi

COPY ./scripts ./scripts

CMD scripts/start_docker.sh