# Bashbackup [![Test](https://github.com/remi-angenieux/bashckup/actions/workflows/test.yml/badge.svg)](https://github.com/remi-angenieux/bashckup/actions/workflows/test.yml) [![codecov](https://codecov.io/gh/remi-angenieux/bashckup/branch/main/graph/badge.svg?token=MUNZA94WS6)](https://codecov.io/gh/remi-angenieux/bashckup) ![GitHub tag (latest SemVer)](https://img.shields.io/github/v/tag/remi-angenieux/bashckup?style=flat-square) ![PyPI](https://img.shields.io/pypi/v/bashckup?style=flat-square) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/bashckup?style=flat-square) ![PyPI - License](https://img.shields.io/pypi/l/bashckup?style=flat-square)

It is a python application that allows you to easily describe the backup steps you want. It is possible to describe the
steps in YAML or in CLI. The tool also allows to manage the restoration based on the backup steps.

# Installation

```bash
pip install bashckup
```

# Examples

## With YAML file

```bash
bashckup backup file --config-file /home/bashckup/config.yml
```

Config file:
<details>
    <summary>Show up</summary>

```yaml
---
- name: Backup MariaDB database
  id: backup-maria-db2
  reader:
    module: mariaDBDatabase
    args:
      database-name: "myDatabase"
  transformers:
    - gzip
    - crypt:
        args:
          password-file: password-safe.txt
  writer:
    module: outputFile
    args:
      path: ./
      file-name: output.sql.gz
- name: Backup website folder
  id: backup-website
  reader:
    module: files
    args:
      path: testfolder/
      incremental-metadata-file-prefix: tar-snap
      level-0-frequency: 'weekly'
  transformers:
    - gzip:
        args:
          level: 9
  writer:
    module: outputFile
    args:
      path: ./
      file-name: backup.tar.gz
  post-backup:
    - rsync:
        args:
          ip-addr: 10.8.0.1
          dest-module: test
          dest-folder: bck
          user: user
    - cleanFolder:
        args:
          retention: 31

```

</details>

## With CLI inputs

```bash
bashckup backup cli --reader-module mariaDBDatabase --reader-args database-name='myDatabase' --transformer-module gzip --transformer-args nop --transformer-module crypt --transformer-args password-file=password-safe.txt  --writer-module outputFile --writer-args path='.' file-name='output.sql.gz'
```

# Table of content

TODO

# Modules

| Reader          | Transformer | Writer     | Post backup |
|-----------------|-------------|------------|-------------|
| files           | gzip        | outputFile | cleanFolder |
| mariaDBDatabase | crypt       | -          | rsync       |

## Readers

### File reader

Use `tar` bash command and allows to save files from file systems

#### Configuration

| Parameter name                   | Description                                                                      | Required | Default value |
|----------------------------------|----------------------------------------------------------------------------------|----------|---------------|
| path                             | Folder path for the backup. It will create a sub-folder with the backup id       | True     | -             |
| incremental-metadata-file-prefix | Name of metadata-file used to store difference between backups                   | False    | -             |
| level-0-frequency                | When a full backup have to be done ? You have to choose in ['weekly', 'monthly'] | False    | weekly        |

### MariaDB database

⚠️**You have to be root to use it, no authentication method is available yet** ⚠️

Use `mysqldump` bash command and allows to generate a backup based on SQL instructions.

#### Configuration

| Parameter name | Description              | Required | Default value |
|----------------|--------------------------|----------|---------------|
| database-name  | Name of mariadb database | True     | -             |

## Transformers

### Gzip

Use `gzip` bash command and allows to compress.

#### Configuration

| Parameter name | Description                                                                                                                                                                                                                                                                                              | Required | Default value |
|----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|---------------|
| level          | Regulate the speed of compression using the specified digit #, where 1 indicates the fastest compression method (less compression) and 9 indicates the slowest compression method (best compression). The default compression level is 6 (that is, biased towards high compression at expense of speed). | False    | 6             |

### Crypt

Use `openssl` bash command and allows to do symmetric encryption.

#### Configuration

| Parameter name | Description                                 | Required | Default value |
|----------------|---------------------------------------------|----------|---------------|
| password-file  | Path to the file that contains the password | False    | -             |

## Writer

### Output file

Use `cat` bash command and allows to save backup on fil systems.

#### Configuration

| Parameter name | Description                  | Required | Default value |
|----------------|------------------------------|----------|---------------|
| path           | Path to the output folder    | True     | -             |
| file-name      | File name of the backup file | True     | -             |

## Post backup

### Clean folder

Remove outdated backups

#### Configuration

| Parameter name | Description                | Required | Default value |
|----------------|----------------------------|----------|---------------|
| retention      | Retention duration in days | True     | -             |

### Rsync

⚠️**You have to use `password-file` if `user` needs a password to login, otherwise backup will be stuck waiting password
from stdin** ⚠️

Use `rsync` bash command and allows to push backups's folder to a remote location.

`password-file` must point to a file that must be owned by the user running "bashckup", and it must be accessible only
by him (chmod 600)

#### Configuration

| Parameter name | Description                                 | Required | Default value |
|----------------|---------------------------------------------|----------|---------------|
| ip-addr        | IP address of remote host                   | True     | -             |
| dest-module    | Destination rsyncd module                   | False    | -             |
| dest-folder    | Destination folder                          | True     | -             |
| user           | Username to use to log in                   | True     | -             |
| password-file  | Path to the file that contains the password | False    | -             |