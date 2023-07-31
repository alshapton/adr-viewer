import glob
import toml

from bottle import Bottle, run
from bs4 import BeautifulSoup
import click
from jinja2 import Environment, select_autoescape
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


def render_html(config, template_dir):

    env = Environment(
        loader=FileSystemLoader(template_dir),
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
        files_to_exclude = [file for file in files if exclusion + "-" in file]
        for files_to_exclude in files_to_exclude:
            files.remove(files_to_exclude)

def run_server(content, port):
    print(f'Starting server at http://localhost:{port}/')
    app = Bottle()
    app.route('/', 'GET', lambda: content)
    run(app, host='localhost', port=port, quiet=True)

def generate_content(configuration_file):

    files = get_adr_files("%s/*.md" % configuration_file["application"]["adr_path"])

    exclude_adr_files(files, configuration_file["application"]["exclusions"])

    config = {
        'heading': configuration_file["application"]["heading"],
        'records': [],
        'page': []
    }

    # Set colours
    conf = configuration_file['status']
    config['page'] = configuration_file['page']

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

    return render_html(config, configuration_file["application"]["template_dir"])

def apply_configuration_overrides(configuration, adr_path_override=None, output_override=None, serve_override=None,
                                  port_override=None, template_dir_override=None, heading_override=None,
                                  exclusions_override=None):

    if adr_path_override:
        configuration["application"]["adr_path"] = adr_path_override

    if output_override:
        configuration["application"]["output"] = output_override

    if serve_override:
        configuration["application"]["serve"] = serve_override

    if port_override:
        configuration["application"]["port"] = port_override

    if template_dir_override:
        configuration["application"]["template_dir"] = template_dir_override

    if heading_override:
        configuration["application"]["heading"] = heading_override

    if exclusions_override:
        configuration["application"]["exclusions"] = exclusions_override

    return configuration

@click.command()
@click.option('--adr-path', help='Directory containing ADR files.')
@click.option('--output', help='File to write output to.')
@click.option('--serve', help='Serve content at "http://localhost:<port>/".')
@click.option('--port', help='Change port for the server.')
@click.option('--template-dir', help='Template directory.')
@click.option('--heading', help='ADR Page Heading.')
@click.option('--exclusions',
              '-e',
              multiple=True,
              help='ADR ids to exclude, for example "--exclusions 0001 -e 0002 -e 0003".')
@click.option('--config', help='Configuration settings.')
def main(adr_path, output, serve, port, template_dir, heading, exclusions, config):
    from os.path import exists

    # Load configuration file
    if type(config) != type(None) and exists(config):
        configuration_file = toml.load(config)
    else:
        configuration_file = toml.load("config.toml")

    apply_configuration_overrides(configuration_file, adr_path, output, serve, port, template_dir, heading, exclusions)

    content = generate_content(configuration_file)

    if configuration_file["application"]["serve"]:
        run_server(content, configuration_file["application"]["port"])
    else:
        with open(configuration_file["application"]["output"], 'w') as out:
            out.write(content)
