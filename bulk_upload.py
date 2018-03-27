#!/usr/bin/env python3


import os
import sys
import xlrd
import time
import getpass
from resource import Resource
from datetime import datetime as dt
import parse as p
import argparse
import connect
import create
import requests


def __exit():
    print('\n' + 50*'-')
    print('Bulk Resource Creation Complete')
    print(50*'-' + '\n')
    sys.exit()


def __auth_user(username, host='www.hydroshare.org', ssl_verify=True):
    hs = connect.authenticate(username, host, 3, ssl_verify)
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
    parser.add_argument('-s', '--no-ssl-verify', action='store_true',
                        help='turn off ssl verification')
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
        import pdb; pdb.set_trace()
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
#            import pdb; pdb.set_trace()
            ssl = False if args.no_ssl_verify else True
            if not ssl:
                requests.packages.urllib3.disable_warnings()
            hs = __auth_user(args.user, args.address, ssl)

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
    created, errors = create.create_many(hs, resources)

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
            print('\n  %s\n  %s/resource/%s' % (t, args.address, r))

    __exit()

