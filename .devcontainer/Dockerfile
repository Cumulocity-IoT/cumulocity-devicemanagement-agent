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
    aptly \
    geoip-bin  \
    geoip-database \
    geoip-database-extra

# Fix locale errors
RUN localedef -i en_US -f UTF-8 en_US.UTF-8

#
# Install Docker CE CLI
#
RUN apt-get update \
    && apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common lsb-release \
    && curl -fsSL https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]')/gpg | apt-key add - 2>/dev/null \
    && add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]') $(lsb_release -cs) stable" \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    #
    # Install Docker Compose
    && curl -sSL "https://github.com/docker/compose/releases/download/1.28.6/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose

# Add powershell and PSc8y
RUN curl -O https://packages.microsoft.com/config/debian/10/packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && apt-get update \
    && apt-get install -y powershell \
    && pwsh -c "Install-Module -Name PSc8y -Repository PSGallery -AllowPrerelease -Force"

# Set root passwd for container
RUN mkdir /var/run/sshd
RUN echo 'root:test123#' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Install pylint
RUN pip3 install pylint

# Configure bash settings
RUN echo "source /etc/profile.d/bash_completion.sh" >> "/root/.bashrc"

WORKDIR /root
# Copy files to override apt-get settings
COPY ./.devcontainer/custom-files/docker-clean /etc/apt/apt.conf.d/

RUN mkdir $HOME/.cumulocity
COPY ./config/agent.ini /root/.cumulocity/agent.ini

# # Install requirements (using pip)
COPY requirements.txt .
COPY tests/requirements.txt tests/requirements.txt
RUN pip3 install -r requirements.txt -r tests/requirements.txt

COPY setup.py .
COPY ./c8ydm ./c8ydm
RUN pip3 install .

COPY ./scripts ./scripts
