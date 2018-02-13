#!/usr/bin/env python3

import os
from tabulate import tabulate

valid_resource_types = {'compositeresource': 'CompositeResource'}
all_resource_types = {'collectionresource': 'CollectionResource',
                      'compositeresource': 'CompositeResource',
                      'genericresource': 'GenericResource',
                      'geographicfeatureresource': 'GeographicFeatureResource',
                      'modflowmodelinstanceresource': 'MODFLOWModelInstanceResource',
                      'modelinstanceresource': 'ModelInstanceResource',
                      'modelprogramresource': 'ModelProgramResource',
                      'netcdfresource': 'NetcdfResource',
                      'rasterresource': 'RasterResource',
                      'reftimeseriesresource': 'RefTimeSeriesResource',
                      'swatmodelinstanceresource': 'SWATModelInstanceResource',
                      'scriptresource': 'ScriptResource',
                      'timeseriesresource': 'TimeSeriesResource',
                      'toolresource': 'ToolResource'}
valid_file_types = {'netcdf:': 'NetCDF',
                    'georaster': 'GeoRaster',
                    'geofeature': 'GeoFeature',
                    '': None}
valid_status = ['public', 'private', 'discoverable']


class Resource(object):

    def __init__(self, title, abstract, keywords, type,
                 files=[], public="false", discoverable="false", 
                 shareable="false", authors=[],
                 custom_metadata={}, file_metadata=[]):
        self.title = title
        self.abstract = abstract
        self.keywords = keywords
        self.type = type
        self.files = files
        self.public = public
        self.shareable = shareable
        self.discoverable = discoverable
#        self.unzip_files = unzip_files
        self.authors = authors
        self.custom_metadata = custom_metadata
        self.filemeta = file_metadata
        self.validation_text = []

    def __validate(self):
        self.validation_text = []

        if type(self.title) != str:
            self.validation_text.append('Title must be a string')
        if self.title.strip() == '':
            self.validation_text.append('Title cannot be empty')

        if type(self.abstract) != str:
            self.validation_text.append('Abstract must be a string')
        if self.abstract.strip() == '':
            self.validation_text.append('Abstract cannot be empty')

        if type(self.keywords) != list:
            self.validation_text.append('keywords must be a list')
        if len(self.keywords) == 0:
            self.validation_text.append('Keywords cannot be empty')

        if type(self.type) != str:
            self.validation_text.append('Type must be a string')
        if self.type.strip() == '':
            self.validation_text.append('Type cannot be empty')
        if self.type.lower() not in valid_resource_types.keys():
            self.validation_text.append('Type must be one of the following: %s'
                                        % (','.join(valid_resource_types)))
        else:
            self.type = valid_resource_types[self.type.lower()]

        self.public = bool(self.public)
        self.discoverable = bool(self.discoverable)
        self.shareable = bool(self.shareable)

        if type(self.files) != list:
            self.validation_text.append('Files must be a list')
        for f in self.files:
            if not os.path.exists(f['path']):
                self.validation_text.append('Could not find file: %s'
                                            % f['path'])
            if f['type'] not in valid_file_types:
                self.validation_text.append('%s is not a valid file type'
                                            % f['type'])
            else:
                f['type'] = valid_file_types[f['type']]

        file_paths = [f['path'] for f in self.files]
        for f in self.filemeta:
            if f['path'] != '' and f['path'] not in file_paths:
                self.validation_text.append('cannot add metadata for file that'
                                            ' is not part of the resource: %s'
                                            % f['path'])
            if f['coverage'] != '':
                if f['coverage'].lower() not in ['point', 'box']:
                    self.validation_text.append('invalid coverage: %s' %
                                                f['converage'])
                try:
                    spatialdef = dict(item.split('=') for item in
                                      f['spatial_def'].split())

                except:
                    spatialdef = {}
                    self.validation_text.append('invalid spatial definition '
                                                'format: %s' % f['spatial_def']
                                                )
                if len(spatialdef.keys()) > 0:
                    if f['coverage'].lower() == 'point':
                        if 'lat' not in spatialdef or 'lon' not in spatialdef:
                            self.validation_text.append('invalid spatial definition '
                                                 'for type "point"')
                    if f['coverage'].lower() == 'box':
                        if 'north_lat' not in spatialdef or \
                           'south_lat' not in spatialdef or \
                           'east_lon' not in spatialdef or \
                           'west_lat' not in spatialdef:
                            self.validation_text.append('invalid spatial definition '
                                                 'for type "box"')
                else:
                    self.validation_text.append('spatial definition is '
                                                'required if coverage type '
                                                'has been specified')
                f['spatial_def'] = spatialdef

    def isvalid(self):
        self.validation_text = []
        self.__validate()
        if len(self.validation_text) == 0:
            return True
        else:
            return False

    def get_validation_errors(self):
        return self.validation_text

    def display_errors(self):
        if len(self.validation_text) == 0:
            print('No Errors')
        else:
            for e in self.validation_text:
                print(' --> %s' % e)

    def print_table(self, title, d, fmt='psql', headers=[]):
        print('\n%s' % title)
        if len(d) > 0:
            if len(headers) == 0:
                headers = d[0].keys()
            rows = [x.values() for x in d]
            print(tabulate(rows, headers, tablefmt=fmt))
        else:
            print('No data')

    def print_multi_table(self, title, list_data, fmt='psql', headers=[]):
        print('\n%s' % title)
        if len(headers) == 0:
            headers = list_data[0][0].keys()
        rows = []
        for item in list_data:
            rows.extend([x.values() for x in item])
            rows.extend(['' * len(headers)])

        print(tabulate(rows, headers, tablefmt=fmt))

    def to_dict_list(self, data):
        dict_list = []
        for item in data:
            dict_list.append([{'k': k, 'v': v} for k, v in item.items()])
        return dict_list

    def display_summary(self):

        gen_meta = [{'k': 'Title', 'v': self.title},
                    {'k': 'Abstract', 'v': self.abstract},
                    {'k': 'Keywords', 'v': ','.join(self.keywords)},
                    {'k': 'Type', 'v': self.type},
                    {'k': 'Public', 'v': self.public},
                    {'k': 'Discoverable', 'v': self.discoverable},
                    {'k': 'Sharable', 'v': self.shareable}]
        self.print_table('General Metadata', gen_meta,
                         headers=['Key', 'Value'])
        self.print_table('Resource Content', self.files)

        filemeta_list = self.to_dict_list(self.filemeta)
        self.print_multi_table('File Metadata', filemeta_list,
                               headers=['Key', 'Value'])
        self.print_table('Authors', self.authors)

