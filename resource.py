#!/usr/bin/env python3  

import os

valid_resource_types = {'collectionresource': 'CollectionResource'}
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

#        fields = ['Public', 'Discoverable', 'Sharable']
#        vars = [self.public, self.discoverable, self.shareable]
#        for i in range(3):
#            if type(vars[i]) != str:
#                self.validation_text.append('%s status must be a string' % fields[i])
#            if vars[i].strip() == '':
#                self.validation_text.append('%s cannot be empty' % fields[i])
#            if vars[i].lower() not in ['true', 'false']:
#                self.validation_text.append('%s must be one of the following: %s'
#                                            % (fields[i], 'true, false'))
        

        if type(self.files) != list:
            self.validation_text.append('Files must be a list')
        for f in self.files:
            if not os.path.exists(f):
                self.validation_text.append('Could not find file: %s' % f)

#        if type(self.unzip_files) != list:
#            self.validation_text.append('Unzip Files must be a list')
#        fnames = [f.split('/')[-1] for f in self.files]
#        for f in self.unzip_files:
#            if f not in fnames:
#                self.validation_text.append('Unzip file "%s" does not exist in specified files' % (f))
#
        

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
#            print('The Following Errors were Found:')
            for e in self.validation_text:
                print(' --> %s' % e)

    def display_summary(self):
        print('Title: %s' % self.title)
        print('Abstract: %s' % self.abstract)
        print('Keywords: %s' % ','.join(self.keywords))
        print('Type: %s' % self.type)
        print('Public: %s' % self.public)
        print('Discoverable: %s' % self.discoverable)
        print('Sharable: %s' % self.shareable)
        print('Files: %s' % ','.join(self.files))
        print('Files to Unzip: %s' % ','.join(self.unzip_files))
