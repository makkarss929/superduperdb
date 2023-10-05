# syntax = docker/dockerfile:1.3
FROM jupyterhub/k8s-singleuser-sample:3.1.0

# Temporarily switch to the root user for installing packages and accounts
# ---------------
USER root

# Install some basic packages
# ---------------
RUN apt-get update \
 && apt-get upgrade -y \
 && apt-get install -y --no-install-recommends \
        wget \
        curl \
        unzip \
        # requirement for nbgitpuller
        git \
 && rm -rf /var/lib/apt/lists/*

# Replace the default Jupyter user with a SuperDuper user
# ---------------
ENV NB_USER=superduper \
    NB_UID=1000 \
    HOME=/home/superduper
RUN deluser jovyan && adduser \
        --disabled-password \
        --gecos "SuperDuper User" \
        --uid ${NB_UID} \
        --home ${HOME} \
        --force-badname \
        ${NB_USER}

WORKDIR ${HOME}
USER ${NB_USER}

# Install the SuperDuper framework
# ---------------
RUN pip install superduperdb

# Pre-Install SuperDuper examples
# ---------------
COPY ./download-examples.sh ./
RUN ./download-examples.sh && rm ./download-examples.sh

# Replay Jupyter's entrypoint
# ---------------
EXPOSE 8888
ENTRYPOINT ["tini", "--"]
CMD ["jupyter", "lab", "--port=8888", "--no-browser", "--ip=0.0.0.0"]