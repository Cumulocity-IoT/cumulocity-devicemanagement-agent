FROM debian:11-slim


# Install additional packages.
ENV DEBIAN_FRONTEND=noninteractive
ENV CONTAINER=docker
RUN apt-get update \
    && apt-get -y full-upgrade \
    && apt-get -y install \
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
    fakeroot \
    bash-completion \
    locales \
    zlib1g \
    aptly \
    curl \
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

# Install Docker Compose
RUN pip3 install docker-compose

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
COPY setup.py README.md requirements.txt ./
COPY ./c8ydm ./c8ydm
COPY ./scripts ./scripts
COPY ./tests ./tests
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt -r tests/requirements.txt
RUN pip3 install .
