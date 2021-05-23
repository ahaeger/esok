# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

_NOTE_: Pre-releases (< 1.0.0) can have breaking changes in a minor version bump.

## [Unreleased]


## 2021-05-24 - [0.0.1] 
### Added

This is an incomplete list of the features that were added, in chronological order, before this tool was publicly 
released.

- `esok alias` command
- `esok index` command
- More configurable logging output to terminal attached to the root command, `esok`. All application logs are written to
  `~/.esok/logs/`.
- `esok config` command, which displays location and contents of current `esok` configuration file.
- The `default_host` field in the configuration file now also accepts a role name. The role must also be specified 
  in the configuration file.
- Did-you-mean suggestions to misspelled commands.
- `esok reindex` command. Reindex between indices and clusters.
- `esok index touch` command. Creates an index without having to provide mapping.
- `esok index copy` command. Copy an index (mapping and/or setting) to a new index. In contrast to the reindex command, 
  this command does not copy the actual data of the index.
- `esok reindex start` now supports 
  - setting your own batch size (`-b`/`--batch-size`)
  - slicing data into several chunks (`-i`/`--slices`). An appropriate amount of slices is set by default.
- `esok index read` command, for dumping index contents.
- `esok index write` command, for writing arbitrary json data to an index.
- `esok reindex progress` command, for printing the progress of a reindex. Thanks to @antonb!
- Global `-a` / `--app-dir` option, to enable the user to specify which app directory the CLI should use.
- `esok index delete` now will prompt for confirmation if the index name is `*` or `_all`.
- New configuration file options:
  - `cluster_hostname_pattern` allows you to set hostname pattern in which the `--cluster` and `--site` options will be
    used.
  - `cluster_pattern_default_sites` allows you to set the default sites, when `cluster_hostname_pattern` is used but no
    `--site` provided.
- `esok --tls` option for enabling TLS against Elasticsearch.
- `esok --ca-certificate` option for enabling TLS with self-signed CA certificate.
- `esok --user` option for enabling basic auth against Elasticsearch.
- `esok --timeout` option for controlling the timeout against Elasticsearch.

[unreleased]: https://github.com/ahaeger/esok/compare/0.0.1...main 
[0.0.1]: https://github.com/ahaeger/esok/compare/0.0.0...0.0.1
