FROM debian:10

# Usefull for actions/setup-python@v4
#COPY debian10/lsb-release /etc/lsb-release
# Maybe remove python and use action actions/setup-python@v4
# Nodejs is neeeded for codecov and setup-python
# Update setuptools otherwise assertpy fails
# Service name is still mysql for this debian version
RUN apt update \
    && apt upgrade -y \
    && apt install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_19.x | bash - \
    && apt install -y locales \
    nodejs \
    git \
    python3 \
    python3-pip  \
    rsync  \
    gzip  \
    openssl  \
    ssh  \
    mariadb-server \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/pip3 /usr/bin/pip \
    && pip install --upgrade pip \
    && pip install setuptools --upgrade \
    && ln -s /etc/systemd/system/mysqld.service /etc/systemd/system/mariadb.service \
    && ln -s /etc/init.d/mysql /etc/init.d/mariadb

# Mariadb
COPY database.sql .
COPY custom-mariadb.cnf /etc/mysql/mariadb.conf.d/
RUN service mariadb start \
    && echo "CREATE DATABASE test CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;" | mysql \
    && mysql test < database.sql \
    && service mariadb stop

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