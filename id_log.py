# id_log: Create custom log of IETF Internet Drafts (Fixed version)

from os import fspath, scandir
from random import randrange
from sys import exit
from time import mktime, strptime
from urllib.parse import urlparse

from lxml import etree

from areas import AREAS
from colours import AREA_COLOURS, IETF_COLOUR, IRTF_COLOUR, OTHER_COLOUR


BIBXML_PATH = fspath('bibxml3')


def get_date(date_tag):
    date = '{year} {month} {day} {hour:02}:{min:02}:00'.format(
                year=date_tag.get('year'),
                month=date_tag.get('month', 'January'),
                day=date_tag.get('day', 1),
                hour=randrange(0, 24),
                min=randrange(0, 60))
    return int(mktime(strptime(date, '%Y %B %d %H:%M:%S')))


def get_area(wg):
    return next((k for k, v in AREAS.items() if wg in v), None)


def get_id_dict(filename):
    name_parts = filename[:-4].split('-')
    id_dict = {}

    if len(name_parts) < 2:
        # Fallback for malformed filenames
        return {
            'org': 'other',
            'name': filename[:-4],
            'file_name': filename[:-4]
        }

    if name_parts[1] == 'ietf':
        id_dict = {
                'org': name_parts[1],
                'area': get_area(name_parts[2]),
                'wg': name_parts[2],
                'name': '-'.join(name_parts[3:-1]),
                'file_name': '-'.join(name_parts)}
    elif name_parts[1] == 'irtf':
        id_dict = {
                'org': name_parts[1],
                'rg': name_parts[2],
                'name': '-'.join(name_parts[3:-1]),
                'file_name': '-'.join(name_parts)}
    elif name_parts[1] == '':
        id_dict = {
                'org': name_parts[2],
                'name': '-'.join(name_parts[3:-1]),
                'file_name': '-'.join(name_parts)}
    else:
        id_dict = {
                'org': name_parts[1],
                'name': '-'.join(name_parts[2:-1]),
                'file_name': '-'.join(name_parts)}
    return id_dict


def get_id_file(id_dict):
    return '/'.join(filter(None, id_dict.values()))


def get_colour(id_dict):
    if 'area' in id_dict.keys() and id_dict['area']:
        return AREA_COLOURS.get(id_dict['area'], OTHER_COLOUR)
    elif id_dict['org'] == 'ietf':
        return IETF_COLOUR
    elif id_dict['org'] == 'irtf':
        return IRTF_COLOUR
    else:
        return OTHER_COLOUR


def get_draft_filename(root):
    """Extract draft filename from XML, handling both old and new formats"""
    
    # Try old format first: look for format element with type='TXT'
    format_elements = root.xpath("/reference/format[@type='TXT']")
    if format_elements:
        text_url = format_elements[0].get('target')
        if text_url:
            text_url_path = urlparse(text_url).path
            return text_url_path.split('/')[-1]
    
    # Try new format: get from seriesInfo element
    series_info_elements = root.xpath("/reference/seriesInfo[@name='Internet-Draft']")
    if series_info_elements:
        draft_name = series_info_elements[0].get('value')
        if draft_name:
            return draft_name + '.txt'
    
    # Fallback: try to extract from anchor
    anchor = root.get('anchor')
    if anchor and anchor.startswith('I-D.'):
        # Convert I-D.draft-name to draft-name.txt
        draft_name = anchor[4:]  # Remove 'I-D.' prefix
        return draft_name + '.txt'
    
    return None


def main():
    files = scandir(BIBXML_PATH)
    
    for file in files:
        try:
            with open(file, 'rb') as xml_file:
                xml = xml_file.read()

            root = etree.fromstring(xml)

            # Check if we have required elements
            title_elements = root.xpath('/reference/front/title')
            date_elements = root.xpath('/reference/front/date')
            author_elements = root.xpath('/reference/front/author')
            
            if not title_elements or not date_elements:
                continue
                
            title = title_elements[0].text
            date = get_date(date_elements[0])

            # Get draft filename using improved method
            id_filename = get_draft_filename(root)
            if not id_filename:
                continue

            id_dict = get_id_dict(id_filename)
            id_file = get_id_file(id_dict)
            id_colour = get_colour(id_dict)

            # Process authors
            for author in author_elements:
                author_name = author.get('fullname')
                if author_name:
                    print('{timestamp}|{username}|{type}|{file}|{colour}'.format(
                        timestamp=date,
                        username=author_name,
                        type='M',
                        file=id_file,
                        colour=id_colour))
        except Exception as e:
            # Silently skip problematic files
            pass
    exit(0)


if __name__ == '__main__':
    main()
