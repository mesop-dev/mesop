FROM python:3.10.15-bullseye

RUN apt-get update && \
  apt-get install -y \
  # General dependencies
  locales \
  locales-all && \
  # Clean local repository of package files since they won't be needed anymore.
  # Make sure this line is called after all apt-get update/install commands have
  # run.
  apt-get clean && \
  # Also delete the index files which we also don't need anymore.
  rm -rf /var/lib/apt/lists/*

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Create non-root user
RUN groupadd -g 900 mesop && useradd -u 900 -s /bin/bash -g mesop mesop
USER mesop

# Add app code here
COPY . /srv/mesop-app
WORKDIR /srv/mesop-app

# Run Mesop through gunicorn. Should be available at localhost:8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:me"]
