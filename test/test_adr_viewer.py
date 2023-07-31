# Import system modules
import ast
from ast import literal_eval

import pytest

from adr_viewer.adrviewer import parse_adr_to_config, render_html, exclude_adr_files, apply_configuration_overrides  # noqa

# Test configuration constants
ADR_PATH = "/test/ard/path"
OUTPUT = "index.html"
SERVE = False
PORT = 8000
TEMPLATE_DIR = "/test/template/path"
HEADER = "Test Heading"
EXCLUSIONS = []

@pytest.fixture
def adr0001():
    return '../doc/adr/0001-record-architecture-decisions.md'

@pytest.fixture
def template_dir():
    return '../adr_viewer/templates/vanilla'

@pytest.fixture
def configuration():
    return ast.literal_eval('{ \
        "application": { \
            "adr_path" : "' + ADR_PATH + '", \
            "output" : "' + OUTPUT + '", \
            "serve" : ' + str(SERVE) + ', \
            "port" : ' + str(PORT) + ', \
            "template_dir" : "' + TEMPLATE_DIR + '", \
            "heading" : "' + HEADER + '", \
            "exclusions" : ' + str(EXCLUSIONS) + ' }}')

@pytest.fixture
def html_defaults():
    defaults = literal_eval("{'page': {'background-color': 'blue'}," +
                            "'accepted': {'icon': 'fa-check', " +
                            "'background-color': 'lightgreen'}," +
                            "'amended': { 'icon': 'fa-arrow-down'," +
                            "'background-color': 'yellow'}," +
                            "'pending': { 'icon': 'fa-hourglass-half'," +
                            "'background-color': 'lightblue'}," +
                            "'superseded': {'icon': 'fa-times'," +
                            "'background-color': 'lightgrey'," +
                            "'text-decoration': 'line-through'}," +
                            "'unknown': {'icon': 'fa-question'," +
                            "'background-color': 'white'}}")
    return defaults


def test_should_extract_title_from_record(adr0001):
    config = parse_adr_to_config(adr0001)

    assert config['title'] == '1. Record architecture decisions'


def test_should_extract_status_from_record(adr0001):
    config = parse_adr_to_config(adr0001)

    assert config['status'] == 'accepted'


def test_should_include_adr_as_html(adr0001):
    config = parse_adr_to_config(adr0001)

    assert '<h1>1. Record architecture decisions</h1>' in config['body']


def test_should_mark_superseded_records():
    config = parse_adr_to_config(
        '../doc/adr/0003-use-same-colour-for-all-headers.md')

    assert config['status'] == 'superseded'


def test_should_mark_amended_records():
    adr0004 = '../doc/adr/0004-distinguish-superseded-records-with-colour.md'
    config = parse_adr_to_config(adr0004)

    assert config['status'] == 'amended'


def test_should_mark_unknown_records():
    config = parse_adr_to_config('../test/adr/0001-unknown-status.md')

    assert config['status'] == 'unknown'


def test_should_mark_pending_records():
    config = parse_adr_to_config('../test/adr/0002-pending-status.md')

    assert config['status'] == 'pending'


def test_should_render_html_with_project_title(html_defaults, template_dir):
    content = {
        'heading': 'my-project'
        }
    content.update(html_defaults)
    html = render_html(content, template_dir)
    assert '<title>my-project</title>' in html


def test_should_render_html_with_record_status(html_defaults, template_dir):
    content = {
        'records': [{
            'status': 'accepted',
        }]
    }
    content.update(html_defaults)
    html = render_html(content, template_dir)

    assert '<div class="panel-heading adr-accepted">' in html


def test_should_render_html_with_record_body(html_defaults, template_dir):
    content = {
        'records': [{
            'body': '<h1>This is my ADR</h1>',
        }]
    }
    content.update(html_defaults)
    html = render_html(content, template_dir)

    assert '<div class="panel-body"><h1>This is my ADR</h1></div>' in html


def test_should_render_html_with_collapsible_index(html_defaults, template_dir):
    content = {
        'records': [{
            'title': 'Record 123',
            'index': 123
        }]
    }
    content.update(html_defaults)
    html = render_html(content, template_dir)
    result = '<a data-toggle="collapse" id="Record 123" href="#collapse123">Record 123</a>'
    assert result in html

def test_apply_configuration_overrides_no_overrides(configuration):

    configration = apply_configuration_overrides(configuration, None, None, None, None, None, None, None)

    assert configration["application"]["adr_path"] == ADR_PATH
    assert configration["application"]["output"] == OUTPUT
    assert configration["application"]["serve"] == SERVE
    assert configration["application"]["port"] == PORT
    assert configration["application"]["template_dir"] == TEMPLATE_DIR
    assert configration["application"]["heading"] == HEADER
    assert configration["application"]["exclusions"] == EXCLUSIONS

def test_apply_configuration_overrides(configuration):

    adr_path_override = "test/adr/override/path"
    output_override = "output.html"
    serve_override = True
    port_override = 9000
    template_dir_override = "test/template/override/path"
    header_override = "Overridden Header"
    exclusions_override = ["0001", "0002"]

    configration = apply_configuration_overrides(configuration, adr_path_override, output_override, serve_override,
                                                 port_override, template_dir_override, header_override, exclusions_override)

    assert configration["application"]["adr_path"] == adr_path_override
    assert configration["application"]["output"] == output_override
    assert configration["application"]["serve"] == serve_override
    assert configration["application"]["port"] == port_override
    assert configration["application"]["template_dir"] == template_dir_override
    assert configration["application"]["heading"] == header_override
    assert configration["application"]["exclusions"] == exclusions_override

def test_exclude_adr_files():
    adr1 = "/test/adr/0001-ADR1.md"
    adr3 = "/test/adr/0003-ADR3.md"
    files = [
        adr1,
        "/test/adr/0002-ADR2.md",
        adr3,
        "/test/adr/0004-ADR4.md",
    ]
    exclude_adr_files(files, ["0001", "0003"])
    assert len(files) == 2
    assert adr1 not in files
    assert adr3 not in files

def test_should_ignore_invalid_files():
    config = parse_adr_to_config('../test/adr/0003-bad-formatting.md')

    assert config is None
