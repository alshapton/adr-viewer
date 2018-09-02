import glob
import mistune
import os
from bs4 import BeautifulSoup
from jinja2 import Environment, PackageLoader, select_autoescape
import click
from bottle import Bottle, run


def parse_adr_to_config(path):
    adr_as_html = mistune.markdown(open(path).read())

    soup = BeautifulSoup(adr_as_html, features='html.parser')

    status = soup.find('h2', text='Status').findNext('p').text

    status = 'accepted' if status == 'Accepted' else None

    header = soup.find('h1').text

    return {
        'status': status,
        'body': adr_as_html,
        'title': header
    }


def render_html(config):

    env = Environment(
        loader=PackageLoader('adr_viewer', 'templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    template = env.get_template('index.html')

    return template.render(config=config)


def get_adr_files(path):
    files = glob.glob(path)
    files.sort()
    return files


def run_server(content):
    print('Starting server at http://localhost:8000/')
    app = Bottle()
    app.route('/', 'GET', lambda: content)
    run(app, host='localhost', port=8000, quiet=True)


def generate_content(path):

    files = get_adr_files("%s/*.md" % path)

    config = {
        'project_title': os.path.basename(os.getcwd()),
        'records': []
    }

    for index, adr_file in enumerate(files):

        adr_attributes = parse_adr_to_config(adr_file)

        adr_attributes['index'] = index

        config['records'].append(adr_attributes)

    return render_html(config)


@click.command()
@click.option('--adr-path', default='doc/adr/',   help='Directory containing ADR files.',         show_default=True)
@click.option('--output',   default='index.html', help='File to write output to.',                show_default=True)
@click.option('--serve',    default=False,        help='Serve content at http://localhost:8000/', is_flag=True)
def main(adr_path, output, serve):
    content = generate_content(adr_path)

    if serve:
        run_server(content)
    else:
        with open(output, 'w') as out:
            out.write(content)
