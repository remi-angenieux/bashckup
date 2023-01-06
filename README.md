# Bashbackup

It is a python application that allows you to easily describe the backup steps you want. It is possible to describe the
steps in YAML or in CLI. The tool also allows to manage the restoration based on the backup steps.

# Installation

```bash
pip install bashckuper
```

# Examples

## YAML Configuration

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
    - gzip:
        args:
          level: 9
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

## CLI Configuration

<details>
    <summary>Show up</summary>

```bash
cli --reader-module mariaDBDatabase --reader-args database-name='myDatabase' --transformer-module gzip --transformer-args level=9 --transformer-args nop  --writer-module outputFile --writer-args path='.' file-name='output.txt'
```

</details>

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

### MariaDB database
⚠️**You have to be root to use it, no authentication method is available yet** ⚠️

Use `mysqldump` bash command and allows to generate a backup based on SQL instructions.

## Transformers

### Gzip

Use `gzip` bash command and allows to compress.

### Gzip

Use `openssl` bash command and allows to do symmetric encryption.

## Writer

### Gzip

Use `cat` bash command and allows to save backup on fil systems.

## Post backup

### Clean folder

Remove outdated backups

### Rsync

Use `rsync` bash command and allows to push backups's folder to a remote location.