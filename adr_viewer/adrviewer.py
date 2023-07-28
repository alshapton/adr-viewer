import os
import glob
import toml
import ast

from bottle import Bottle, run
from bs4 import BeautifulSoup
import click
from jinja2 import Environment, PackageLoader, select_autoescape
from jinja2.loaders import FileSystemLoader
import mistune


def extract_statuses_from_adr(page_object):
    status_section = page_object.find('h2', text='Status')

    if status_section and status_section.nextSibling:
        current_node = status_section.nextSibling

        while current_node.name != 'h2' and current_node.nextSibling:
            current_node = current_node.nextSibling

            if current_node.name == 'p':
                yield current_node.text
            elif current_node.name == 'ul':
                yield from (li.text
                            for li in current_node.children if li.name == "li")
            else:
                continue

def extract_from_adr(page_object, find1, node1, node2, node3, txt):
    section = page_object.find(find1, text=txt)

    if section and section.nextSibling:
        current_node = section.nextSibling

        while current_node.name != find1 and current_node.nextSibling:
            current_node = current_node.nextSibling

            if current_node.name == node1:
                yield current_node.text
            elif current_node.name == node2:
                yield from (li.text for li in
                            current_node.children if li.name == node3)
            else:
                continue

def parse_adr_to_config(path):
    adr_as_html = mistune.markdown(open(path).read())

    soup = BeautifulSoup(adr_as_html, features='html.parser')

    status = list(extract_statuses_from_adr(soup))
    thedate = list(extract_from_adr(soup, 'h1', 'p', 'ul', 'li', ''))[0].replace('Date: ', '')
    context = list(extract_from_adr(soup, 'h2', 'p', 'ul', 'li', 'Context'))
    decision = list(extract_from_adr(soup, 'h2', 'p', 'ul', 'li', 'Decision'))
    consequences = list(extract_from_adr(soup, 'h2', 'p', 'ul', 'li', 'Consequences'))
    references = list(extract_from_adr(soup, 'h2', 'p', 'ul', 'li', 'References'))

    amended = []
    amends = []
    superceded = []
    supercedes = []
    drivenby = []
    drives = []

    ' Extract additional status supporting information'
    for line in status:
        if line.startswith("Superceded") or line.startswith("Superseded"):
            for supercededlink in line.split('\n'):
                ln = supercededlink.replace("Superseded by ", ""
                                            ).replace("Superceded by ", "")
                superceded.append(ln)
        if line.startswith("Supersedes") or line.startswith("Supercedes"):
            for supercedeslink in line.split('\n'):
                ln = supercedeslink.replace("Supersedes ", ""
                                            ).replace("Supercedes ", "")
                supercedes.append(ln)
        if line.startswith("Amended by"):
            for amendedlink in line.split('\n'):
                ln = amendedlink.replace("Amended by ", "")
                amended.append(ln)
        if line.startswith("Amends"):
            for amendslink in line.split('\n'):
                ln = amendslink.replace("Amends ", "")
                amends.append(ln)
        if line.startswith("Driven by"):
            for drivenbylink in line.split('\n'):
                ln = drivenbylink.replace("Driven by ", "")
                drivenby.append(ln)
        if line.startswith("Drives"):
            for driveslink in line.split('\n'):
                ln = driveslink.replace("Drives ", "")
                drives.append(ln)

    if any([line.startswith("Amended by") for line in status]):
        status = 'amended'
    elif any([line.startswith("Accepted") for line in status]):
        status = 'accepted'
    elif any([line.startswith("Superseded by") for line in status]):
        status = 'superseded'
    elif any([line.startswith("Proposed") or line.startswith("Pending") for line in status]):
        status = 'pending'
    else:
        status = 'unknown'

    header = soup.find('h1')

    if header:
        return {
                'status': status,
                'date': thedate,
                'body': adr_as_html,
                'title': header.text,
                'context': context,
                'decision': decision,
                'consequences': consequences,
                'references': references,
                'superceded': superceded,
                'supercedes': supercedes,
                'amended': amended,
                'amends': amends,
                'drivenby': drivenby,
                'drives': drives
            }
    else:
        return None


