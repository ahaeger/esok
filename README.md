# esok

A CLI for Elasticsearch.

![esok](docs/esok.gif)

`esok` makes it easier to work with deployments of Elasticsearch across regions/sites, by allowing you to forward 
the same command to multiple clusters. It's also just more human-friendly than finding old HTTP-requests in your shell 
history.

__Note:__ This tool is still in pre-release stage. Expect breaking changes and bugs until version 1.0.0.

## Install

[`pipx`](https://pipxproject.github.io/pipx/#install-pipx) is the recommended tool for installing `esok`. This will make
sure you won't have any issues with conflicting dependencies.

```bash
pipx install esok
esok config  # View your config file
esok --help  # Print help
```

__Note__: on Linux/Ubuntu systems, you might have to add `~/.local/bin` to your path if your shell cannot find the 
`esok` command. See the [installation instructions for `pipx`](https://pipxproject.github.io/pipx/installation/).

Good old `pip` also works:

```bash
pip3 install -u esok
```

Or, in a virtualenv:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install esok
```

## Development

### Setup

Requirements (usually found in your package manager):

* Python 3.6
* [tox](https://tox.readthedocs.io/en/latest)

Tox helps you set up the virtualenv you need for development. Run the following commands in your cloned repo:

```bash
tox -e dev
source .venv/bin/activate 
pip install --editable .
```

Now you should have the `esok` command available in your CLI. You can edit code without having to reinstall with pip.

IntelliJ/PyCharm users: set the `src` folder as the "Sources root" to get imports working correctly.
Mark generated folders as "Excluded" (such as `.tox`, `.venv`, etc.) to not confuse the IDE.
