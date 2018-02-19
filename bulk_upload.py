#!/usr/bin/env python3


import os
import sys
import xlrd
import time
import getpass
from resource import Resource
from datetime import datetime as dt
import parse_template as p
import argparse
import connect


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

#            for f in r.unzip_files:
#                print('  decompressing file: %s...' % f, end='')
#                options = {"zip_with_rel_path": f,
#                           "remove_original_zip": False}
#                hs.resource(resid).functions.unzip(options)
#                print('done')

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


def __auth_user(username, host='www.hydroshare.org'):

    hs = connect.authenticate(username, host, 3)
    if hs:
        return hs
    else:
        __exit()


def run_interactive():

    default_host = "www.hydroshare.org"
    host = input('Enter host address (default: www.hydroshare.org): ') or default_host
    username = input('Please enter username: ')

    hs = __auth_user(username, host)

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
    parser.add_argument('-t', '--template', help='bulk insert template file')
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
        print('\n'+50 * '-')
        print('Interactive Mode')
        print(50 * '-' + '\n')
        host, hs, template = run_interactive()
    elif args.debug:
        print('\n'+50 * '-')
        print('Running in Debug Mode')
        print(50 * '-' + '\n')
        res = p.parse_template(template)
        p.validate(res)
        print('\nTemplate Summary')
        for r in res:
            print(50*'-')
            r.display_summary()
        print(50*'-')
        sys.exit()
    else:
        print('\n'+50 * '-')
        print('Running in Standard Mode')
        print(50 * '-' + '\n')

        if None in (args.address, args.user):
            print('\nERROR: Missing one of the required arguments for non-interactive '
                  'mode: [ADDRESS], [USER]')
            parser.print_help()
            sys.exit()
        else:
            hs = __auth_user(args.user, args.address)

    # parse template
    resources = p.parse_template(template)

    # run template validation
    failed = p.validate(resources)

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
            print('\n  %s\n  %s/%s' % (t, args.address, r))

    __exit()