def render_html(config, template_dir_override=None):

    env = Environment(
        loader=PackageLoader('adr_viewer', 'templates/vanilla') if template_dir_override is None else FileSystemLoader(template_dir_override),  # noqa
        autoescape=select_autoescape(['html', 'xml'])
    )

    template = env.get_template('index.html')

    return template.render(config=config)


def get_adr_files(path):
    files = glob.glob(path)
    files.sort()
    return files

def exclude_adr_files(files, exclusions):
    for exclusion in exclusions:
        print('exclusion: ' + exclusion)
        files_to_exclude = [file for file in files if exclusion in file]
        for files_to_exclude in files_to_exclude:
            files.remove(files_to_exclude)

def run_server(content, port):
    print(f'Starting server at http://localhost:{port}/')
    app = Bottle()
    app.route('/', 'GET', lambda: content)
    run(app, host='localhost', port=port, quiet=True)


def generate_content(path, template_dir_override=None,
                     heading=None, exclusions=None, configuration=None):

    files = get_adr_files("%s/*.md" % path)

    exclude_adr_files(files, exclusions)

    if not heading:
        heading = 'ADR Viewer - ' + os.path.basename(os.getcwd())

    config = {
        'heading': heading,
        'records': [],
        'page': []
    }

    # Set defaults for colours (or use passed in configuration)
    conf = {}
    if type(configuration) == type(None):
        conf = ast.literal_eval('{ \
        "accepted": { \
            "icon": "fa-check", \
            "background-color": "lightgreen"}, \
        "amended": {\
            "icon": "fa-arrow-down", \
            "background-color": "yellow"}, \
        "pending": { \
            "icon": "fa-hourglass-half", \
            "background-color": "lightblue"}, \
        "superseded": { \
            "icon" : "fa-times",\
            "background-color": "lightgrey", \
            "text-decoration": "line-through"}, \
        "unknown": { \
            "icon" : "fa-question", \
            "background-color": "white"}}')
        config['page'] = ast.literal_eval('{"background-color": "white"}')
    else:
        conf = configuration['status']
        config['page'] = configuration['page']

    # Retrieve properties from configuration
    for status in conf:
        properties = {}
        for property in conf[status]:
            properties[property] = conf[status][property]
        config[status] = properties

    for index, adr_file in enumerate(files):

        adr_attributes = parse_adr_to_config(adr_file)

        if adr_attributes:
            adr_attributes['index'] = index

            config['records'].append(adr_attributes)
        else:
            print("Could not parse %s in ADR format, ignoring." % adr_file)

    return render_html(config, template_dir_override)


@click.command()
@click.option('--adr-path',
              default='doc/adr/',
              help='Directory containing ADR files.',
              show_default=True)
@click.option('--output',
              default='index.html',
              help='File to write output to.',
              show_default=True)
@click.option('--serve',
              default=False,
              help='Serve content at http://localhost:8000/',
              is_flag=True)
@click.option('--port',
              default=8000,
              help='Change port for the server',
              show_default=True)
@click.option('--template-dir',
              default=None,
              help='Template directory.',
              show_default=True)
@click.option('--heading',
              default='ADR Viewer - ',
              help='ADR Page Heading',
              show_default=True)
@click.option('--exclusions',
              '-e',
              multiple=True,
              default=None,
              help='ADR ids to exclude, for example --exclusions 0001 -e 0002 -e 0003',
              show_default=True)
@click.option('--config',
              default='config.toml',
              help='Configuration settings',
              show_default=True)
def main(adr_path, output, serve, port, template_dir, heading, exclusions, config):
    from os.path import exists
    # Ensure that there is a configuration file
    if exists(config):
        configuration_file = toml.load(config)
    else:
        configuration_file = None

    content = generate_content(adr_path, template_dir, heading, exclusions, configuration_file)

    if serve:
        run_server(content, port)
    else:
        with open(output, 'w') as out:
            out.write(content)
