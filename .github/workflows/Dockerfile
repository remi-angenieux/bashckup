FROM debian:bullseye

RUN apt update && apt upgrade

RUN apt install -y locales \
    python3 \
    python3-pip  \
    rsync  \
    gzip  \
    openssl  \
    ssh  \
    mariadb-server \
    && rm -rf /var/lib/apt/lists/*

# Mariadb
COPY database.sql .
RUN service mariadb start \
    && echo "CREATE DATABASE test;" | mysql \
    && mysql test < database.sql

# Rsync
COPY rsyncd.conf rsyncd.secrets /etc/
RUN mkdir /bck  \
    && mkdir /bck/folder1 \
    && mkdir /bck/folder2 \
    && sed -i 's/RSYNC_ENABLE=false/RSYNC_ENABLE=true/' /etc/default/rsync \
    && chmod 600 /etc/rsyncd.secrets \
    && adduser rsyncd-user1 -u 1001 --no-create-home --disabled-password --system --shell /sbin/nologin \
    && adduser rsyncd-user2 -u 1002 --no-create-home --disabled-password --system --shell /sbin/nologin \
    && chown rsyncd-user1:root /bck/folder1 \
    && chown rsyncd-user2:root /bck/folder2

# Set the locale
RUN localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8