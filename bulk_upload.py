#!/usr/bin/env python3


import os
import sys
import xlrd
import time
import getpass
from hs_restclient import HydroShare, HydroShareAuthBasic, HydroShareHTTPException
from resource import Resource
from datetime import datetime as dt
import parse_template as p
import argparse


def __connect(username, host):
    u = username
    p = getpass.getpass('Password:')
    auth = HydroShareAuthBasic(username=u, password=p)
    return HydroShare(hostname=host, auth=auth)


def __parse_template(template):
    resources = []
    data = xlrd.open_workbook(template)

    def get_value(sheet, row, col):

        value_type = sheet.cell_type(rowx=row, colx=col)
        value = sheet.cell_value(rowx=row, colx=col)
        if value_type == xlrd.XL_CELL_DATE:
            return dt(*xlrd.xldate_as_tuple(value, data.datemode)).isoformat()
        else:
            return value

    for i in range(data.nsheets):
        sheet = data.sheet_by_index(i)

        # skip the __vocab sheet
        if sheet.name[0:2] == '__':
            continue

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
                value = get_value(sheet, row, 7)
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
                value = get_value(sheet, row, 3)
                custom_metadata[key] = value

        # file custom metadata
        file_metadata = []
        for row in range(57, 67):
            key = sheet.cell_value(rowx=row, colx=7)
            path = sheet.cell_value(rowx=row, colx=9)
            if path != '' and key != '':
                value = get_value(sheet, row, 8)
                file_metadata.append(dict(path=path, key=key, value=value))

        r = Resource(title, abstract, keywords, type, files,
                     public, discoverable, shareable, authors,
                     custom_metadata, file_metadata)

        resources.append(r)

    return resources




def __createResources(resource_list):
    resources_created = {}
    errors = {}
    for r in resource_list:

        resid = None
        st = time.time()
        try:
            print('\nCreating resource: %s' % r.title)
            resid = hs.createResource(resource_type=r.type,
                                      title=r.title,
                                      abstract=r.abstract,
                                      keywords=r.keywords)

            for f in r.files:
                print('  uploading file: %s...' % f.split('/')[-1], end='')
                hs.addResourceFile(resid, f)
                print('done')

            for f in r.unzip_files:
                print('  decompressing file: %s...' % f, end='')
                options = {"zip_with_rel_path": f,
                           "remove_original_zip": False}
                hs.resource(resid).functions.unzip(options)
                print('done')

            # set sharing status
            print('  setting sharing status...', end='')
            hs.resource(resid).public(r.public)
            hs.resource(resid).discoverable(r.discoverable)
            hs.resource(resid).shareable(r.shareable)
            print('done')

            # set custom metadata
            if len(r.custom_metadata.keys()) > 0:
                print('  setting custom metadata...', end='')
                hs.resource(resid).scimeta.custom(r.custom_metadata)
                print('done')

            # set science metadata
            if len(r.authors) > 0:
                print('  setting science metadata...', end='')
#                import pdb; pdb.set_trace()
                hs.updateScienceMetadata(resid,
                                         metadata={'creators': r.authors})
                print('done')

            resources_created[resid] = r.title

        except Exception as e:
            print('\n  ERROR ENCOUNTERED')
            if resid is not None:
                errors[resid] = {'error': e, 'title': r.title}

        print('  elapsed time %3.5f seconds' % (time.time() - st))

    return resources_created, errors


def __exit():
    print('\n' + 50*'-')
    print('Bulk Resource Creation Complete')
    print(50*'-' + '\n')
    sys.exit()

def run_interactive():
    default_host = "www.hydroshare.org"
    host = input('Enter host address (default: www.hydroshare.org): ') or default_host
    auth_success = False
    attempt = 1
    while not auth_success:
        username = input('Please enter username: ')
        hs = __connect(username, host)
        try:
            hs.getUserInfo()
            auth_success = True
        except HydroShareHTTPException:
            print('  Authorization Failed - Attempt %d' % attempt)
        attempt += 1
        if attempt > 3:
            __exit()
    print('  Authorization Successful')

    template_exists = False
    while not template_exists:
        template = input('Please enter path to template file: ')
        if os.path.exists(template):
            template_exists = True
        else:
            print('  Could not find template file')

    return (host, hs, template)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='HydroShare bulk resource '
                                     'creator tool.')
    parser.add_argument('-t', '--template', help='bulk insert template file',
                        required=True)
    parser.add_argument('-a', '--address', help='hydroshare host address')
    parser.add_argument('-u', '--user', help='hydroshare username')
    parser.add_argument('-i', '--interactive-mode', action='store_true',
                        help='run in interactive mode')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='run in debug mode to check the validity of '
                        'the template file')

    args = parser.parse_args()
    template = args.template

    # run interactive mode
    if args.interactive_mode:
        print('Interactive Mode')
        host, hs, template = run_interactive(template)
    elif args.debug:
        print('\nRunning in Debug Mode')
        p.validate_template(template)
        sys.exit()
    else:
        if None in (args.address, args.user):
            print('Missing one of the required arguments for non-interactive '
                  'mode: [ADDRESS], [USER]')
            parser.print_help()



    import pdb; pdb.set_trace() 

    # run template validation
    failed = p.validate_template(template)

    if len(failed) > 0:
        res = input('Would you like to continue [Y/n]? ')
        if res.lower() == 'n':
            __exit()
        elif len(failed) > 0:
            res = input('  It is not recommended that you proceed with validation errors.  Are you sure you want to create HydroShare resources from this template [y/N]? ')
            if res.lower() != 'y':
                __exit()

    print('\n' + 50*'-')
    print('Begin creating HydroShare resources')
    print(50*'-')
    created, errors = __createResources(resources)

    if len(errors) > 0:
        print('\n' + 50*'-')
        print('The following errors were encountered:')
        print(50*'-' + '\n')
        for r, d in errors.items():
            res = input('  %s: %s.\nWould you like to delete it [Y/n]?'
                        % (r, d['error']))
            if res != 'n':
                print('  deleting resource id=%s' % r, end='')
                hs.deleteResource(r)
                print('done')
            else:
                # add the resource to the created list since it was not deleted
                created[r] = d['title']

    if len(created) > 0:
        print('\n' + 50*'-')
        print('The following resources were created:')
        print(50*'-')
        for r, t in created.items():
            print('\n  %s\n  %s/%s' % (t, host, r))

    __exit()

