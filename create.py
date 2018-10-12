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


def create_many(hs, resource_list):
    created = {}
    errors = {}
    for r in resource_list:
        res = create_resource(hs, r)

        if res['status'] == 'success':
            created[res['id']] = res['title']
        else:
            errors[res['id']] = {'error': res['message'],
                                 'title': res['title']}
    return created, errors


def create_resource(hs, resource):
    r = resource
    resid = None
    st = time.time()
    try:
        print('\nCreating resource: %s' % r.title)
        resid = hs.createResource(resource_type=r.type,
                                  title=r.title,
                                  abstract=r.abstract,
                                  keywords=r.keywords)

        # set sharing status
        print('  setting status ', end='')
        if resource.sharing_status == 'discoverable':
            print('discoverable... ', end='')
            hs.resource(resid).discoverable(True)
        elif resource.sharing_status == 'public':
            print('public... ', end='')
            hs.resource(resid).public(True)
        else:
            print('private... ', end='')
            hs.resource(resid).public(False)
        print('done')

        if resource.shareable:
            print('sharable... ', end='')
            hs.resource(resid).shareable(True)
        else:
            print('not sharable... ', end='')
            hs.resource(resid).shareable(False)
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

        # add files to resource
        for f in r.files:
            # upload file
            fpath = f['path']
            ftype = f['type']
            funzip = f['unzip']
            print('  uploading file: %s...' % fpath.split('/')[-1], end='')
            hs.addResourceFile(resid, fpath)
            print('done')

            # unzip
            if funzip:
                print('  decompressing file: %s...' % f, end='')
                options = {"zip_with_rel_path": f,
                           "remove_original_zip": False}
                hs.resource(resid).functions.unzip(options)
                print('done')

            # set file type
            if ftype:
                print('  setting file type: %s...' % ftype, end='')
                path = os.path.join(resid, 'data/contents',
                                    os.path.basename(f))
                options = {'file_path': f,
                           'hs_file_type': ftype}
                res = hs.resource(resid).functions.set_file_type(options)
                print('done')

                # check to see if file id/path is in the response
                import pdb; pdb.set_trace()

            # set file level metadata
#            if 


#            for ss in ['public', 'discoverable', 'shareable']:
#                print('  setting status %s...' % (ss), end='')
#                func = getattr(hs.resource(resid), ss)
#                val = getattr(r, ss)
#                func(val)
#                print('done')
#            hs.resource(resid).public(r.public)
#            hs.resource(resid).discoverable(r.discoverable)
#            hs.resource(resid).shareable(r.shareable)
#            print('done')



            print('  elapsed time %3.5f seconds' % (time.time() - st))
            return {'id': resid,
                    'title': r.title,
                    'status': 'success',
                    'message': None}

    except Exception as e:
        print('\n  ERROR ENCOUNTERED')
        print('\n  elapsed time %3.5f seconds' % (time.time() - st))
        if resid is not None:
            return {'id': resid,
                    'title': r.title,
                    'status': 'failed',
                    'message': e}
