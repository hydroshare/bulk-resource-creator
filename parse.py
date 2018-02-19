#!/usr/bin/env python3


import xlrd
from resource import Resource
from datetime import datetime as dt

datemode = None

valid_sections = ('General Metadata', 'Sharing Status',
                  'Resource Content', 'File Metadata',
                  'Science Metadata', 'Resource Metadata')


def validate(resources):

    print('Validating data')
    failed = []
    for r in resources:
        if not r.isvalid():
            failed.append(r)
    print('  %d resources are valid' % (len(resources) - len(failed)))
    print('  %d resources are NOT valid' % len(failed))

    if len(failed) > 0:
        print('Some components of the template failed validation.')
        for f in failed:
            print('\nResource: %s' % f.title)
            print(50*'-')
            f.display_errors()
        print('\n')
    return failed


def get_value(sheet, row, col):

    if datemode is None:
        raise Exception('Date mode has not been set')

    value_type = sheet.cell_type(rowx=row, colx=col)
    value = sheet.cell_value(rowx=row, colx=col)
    if value_type == xlrd.XL_CELL_DATE:
        return dt(*xlrd.xldate_as_tuple(value, datemode)).isoformat()
    else:
        return value


def get_section_ranges(sheet):
    """
    This function returns the row ranges for each section in
    each sheet of the template.
    """
    conseq_blank = 0
    row = 0
    sections = {}
    current_section = None
    while 1:
        try:
            value = get_value(sheet, row, 0)
        except Exception:
            sections[current_section]['end'] = row
            break

        # track the number of consecutive blank lines
        conseq_blank = conseq_blank + 1 if value == '' else 0

        if value in valid_sections:

            # save the current section info
            sections[value] = dict(start=row+2, end=None)

            # set the end row for the previous section
            if current_section is not None:
                sections[current_section]['end'] = row-2

            # change the current section
            current_section = value

        row += 1

    return sections


def parse_template(template):
    global datemode

    print('Parsing template data')

    resources = []
    data = xlrd.open_workbook(template)
    datemode = data.datemode

    for i in range(data.nsheets):
        sheet = data.sheet_by_index(i)

        # skip the __vocab sheet
        if sheet.name[0:2] == '__':
            print('  sheet %d: skipped' % i)
            continue

        print('  sheet %d: read' % i)
        # get section ranges
        sections = get_section_ranges(sheet)

        # general metadata
        rs = sections['General Metadata']['start']
        resource_title = sheet.cell_value(rowx=rs, colx=1)
        abstract = sheet.cell_value(rowx=rs+1, colx=1)
        keywords = [k.strip() for k in
                    sheet.cell_value(rowx=rs+2, colx=1).split()
                    if k != '']
        resource_type = sheet.cell_value(rowx=rs+3, colx=1)

        # sharing status
        rs = sections['Sharing Status']['start']
        public = sheet.cell_value(rowx=rs, colx=1)
        discoverable = sheet.cell_value(rowx=rs+1, colx=1)
        shareable = sheet.cell_value(rowx=rs+2, colx=1)

        # resource content
        files = []
        rs = sections['Resource Content']['start']
        re = sections['Resource Content']['end']
        for row in range(rs, re):
            path = sheet.cell_value(rowx=row, colx=1)
            type = sheet.cell_value(rowx=row, colx=7)
            unzip = sheet.cell_value(rowx=row, colx=9)
            if path != '':
                files.append(dict(path=path, type=type, unzip=unzip))

        # file metadata
        file_meta = []
        rs = sections['File Metadata']['start']
        re = sections['File Metadata']['end']
        for row in range(rs, re):
            path = sheet.cell_value(rowx=row, colx=1)
            title = sheet.cell_value(rowx=row, colx=5)
            start_dt = get_value(sheet, row, 7)
            end_dt = get_value(sheet, row, 8)
            location = sheet.cell_value(rowx=row, colx=9)
            coverage = sheet.cell_value(rowx=row, colx=11)
            spatial_def = sheet.cell_value(rowx=row, colx=13)
            if path != '':
                value = get_value(sheet, row, 7)
                file_meta.append(dict(path=path,
                                 title=title,
                                 start_dt=start_dt,
                                 end_dt=end_dt,
                                 location=location,
                                 coverage=coverage,
                                 spatial_def=spatial_def))

        # science metadata
        authors = []
        rs = sections['Science Metadata']['start']
        re = sections['Science Metadata']['end']
        for row in range(rs, re):
            name = sheet.cell_value(rowx=row, colx=1)
            org = sheet.cell_value(rowx=row, colx=3)
            email = sheet.cell_value(rowx=row, colx=5)
            addr = sheet.cell_value(rowx=row, colx=7)
            phone = sheet.cell_value(rowx=row, colx=11)

            # save author metadata if provided.
            if name != '':
                authors.append(dict(name=name,
                                    organization=org,
                                    email=email,
                                    address=addr,
                                    phone=phone))

        # extended custom metadata
        custom_metadata = {}
        rs = sections['Resource Metadata']['start']
        re = sections['Resource Metadata']['end']
        for row in range(rs, re):
            key = sheet.cell_value(rowx=row, colx=1)

            if key != '':
                value = get_value(sheet, row, 3)
                custom_metadata[key] = value

        r = Resource(resource_title, abstract, keywords, resource_type, files,
                     public, discoverable, shareable, authors,
                     custom_metadata, file_meta)
        resources.append(r)

    return resources
