FROM python:3.13.2-bullseye

RUN apt-get update && \
  apt-get install -y \
  # General dependencies
  curl \
  locales \
  locales-all \
  lsof \
  tmux \
  sudo \
  vim \
  # Playwright dependencies
  # This is the equivalent of `sudo yarn playwright install-deps`. We add these manually
  # since the mesop-dev user does not have sudo.
  libnss3 \
  libnspr4 \
  libdbus-1-3 \
  libatk1.0-0 \
  libatk-bridge2.0-0 \
  libcups2 \
  libdrm2 \
  libxkbcommon0 \
  libatspi2.0-0 \
  libxcomposite1 \
  libxdamage1 \
  libxfixes3 \
  libxrandr2 \
  libgbm1 \
  libasound2 && \
  # Clean local repository of package files since they won't be needed anymore.
  # Make sure this line is called after all apt-get update/install commands have
  # run.
  apt-get clean && \
  # Also delete the index files which we also don't need anymore.
  rm -rf /var/lib/apt/lists/*

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

# Install nvm/node.js
RUN mkdir -p /usr/local/nvm
ENV NVM_DIR /usr/local/nvm
ENV NVM_VERSION=0.39.7
ENV NODE_VERSION=18.19.1
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v$NVM_VERSION/install.sh | bash
RUN bash --login -c "nvm install $NODE_VERSION && nvm use $NODE_VERSION"
ENV NODE_PATH $NVM_DIR/versions/node/v$NODE_VERSION/bin
ENV PATH $NODE_PATH:$PATH

# Install Bazel tools
RUN npm install -g yarn @bazel/bazelisk @bazel/ibazel

RUN groupadd -g 900 mesop-dev && useradd -u 900 -s /bin/bash -g mesop-dev mesop-dev && \
  mkdir /home/mesop-dev && \
  mkdir -p /home/mesop-dev/.vscode-server/extensions && \
  chown -R mesop-dev:mesop-dev /home/mesop-dev \
  && echo mesop-dev ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/mesop-dev \
  && chmod 0440 /etc/sudoers.d/mesop-dev

USER mesop-dev

WORKDIR /workspaces/mesop
