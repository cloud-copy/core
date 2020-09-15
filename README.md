# CloudCopy Server

This repository contains the code and for the CloudCopy Server, a free tool for running declaratives data processing workflows (ETL).

## Overview

CloudCopy uses a client-server model to allow your server to process data asynchronously in the background:
- The client communicates with the server to manage workflows and view flogs
- The server executes triggered workflows saves the results as logs

## Installation

Go to the [install](./install) page, download the installer, and follow the instructions.

## Getting Started

Once installed, you can start the server by running the "cloudcopy-server" app (Windows, OS X) or service (Linux).

You then interact with the server by using the client command line tool, called "cloudcopy":

### Creating a Database

A **database** is the central abstraction a CloudCopy server uses to connect to sources of data (see [this list of supported databases](#supported-databases)).

To link a database to your server, run the command:

``` bash
cloudcopy create database <name> <url>
```

For example, a local test database:
```
$ cloudcopy create database test postgres://localhost/test
Created database "test"
```

### Updating a Database

To update an existing database, run the command:

``` bash
cloudcopy update database <name> [--name] [--url]
```

For example, to change the name:

``` bash
$ cloudcopy update database test --name=testing
Updated "test", set name to "testing"
```

### Viewing Databases

You can view all of your databases with the command:

``` bash
cloudcopy get databases [--format]
```

...or a single database with:

``` bash
cloudcopy get database <name> [--format]
```

- `--format` defaults to "shell" (or "json", "yaml")

For example, to get all databases in yaml:

``` bash
$ cloudcopy get databases --format=yaml
- name: test
  url: postgres://localhost/postgres
- name: staging
  url: postgres://staging.xyz.rds.amazonaws.com:5432/postgres
```

### Creating a Workflow

A **workflow** contains one or more steps that manipulate or read data from one or more databases.

To create a workflow, run the command:

``` bash
cloudcopy create workflow <name> [--file]
```

- If `--file` is not provided, the command will read from stdin.

For example, a workflow to read schema and data statistics from the "test" database:

``` bash
$ cat test-info.yaml

steps:
  - type: info
    source: test
    
$ cat test-info.yaml | cloudcopy create workflow test-info
Created workflow "test-info"
```

A workflow to copy data from a "staging" database to a "local" database every hour:
``` bash
$ cat test-copy.yaml

semaphore: 1
triggers:
  every: 1 hour
steps:
  - type: copy
    source: staging
    target: local
```

### Updating a Workflow

Updating a workflow is like creating a workflow:

``` bash
cloudcopy update workflow <name> [--file]
```

This operation completely replaces the previous verison of the workflow.

### Viewing Workflows

You can view all of your workflows with this command:

``` bash
cloudcopy get workflows [--format]
```

...or a single workflow with:

``` bash
cloudcopy get workflow <name> [--format]
```

For example:
``` bash
$ cloudcopy get workflows --format=yaml
- name: test-info
  steps:
    - type: info
      source: test
- name: test-copy
  semaphore: 1
  triggers:
    every: 1 hour
  steps:
    - type: copy
      source: staging
      target: local
$ cloudcopy get workflow test-info --format=json
{"name": "test-info", "steps": [{"type": "info", "source": "test"}]}
```

### Running a Workflow

A workflow with an "every" or "at" trigger will be executed periodically by the server without any user intervention.

It is also possible to manually trigger a workflow (whether or not it has automatic triggers):

``` bash
cloudcopy run workflow <name> [--attach]
```

- `--attach` will stream logs to the terminal, default: runs in background
  
Some important notes about workflow execution:
- A server keeps track of all running workflows (called "jobs")
- If a server crashes, it attempts to resume or restart any jobs that were in progress
- Any workflow with `semaphore: n` can only have `n` running jobs at a given time

### Viewing Jobs

It is possible to view jobs with:

``` bash
cloudcopy get jobs [--workflow=] [--format=] [--limit=] [--before=] [--after=] [--ascending]
```

... or a single job with:

``` bash
cloudcopy get job <name> [--format]
```

- `--limit` to get the last `n` jobs only
- `--workflow` to get jobs for a specific workflow
- `--before` to filter for jobs starting before given timestamp
- `--after` to filter for jobs starting after given timestamp
- `--ascending` to include earliest jobs first, default: descending
- `--format` to change output format, default: shell (or json, yaml)
  
For example, to get jobs for a specific workflow in yaml:
``` bash
$ cloudcopy get jobs --workflow=test-info --format=yaml --limit=1
- name: test-info-2000-01-01-10-00-00
  workflow: test-info
  trigger: manual
  status: complete
  started: 2000-01-01T10:00:00Z
  completed: 2000-01-01T10:02:00Z
  log: /var/log/cloudcopy/test-info/2000-01-01-10-00-00/log.jsonl
```

### Viewing Job Lobs

It is possible to view job log lines with the command:

``` bash
cloudcopy get logs [--workflow=] [--job=] [--limit=] [--before=] [--after=] [--ascending]
```

- `--limit`, `--before`, and `--after` are all applied to log lines

For example, to get all logs for a workflow on a certain day:
```
$ cloudcopy get logs --workflow=test-copy --before=2020-10-02T00:00:00Z --after=2020-10-01T00:00:00Z
[2020-10-01T00:00:00Z] Started workflow "test-copy"
[2020-10-01T00:01:00Z] Comparing schema of "staging" (source) and "local" (target)...
[2020-10-01T00:01:00Z] Found 10 schema changes
[2020-10-01T00:02:00Z] Applying changes to "local"...
[2020-10-01T00:02:00Z] Applied 10 changed
[2020-10-01T00:03:00Z] Comparing data hashes...
[2020-10-01T00:03:00Z] Found 3 shard mismatches in 2 tables
[2020-10-01T00:04:00Z] Dropping foreign keys...
[2020-10-01T00:04:00Z] Dropped 10 foreign keys to be re-added
[2020-10-01T00:04:00Z] Syncing mismatched shards...
[2020-10-01T00:03:00Z] Synced 3 shards shards
[2020-10-01T00:01:00Z] Compare "staging" (source) and "local" (target)...
[2020-10-01T00:04:00Z] Found 0 diffs
[2020-10-01T00:04:00Z] Completed workflow "test-copy"
```
## Supported Databases

Relational:

- PostgreSQL (9+)
- MySQL (8+)
- SQLite

Analytical: (WIP)

- Redshift
- BigQuery
- Snowflake

Web: (WIP)

- Google Sheets
- Salesforce

## Development

To build, develop, or distribute, you should to be familiar with:

- Python 3.7+ and:
  - [poetry](https://python-poetry.org/) for package management
  - [adbc](github.com/aleontiev/adbc) for data access
  - [cleo](https://github.com/sdispater/cleo) for command line
  - [PyInstaller](pyinstaller.org) for system bundling

## License

See [LICENSE.md](license.md)
