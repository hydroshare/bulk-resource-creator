#!/usr/bin/env python3


import xlrd
from resource import Resource
from datetime import datetime as dt

datemode = None

sections = ('General Metadata', 'Sharing Status', 'Resource Count',
            'File Metadata', 'Science Metadata', 'Resource Metadata')

def validate_template(template):

    print('  Validating template...', end='')
    resources = parse_template(template)
    failed = []
    for r in resources:
        if not r.isvalid():
            failed.append(r)
    print('done')
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
        return dt(*xlrd.xldate_as_tuple(value, data.datemode)).isoformat()
    else:
        return value


def get_section_ranges(sheet):
    """
    This function returns the row ranges for each section in the 
    a sheet of the template.
    """
    conseq_blank = 0
    row = 0
    sections = {}
    current_section = None
    while 1:

        value = get_value(sheet, row, 0)

        # track the number of consecutive blank lines
        conseq_blank = conseq_blank + 1 if value == '' else 0

        if value in sections:

            # save the current section info
            sections[value] = dict(start=row, end=None)
            
            # set the end row for the previous section
            if current_section is not None:
                sections[current_section]['end'] = row-1

            # change the current section
            current_section = value

        row += 1

        # exit of too many consecutive blank rows are encountered
        conseq_blank += 1
        if conseq_blank == 100:

            # set the end row for the previous section
            if current_section is not None:
                sections[current_section]['end'] == row - conseq_blank

        return sections




def parse_template(template):
    global datemode


    resources = []
    data = xlrd.open_workbook(template)
    datemode = data.datemode


    for i in range(data.nsheets):
        sheet = data.sheet_by_index(i)

        # skip the __vocab sheet
        if sheet.name[0:2] == '__':
            continue
        
        # get section ranges
        sections = get_section_ranges(sheet)

        # general metadata
        title = sheet.cell_value(rowx=4, colx=1)
        abstract = sheet.cell_value(rowx=5, colx=1)
        keywords = [k.strip() for k in
                    sheet.cell_value(rowx=6, colx=1).split()
                    if k != '']
        type = sheet.cell_value(rowx=7, colx=1)

        # sharing status
        public = sheet.cell_value(rowx=10, colx=1)
        discoverable = sheet.cell_value(rowx=11, colx=1)
        shareable = sheet.cell_value(rowx=12, colx=1)

        # file contents
        files = []
        for row in range(16, 26):
            path = sheet.cell_value(rowx=row, colx=1)
            type = sheet.cell_value(rowx=row, colx=7)
            unzip = sheet.cell_value(rowx=row, colx=9)
            if path != '':
                files.append(dict(path=path, type=type, unzip=unzip))

        # file metadata
        file_meta = []
        for row in range(29, 39):
            path = sheet.cell_value(rowx=row, colx=1)
            key = sheet.cell_value(rowx=row, colx=5)
            if path != '' and key != '':
                value = get_value(data, sheet, row, 7)
                file_meta.append(dict(path=path, key=key, value=value))

        # science metadata
        authors = []
        for row in range(42, 52):
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
        for row in range(57, 67):
            key = sheet.cell_value(rowx=row, colx=1)

            if key != '':
                value = get_value(data, sheet, row, 3)
                custom_metadata[key] = value

        # file custom metadata
        file_metadata = []
        for row in range(57, 67):
            key = sheet.cell_value(rowx=row, colx=7)
            path = sheet.cell_value(rowx=row, colx=9)
            if path != '' and key != '':
                value = get_value(data, sheet, row, 8)
                file_metadata.append(dict(path=path, key=key, value=value))

        r = Resource(title, abstract, keywords, type, files,
                     public, discoverable, shareable, authors,
                     custom_metadata, file_metadata)

        resources.append(r)

    return resources

