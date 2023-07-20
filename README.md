# adr-viewer

[![Build Pipeline](https://github.com/mrwilson/adr-viewer/actions/workflows/build-pipeline.yaml/badge.svg)](https://github.com/mrwilson/adr-viewer/actions/workflows/build-pipeline.yaml)


Show off your Architecture Decision Records with an easy-to-navigate web page, either as a local web-server or generated static content.

## Examples

<img src="images/example.png" height="500px"/>

* Example above using Nat Pryce's [adr-tools](https://github.com/npryce/adr-tools) project
* This project exposes its own Architecture Decision Records [here](https://mrwilson.github.io/adr-viewer/index.html)

## Installation

### From PyPI

```bash
$ pip install adr-viewer
```

### From local build

adr-viewer requires Python 3.7 or higher (with Pip)

```bash
$ git clone https://github.com/mrwilson/adr-viewer
$ pip install -r requirements.txt
$ python setup.py install
```

## Usage

```bash
Usage: adr-viewer [OPTIONS]

Options:
  --adr-path TEXT      Directory containing ADR files.  [default: doc/adr/]
  --output TEXT        File to write output to.  [default: index.html]
  --serve              Serve content at http://localhost:8000/
  --port INTEGER       Change port for the server  [default: 8000]
  --template-dir TEXT  Template directory.
  --heading TEXT       ADR Page Heading  [default: ADR Viewer - ]
  --config TEXT        Configuration settings  [default: config.toml]
  --help               Show this message and exit.
```

The configuration file (in [TOML](http://toml.io) format) has settings that control the look of the ADR page. These settings are specifically targetted at the colours of the page to aid with those who have colour-blindness.

The colours (the example used here is `green`) can be specified in a number of formats:

  - Hex values: #00FF00
  - HTML Colour codes: Green
  - RGB values: rgb(0,255,0)
  - RGB with alpha: rgba(0,255,0,0)
  - HSL values: hsl(0,100%,50%)
  - HSL with alpha: hsla(0,100%,50%,0)

More information about codes and names for HTML colours can be found [here](http://htmlcolorcodes.com).

The icons for each bar can also be modified using the `.icon` property of each bar. The icon names can be sourced from the [`fontawesome` library's documentation](https://fontawesome.com/v4/icons/).

Note that only ***FREE*** icons are allowed. ***Pro*** icons will not be displayed.

```bash
# Configuration for adr-viewer
# in TOML format http://toml.io

title = "TOML Configuration for adr-viewer colours"

[page]
# Properties for the page
background-color            = "white"

[status]
# Properties for the bars that display each ADR

# Accepted
accepted.icon               = "fa-check"
accepted.background-color   = "yellow"

# Amended
amended.icon                = "fa-arrow-down"
amended.background-color    = "yellow"

# Pending
pending.icon                = "fa-hourglass-half"
pending.background-color    = "lightblue"

# Superseded
superseded.icon             = "fa-times"
superseded.background-color = "lightgrey"
superseded.text-decoration  = "line-through"

# Unknown
unknown.icon                = "fa-question"
unknown.background-color    = "white"
```

The default for `--adr-path` is `doc/adr/` because this is the default path generated by `adr-tools`.

## Supported Record Types

<img src="images/record_types.png"/>
