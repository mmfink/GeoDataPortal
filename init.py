'''The GeoDataPortal package is a VisTrails implementation of
the pyGDP Python API of the USGS GeoDataPortal.
Additional convenience functions for data pre and post processing
as well as result visualization are provided.

info on GDP: https://my.usgs.gov/confluence/display/GeoDataPortal/GDP+Home
info on pyGDP: https://my.usgs.gov/confluence/pages/viewpage.action?pageId=250937417
pyGDP is available on github: https://github.com/USGS-CIDA/pyGDP

pyGDP requires:
owslib: http://geopython.github.com/OWSLib/
lxml: https://github.com/lxml/lxml


Written by Colin Talbert
Created on Feb 6, 2014
'''

import os
import tempfile
import copy
import dateutil
import hashlib
import zipfile
import glob
import csv

from osgeo import ogr
from osgeo import osr

from vistrails.core.modules.vistrails_module import Module, new_module, ModuleError
from vistrails.core.modules.basic_modules import File, Directory, Dictionary
from vistrails.core.modules.vistrails_module import ModuleSuspended
from vistrails.gui.modules.module_configure import StandardModuleConfigurationWidget
from vistrails.core import system

from PyQt4 import QtGui, QtCore

import pyGDP as _pyGDP
import picklists, utils, ParseGDPOutput

import SpatialUtilities

identifier = 'gov.usgs.GeoDataPortal'
pyGDP = _pyGDP.pyGDPwebProcessing()

global _cida_datatypes
_cida_datatypes = {}
''' This is a global dictionary that stores all parameters from CIDA
since there is a cost for each query we are caching the returned values
in this dictionary so we only have to make each request once per session.
so that we don't have to make requests multiple times.
The format is {serviceName: {'abstract':<abstract>,
                            'URIs':{<URI1>:{'datasets':{<dataset_name>:{long_name':<long name>}
                                                                        }
                                            'start_date:<start date>,
                                            'end_date':<end date>
                                            }
                                    }
                            }
'''


def menu_items():
    """ Add a menu item which allows users to specify their session directory
    and select and test the final model
    """
    def change_session_folder():
        '''User interface for easily changing the 'session directory'.
        The 'session directory' is the folder that all outputs are currently
        being saved into.
        '''
        path = str(QtGui.QFileDialog.getExistingDirectory(None,
                        'Browse to new session folder -', utils.get_root_dir()))
        if path == '':
            return None
        utils.set_root_dir(path)


    lst = []
    lst.append(("Change session folder", change_session_folder))
    return(lst)

class pyGDP_function(Module):
    '''The base class for all of the pyGDP 'submit' service calls.
    '''
    _input_ports = [('data_service_parameters',
                        "(gov.usgs.GeoDataPortal:DataServiceParameters:Other)"),
                    ('shapefile_parameters',
                        "(gov.usgs.GeoDataPortal:ShapefileParameters:Other)"),
                    ]

    _output_ports = [('outputFile', '(edu.utah.sci.vistrails.basic:File)'), ]

    port_map = {'shapefile_parameters':('shapefile_parameters', None, True),
                'data_service_parameters':('data_service_parameters', None, True),
                }
    def __init__(self):
        self.port_map = copy.deepcopy(pyGDP_function.port_map)
        Module.__init__(self)

    def compute(self):
        '''The core compute method needed by any of the pyGDP functions
        This just parses out some of the inputs from the ports.
        The actual pyGDP service call is handled in the child class.
        '''

        self.inputs = utils.map_ports(self, self.port_map)

        self.startTime = self.inputs['data_service_parameters']['startDate']
        self.endTime = self.inputs['data_service_parameters']['endDate']
        self.varID = self.inputs['data_service_parameters']['dataType'][0]

        self.geoType = self.inputs['shapefile_parameters']['File']
        self.dataSetURI = self.inputs['data_service_parameters']['URI']

    def set_outputfile(self):
        '''Renames the output to have an appropriate extension and sets the
        result into the output port.
        '''
        outfile = File()

        outfname = os.path.join(utils.get_root_dir(), self.outfile)
        renamed = os.path.splitext(outfname)[0] + self.output_extension
        os.rename(outfname, renamed)
        outfile.name = renamed
        outfile.upToDate = True

        self.setResult('outputFile', outfile)

class feature_weighted_grid_statistics(pyGDP_function):
    '''Extends the base pyGDP function to cover the specifics of the
    pyGDP function submitFeatureWeightedGridStatistics
    This returns a csv time series of the values under specific polygons

    WPS ID: gov.usgs.cida.gdp.wps.algorithm.FeatureGridStatisticsAlgorithm

    Summary: This algorithm generates unweighted statistics of a gridded dataset
     for a set of vector polygon features. Using the bounding-box that encloses
     the feature data and the time range, if provided, a subset of the gridded
     dataset is requested from the remote gridded data server.
     Polygon representations are generated for cells in the retrieved grid.
     The polygon grid-cell representations are then projected to the feature
     data coordinate reference system.
     The grid-cells are used to calculate per grid-cell feature coverage fractions.
     Area-weighted statistics are then calculated for each feature using
     the grid values and fractions as weights. If the gridded dataset
     has a time range the last step is repeated for each time step within the
     time range or all time steps if a time range was not supplied.

    Notes: This algorithm will work with gridded data from a Web Coverage
    Service or an OPeNDAP service. It will work with both time-series grids
    and non-time-varying grids. It expects a grid containing continuous
    numerical values. Given a categorical data type (integers), it will treat
    the data as if it were continuous. For large spatio-temporal request extents,
    it is recommended that users make test requests using a subset of the
    eventual need in order to verify that the response is as expected.
    '''
    _input_ports = list(pyGDP_function._input_ports)
    _input_ports.extend([('statistic', '(gov.usgs.GeoDataPortal:Stat:Other)', {'defaults':'["MEAN"]'}),
                        ('summarize_timestep', '(edu.utah.sci.vistrails.basic:Boolean)', {'defaults':'["False"]'}),
                        ('summarize_feature_attribute', '(edu.utah.sci.vistrails.basic:Boolean)', {'defaults':'["False"]'})])

    def __init__(self):
        pyGDP_function.__init__(self)
        self.output_extension = '.csv'
        self.port_map.update({'statistic':('statistic', None, True),
                         'summarize_timestep':('summarize_timestep', None, True),
                         'summarize_feature_attribute':('summarize_feature_attribute', None, True),
                         })
    def compute(self):

        pyGDP_function.compute(self)

        self.kwargs = {}
        self.kwargs["attribute"] = self.inputs['shapefile_parameters']['Field']

        if 'all_values' in self.inputs['shapefile_parameters']['Value']:
            self.kwargs["value"] = 'all_values'
        else:
            self.kwargs["value"] = self.inputs['shapefile_parameters']['Value']

        self.kwargs["stat"] = self.inputs["statistic"]
        self.kwargs["timeStep"] = str(self.inputs['summarize_timestep']).lower()
        self.kwargs["summAttr"] = str(self.inputs['summarize_feature_attribute']).lower()

        origdir = os.getcwd()
        os.chdir(utils.get_root_dir())
#          print os.getcwd()
        self.outfile = pyGDP.submitFeatureWeightedGridStatistics("upload:" + self.geoType,
                                self.dataSetURI, self.varID,
                                self.startTime, self.endTime, **self.kwargs)
        os.chdir(origdir)

        pyGDP_function.set_outputfile(self)

        print "Done"

class SubmitFeatureCoverageOPenDAP(pyGDP_function):
    '''Extends the base pyGDP function to cover the specifics of the
    pyGDP function submitFeatureCoverageOPenDAP
    This returns a netcdf time series of the data requested

    id: gov.usgs.cida.gdp.wps.algorithm.FeatureCoverageOPeNDAPIntersectionAlgorithm

Summary: This service returns the subset of data from an OPeNDAP service that
intersects a set of vector polygon features and time range, if specified.
A NetCDF file is returned.

Notes:This service will only work with gridded time series datasets via OPeNDAP.
It writes a NetCDF-3 file which has limit of about 2GiB per variable.
This service returns a rectangular spatial extent of data surrounding the
polygons that are submitted. No clipping to the shapefile edges is performed.
    '''
    _input_ports = list(pyGDP_function._input_ports)
    _input_ports.extend([])

    _output_ports = [('output_file_dict', '(edu.utah.sci.vistrails.basic:Dictionary)')]

    def __init__(self):
        pyGDP_function.__init__(self)
        self.output_extension = '.nc'

    def compute(self):

        pyGDP_function.compute(self)

        self.kwargs = {}
        self.kwargs["attribute"] = self.inputs['shapefile_parameters']['Field']

        if 'all_values' in self.inputs['shapefile_parameters']['Value']:
            self.kwargs["value"] = 'all_values'
        else:
            self.kwargs["value"] = self.inputs['shapefile_parameters']['Value']

        origdir = os.getcwd()
        os.chdir(utils.get_root_dir())
#          print os.getcwd()

        outputs = {}

        for var_id in self.varID:
            run_info = {'request_type':'OPeNDAP', 'geotype':self.geoType,
                          'uri':self.dataSetURI, 'var_id':var_id,
                          'start':self.startTime, 'end':self.endTime,
                          'other':self.kwargs}
            if var_id.startswith('BCCA'):
                run_info.update(utils.get_bcca_info(var_id))

            outfname, already_run = utils.get_outfname(run_info)
            if already_run:
                print "This run was completed previously.\n\tPrevious file: ..\\" + outfname
            else:
                print "Starting processing of " + str(var_id)
                outfile = pyGDP.submitFeatureCoverageOPenDAP("upload:" + self.geoType,
                                    self.dataSetURI.replace("http:", "dods:"), var_id,
                                    self.startTime, self.endTime, **self.kwargs)

                result_fname = os.path.join(utils.get_root_dir(), outfile)
                if len(outfname) > 255 and \
                                system.systemType in ['Microsoft', 'Windows']:
                    outfname = u"\\\\?\\" + unicode(outfname)

                os.rename(result_fname, outfname)

                utils.write_hash_entry_pickle(outfname, run_info)

                print "Finished with: ", os.path.split(outfname)[1]
            outputs[os.path.join(utils.get_root_dir(), outfname)] = run_info
        print "Finished with all."

        os.chdir(origdir)
        self.setResult('output_file_dict', outputs)

        print "Done"


class SubmitCustomBioclim(pyGDP_function):
    '''submitCustomBioclim (development, only available on USGS network)
    This returns a netcdf time series of the data requested

    id: gov.usgs.cida.gdp.wps.algorithm.FeatureCoverageOPeNDAPIntersectionAlgorithm

Summary: This service returns the a series of custom BioClim calculuated from
an data service.  The result is a series of geotiffs

    '''
    _input_ports = list(pyGDP_function._input_ports)
    _input_ports.extend([('tmax_var', '(edu.utah.sci.vistrails.basic:String)', {'defaults':'["default"]'}),
                         ('tmin_var', '(edu.utah.sci.vistrails.basic:String)', {'defaults':'["default"]'}),
                         ('tave_var', '(edu.utah.sci.vistrails.basic:String)', {'defaults':'["default"]'}),
                         ('prcp_var', '(edu.utah.sci.vistrails.basic:String)', {'defaults':'["default"]'}),
                         ('bioclims', '(edu.utah.sci.vistrails.basic:List)', {'defaults':'["(1,2,3,4,5)"]'}), ])
    _output_ports = [('output_file_list', '(edu.utah.sci.vistrails.basic:List)'), ]

    def __init__(self):
        pyGDP_function.__init__(self)
        self.output_extension = '.csv'
        self.port_map.update({'tmax_var':('tmax_var', None, True),
                              'tmin_var':('tmin_var', None, True),
                              'tave_var':('tave_var', None, True),
                              'prcp_var':('prcp_var', None, True),
                              'bioclims':('bioclims', None, True),
                         })

    def compute(self):

        pyGDP_function.compute(self)

        self.kwargs = {}
        self.kwargs['bbox_in'] = get_bbox_from_shape_params(self.inputs['shapefile_parameters'])
        self.kwargs['OPeNDAP_URI'] = self.inputs['data_service_parameters']['URI']
        self.kwargs['start'] = dateutil.parser.parse(self.inputs['data_service_parameters']['startDate']).year
        self.kwargs['end'] = dateutil.parser.parse(self.inputs['data_service_parameters']['endDate']).year
        self.kwargs['bioclims'] = self.inputs['bioclims']

        #  assign the default values for our specific climate variables
        #  currently only works for PRISM and University of Idaho
        self.lookup_default_vars()

        #  do they have values that we need for these vars?
        have_all = True
        if self.kwargs["prcp_var"] is "NULL":
            have_all = False
        if (self.kwargs["tmax_var"] is "NULL" or self.kwargs["tmin_var"] is "NULL") and self.kwargs["tave_var"] is "NULL":
            have_all = False

        if not have_all:
            raise ModuleError(self, "Missing tmin, tmax, tave, or prcp var")

        dataset_hash = hashlib.md5(str(self.kwargs)).hexdigest()
        outdir = os.path.join(utils.get_root_dir(), "pyGDP_bioclim_" + dataset_hash)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        out_desc_fname = os.path.join(outdir, "pyGDP_bioclim_params.txt")
        out_desc = open(out_desc_fname, "w")
        out_desc.write(str(self.kwargs))
        out_desc.close()

        outfname = out_desc_fname.replace("_params.txt", "s.zip")

        pyGDP.submitCustomBioclim(outputfname=outfname,
                             verbose=True, **self.kwargs)

        zf = zipfile.ZipFile(outfname)
        zf.extractall(outdir)
        zf.close()
        os.remove(outfname)

        outputs = glob.glob(outdir + "/*.tif")
        self.setResult('output_file_list', outputs)

        print 'Done'

    def lookup_default_vars(self):
        '''return the default var names pased on the input data service
        '''
        #  TODO:This ought not be hard coded here
        inputs_dict = {"dods://cida.usgs.gov/thredds/dodsC/prism":{"tmax_var":"tmx", "tmin_var":"tmn", "prcp_var":"ppt", "tave_var":"NULL"},
          "dods://cida.usgs.gov/thredds/dodsC/new_gmo":{"tmax_var":"tasmax", "tmin_var":"tasmin", "prcp_var":"pr", "tave_var":"tas"},
          "dods://cida.usgs.gov/thredds/dodsC/UofIMETDATA":{"tmax_var":"max_air_temperature", "tmin_var":"min_air_temperature", "prcp_var":"precipitation_amount", "tave_var":None},
#            "dods://cida.usgs.gov/thredds/dodsC/dcp/conus":{"tmax_var":"<<model>><<scenario tag>>tmax-NAm-grid", "tmin_var":"<<model>><<scenario tag>>tmin-NAm-grid", "prcp_var":"<<model>><<scenario tag>>pr-NAm-grid", "tave_var":None},
#            "dods://cida.usgs.gov/thredds/dodsC/maurer/maurer_brekke_w_meta.ncml":{"tmax_var":None, "tmin_var":None, "prcp_var":"<<model>><<scenario tag>>_Prcp", "tave_var":"<<model>><<scenario tag>>_Tavg"}
          }
        uri = self.inputs['data_service_parameters']['URI']
        defaults = inputs_dict.get(uri, {"tmax_var":"NULL", "tmin_var":"NULL", "prcp_var":"NULL", "tave_var":"NULL"})

        for var in ('tmax_var', 'tmin_var', 'prcp_var', 'tave_var'):
                if self.inputs[var] != 'default':
                    self.kwargs[var] = self.inputs[var]
                else:
                    self.kwargs[var] = defaults[var]

def get_bbox_from_shape_params(shape_params):
    '''returns a bbox () based on the selected features in a
    shapefile param dictionary

    returns:  The bounding box to use
            four item tuple (max long, min lat, min long, max lat)
    '''
    driver = ogr.GetDriverByName('ESRI Shapefile')
    datasource = driver.Open(shape_params['local_fname'], 0)
    layer = datasource.GetLayer(0)

    feature = layer.GetNextFeature()

    geomcol = ogr.Geometry(ogr.wkbGeometryCollection)
    value = shape_params['Value']
    while feature:
        if (str(feature.GetField(shape_params['Field']))
           in value) or value == 'all_values':
            #  we are including this feature
            geomcol.AddGeometry(feature.GetGeometryRef())
        feature.Destroy()
        feature = layer.GetNextFeature()
    datasource.Destroy()

    envelope = list(geomcol.GetEnvelope())
    bbox = [envelope[1], envelope[2], envelope[0], envelope[3]]
    return bbox

class GDPServiceConfiguration(StandardModuleConfigurationWidget):

    def __init__(self, module, controller, parent=None):
        """Make sure we have decent default values for URI, datatypes,
        startdate and enddate.
        If we're coming up with these for the first time then update the vistrail
        so they show up in the module properties box.
        """
        StandardModuleConfigurationWidget.__init__(self, module, controller,
                   parent)
        self.setWindowTitle(module.name)

        global _cida_datatypes

        self.URI = utils.getPortValue(self, "URI")

        if not self.URI:
            self.URI = _cida_datatypes[self.module.name]["URIs"].iterkeys().next()
            utils.update_vistrail(self, "URI", [self.URI])

        self.orig_URI = self.URI

        self.store_datasets(self.module.name, self.URI)

        datatypes = utils.getPortValue(self, "dataType")
        if datatypes:
            self.datatypes = eval(datatypes)
        else:
            self.datatypes = [self.get_default_datatype(self.module.name, self.URI), ]
            utils.update_vistrail(self, "dataType", [self.datatypes])

        if not self.datatypes or self.datatypes == ['']:
            del _cida_datatypes[self.module.name]["URIs"][self.URI]
            self.URI = _cida_datatypes[self.module.name]["URIs"].iterkeys().next()
            utils.update_vistrail(self, "URI", [self.URI])
            self.store_datasets(self.module.name, self.URI)
            self.datatypes = [self.get_default_datatype(self.module.name, self.URI), ]
            utils.update_vistrail(self, "dataType", [self.datatypes])
            
        self.orig_datatypes = self.datatypes

        self.store_time_range(self.module.name, self.URI)

        self.startDate = utils.getPortValue(self, "startDate")
        self.endDate = utils.getPortValue(self, "endDate")
        if self.URI and not self.startDate:
            self.startDate = self.get_uri_date(self.module.name,
                        uri=self.URI, which_one="start")
            utils.update_vistrail(self, "startDate", [self.startDate])
        if self.URI and not self.endDate:
            self.endDate = self.get_uri_date(self.module.name,
                        uri=self.URI, which_one="end")
            utils.update_vistrail(self, "endDate", [self.endDate])

        self.orig_startDate = self.startDate
        self.orig_endDate = self.endDate

        self.build_gui()
        self.populate_service_config()
        self.state_changed = False

    def build_gui(self):

        global _cida_datatypes

        QtGui.QWidget.__init__(self)

        layout = QtGui.QVBoxLayout()

        urilayout = QtGui.QHBoxLayout()
        uriLabel = QtGui.QLabel("Available URIs: ")
        urilayout.addWidget(uriLabel)
        self.URI_combobox = QtGui.QComboBox(self)
        self.URI_combobox.setEditable(True)
        self.URI_combobox.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        for uri in _cida_datatypes[self.module.name]["URIs"].iterkeys():
            if not uri is None and not uri.endswith("request=GetCapabilities") \
                and not uri.endswith("dataset.html"):
                self.URI_combobox.addItem(uri)
        urilayout.addWidget(self.URI_combobox)
        layout.addLayout(urilayout)

        self.URI_combobox.currentIndexChanged.connect(self.changed_field)
        self.URI_combobox.editTextChanged.connect(self.changed_field)

        dataTypelayout = QtGui.QHBoxLayout()
        dataTypeLabel = QtGui.QLabel("Available Data Types: ")
        dataTypelayout.addWidget(dataTypeLabel)
        self.datatypes_treeview = QtGui.QTreeWidget(self)
        self.datatypes_treeview.setColumnCount(2)
        self.datatypes_treeview.setSortingEnabled(True)
        self.datatypes_treeview.headerItem().setText(0, "short name")
        self.datatypes_treeview.setColumnWidth(0, 200)
        self.datatypes_treeview.headerItem().setText(1, "description")
        self.datatypes_treeview.setColumnWidth(1, 125)
        self.datatypes_treeview.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        dataTypelayout.addWidget(self.datatypes_treeview)
        layout.addLayout(dataTypelayout)

        self.buttonLayout = QtGui.QHBoxLayout()
        self.buttonLayout.setMargin(5)

        self.selectAllButton = QtGui.QPushButton('&Select All', self)
        self.selectAllButton.setFixedWidth(110)
        self.buttonLayout.addWidget(self.selectAllButton)

        self.switchSelectionButton = QtGui.QPushButton('&Switch Selection', self)
        self.switchSelectionButton.setFixedWidth(110)
        self.buttonLayout.addWidget(self.switchSelectionButton)

        spacerItem = QtGui.QSpacerItem(10, 0, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.buttonLayout.addItem(spacerItem)

        self.queryLabel = QtGui.QLabel("Query")
        self.buttonLayout.addWidget(self.queryLabel)

        self.queryText = QtGui.QLineEdit(self)
        self.queryText.setFixedWidth(110)
        self.buttonLayout.addWidget(self.queryText)

        self.addQuery = QtGui.QPushButton('&Add', self)
        self.addQuery.setFixedWidth(60)
        self.buttonLayout.addWidget(self.addQuery)

        self.removeQuery = QtGui.QPushButton('&Remove', self)
        self.removeQuery.setFixedWidth(60)
        self.buttonLayout.addWidget(self.removeQuery)

        self.connect(self.selectAllButton, QtCore.SIGNAL('clicked(bool)'),
                     self.select_all)
        self.connect(self.switchSelectionButton, QtCore.SIGNAL('clicked(bool)'),
                     self.switch_selection)
        self.connect(self.addQuery, QtCore.SIGNAL('clicked(bool)'),
                     self.query_add)
        self.connect(self.removeQuery, QtCore.SIGNAL('clicked(bool)'),
                     self.query_remove)

        layout.addLayout(self.buttonLayout)

        self.startdate_label = QtGui.QLabel("NA")
        startlayout = QtGui.QHBoxLayout()
        startlayout.addWidget(self.startdate_label)
        self.startDateText = QtGui.QLineEdit(self)
        self.startDateText.setText(self.startDate)
        self.startDateText.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        startlayout.addWidget(self.startDateText)
        layout.addLayout(startlayout)

        endlayout = QtGui.QHBoxLayout()
        self.enddate_label = QtGui.QLabel("NA")
        endlayout.addWidget(self.enddate_label)
        self.endDateText = QtGui.QLineEdit(self)
        self.endDateText.setEnabled(True)
        self.endDateText.setText(self.endDate)
        self.endDateText.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                                    QtGui.QSizePolicy.Maximum)
        endlayout.addWidget(self.endDateText)
        layout.addLayout(endlayout)

        save_layout = QtGui.QHBoxLayout()
        save_layout.setMargin(5)

        self.OK = QtGui.QPushButton('&OK', self)
        self.OK.setFixedWidth(110)
        save_layout.addWidget(self.OK)
        self.Cancel = QtGui.QPushButton('&Cancel', self)
        self.Cancel.setFixedWidth(110)
        save_layout.addWidget(self.Cancel)
        layout.addLayout(save_layout)
        self.connect(self.OK, QtCore.SIGNAL('clicked(bool)'),
                     self.save_changes)
        self.connect(self.Cancel, QtCore.SIGNAL('clicked(bool)'),
                     self.close)

        self.setLayout(layout)

    def ok_selected(self):
        self.save_changes()
        self.close()

    def saveTriggered(self):
        self.save_changes()

    def resetTriggered(self):
        self.close()

    def save_changes(self):
        functions = [('URI', [self.URI])]
        self.controller.update_functions(self.module, functions)
        functions = [("dataType", [str(self.datatypes)])]
        self.controller.update_functions(self.module, functions)
        functions = [("startDate", [self.startDate])]
        self.controller.update_functions(self.module, functions)
        functions = [("endDate", [self.endDate])]
        self.controller.update_functions(self.module, functions)
        self.state_changed = False
        self.close()

#          utils.update_vistrail(self, 'URI', [self.URI])
#          utils.update_vistrail(self, "dataType", [self.datatypes])
#          utils.update_vistrail(self, "startDate", [self.startDate])
#          utils.update_vistrail(self, "endDate", [self.endDate])
#          self.state_changed = False

    def cancel_changes(self):
        self.URI = self.orig_URI
        self.datatypes = self.orig_datatypes
        self.startDate = self.orig_startDate
        self.endDate = self.orig_endDate
        self.populate_service_config()
#          self.state_changed = False

    def select_all(self):
        try:
            self.datatypes_treeview.itemChanged.disconnect()
        except TypeError:
            pass
        treeviewIter = QtGui.QTreeWidgetItemIterator(self.datatypes_treeview)
        self.datatypes = []
        while treeviewIter.value():
            item = treeviewIter.value()
            item.setCheckState(0, QtCore.Qt.Checked)
            self.datatypes.append(str(item.text(0)))
            treeviewIter += 1
#          self.state_changed = True
        self.datatypes_treeview.itemChanged.connect(self.changed_checked_field_values)

    def switch_selection(self):
        try:
            self.datatypes_treeview.itemChanged.disconnect()
        except TypeError:
            pass
        treeviewIter = QtGui.QTreeWidgetItemIterator(self.datatypes_treeview)
        self.datatypes = []
        while treeviewIter.value():
            item = treeviewIter.value()
            if item.checkState(0) == QtCore.Qt.Checked:
                item.setCheckState(0, QtCore.Qt.Unchecked)
            else:
                item.setCheckState(0, QtCore.Qt.Checked)
                self.datatypes.append(str(item.text(0)))
            treeviewIter += 1
#          self.state_changed = True
        self.datatypes_treeview.itemChanged.connect(self.changed_checked_field_values)

    def query_add(self, query_text):
        self.datatypes_treeview.blockSignals(True)
        itemsChecked = 0
        treeviewIter = QtGui.QTreeWidgetItemIterator(self.datatypes_treeview)
        while treeviewIter.value():
            item = treeviewIter.value()
            if str(self.queryText.text()) in item.text(0) or \
                str(self.queryText.text()) in item.text(1):
                self.datatypes.append(str(item.text(0)))
                if item.checkState(0) == QtCore.Qt.Unchecked:
                    item.setCheckState(0, QtCore.Qt.Checked)
                    itemsChecked += 1
            treeviewIter += 1
        self.datatypes_treeview.blockSignals(False)
#          self.state_changed = True

        msgbox = QtGui.QMessageBox(self)
        msgbox.setText(str(itemsChecked) + " items selected.")
        msgbox.exec_()

    def query_remove(self, query_text):
        try:
            self.datatypes_treeview.itemChanged.disconnect()
        except TypeError:
            pass
        itemsUnchecked = 0
        treeviewIter = QtGui.QTreeWidgetItemIterator(self.datatypes_treeview)
        while treeviewIter.value():
            item = treeviewIter.value()
            if str(self.queryText.text()) in item.text(0) or \
                str(self.queryText.text()) in item.text(1):
                if self.datatypes.count(str(item.text(0))) > 0:
                    self.datatypes.remove(str(item.text(0)))
                if item.checkState(0) == QtCore.Qt.Checked:
                    item.setCheckState(0, QtCore.Qt.Unchecked)
                    itemsUnchecked += 1
            treeviewIter += 1
        self.datatypes_treeview.itemChanged.connect(self.changed_checked_field_values)
#          self.state_changed = True
        msgbox = QtGui.QMessageBox(self)
        msgbox.setText(str(itemsUnchecked) + " items deselected.")
        msgbox.exec_()

    def check_uri(self, uri):
        global _cida_datatypes
        self.store_datasets(self.module.name, uri)
        if not "":
            pass

    def update_datatypes(self, uri=None):
        global _cida_datatypes
        self.store_datasets(self.module.name, self.URI)
        uri_info = _cida_datatypes[self.module.name]["URIs"][self.URI]

        available_datasets = list(uri_info['datasets'].iterkeys())

        self.datatypes[:] = [dt for dt in self.datatypes if dt in available_datasets]

        if not self.datatypes:
            self.datatypes = [self.get_default_datatype(self.module.name, self.URI)]

    def populate_service_config(self):
        self.disconnect_all()

        try:
            curIndex = [i for i in range(self.URI_combobox.count()) if self.URI_combobox.itemText(i) == self.URI][0]
            self.URI_combobox.setCurrentIndex(curIndex)
        except IndexError:
            curIndex = -1
        self.URI_combobox.currentIndexChanged.connect(self.changed_field)

        self.populate_datatypes()
        self.datatypes_treeview.itemChanged.connect(self.changed_checked_field_values)

        maxEnd = _cida_datatypes[self.module.name]['URIs'][self.URI]['end_date']
        self.enddate_label.setText("End Date: \n(max = " + maxEnd + ")")
        if not str(self.endDateText.text()):
            self.endDateText.setText(maxEnd)

        self.endDateText.textChanged.connect(self.endDateChanged)

        minStart = _cida_datatypes[self.module.name]['URIs'][self.URI]['start_date']
        self.startdate_label.setText("Start Date: \n(min = " + minStart + ")")
        if not str(self.startDateText.text()):
            self.startDateText.setText(minStart)
        self.startDateText.textChanged.connect(self.startDateChanged)

    def store_datasets(self, serviceName, uri):
        '''Populate the global CIDA_datatypes dictionary if it has not been
        previously done.
        '''
        global _cida_datatypes

        if not _cida_datatypes[serviceName]['URIs'].has_key(uri):
            _cida_datatypes[serviceName]['URIs'][uri] = {}

        if not uri:
            _cida_datatypes[serviceName]['URIs'][uri]["datasets"] = {}
        elif not _cida_datatypes[serviceName]['URIs'][uri].has_key('datasets'):
            pyGDP.sleepSecs = 1
            pyGDP.WPS_attempts = 1
            try:
                data_types = pyGDP.getDataType(uri)
                long_names = pyGDP.getDataLongName(uri)
                datasets = dict(zip(data_types, long_names))
            except:
                datasets = None

            _cida_datatypes[serviceName]['URIs'][uri]["datasets"] = {}
            if datasets:
                for dataset, long_name in datasets.iteritems():
                    _cida_datatypes[serviceName]['URIs'][uri]['datasets'][dataset] = \
                                                        {'long_name':long_name}

    def populate_datatypes(self):
        '''load the existing data type descriptions in the data_types_treeview
        '''
        self.datatypes_treeview.clear()
        global _cida_datatypes
        self.store_datasets(self.module.name, self.URI)
        uri_info = _cida_datatypes[self.module.name]["URIs"][self.URI]

        for dataset, vals in uri_info['datasets'].iteritems():
            description = vals['long_name']
            child_item = QtGui.QTreeWidgetItem([dataset, description])
            child_item.setFlags(QtCore.Qt.ItemIsUserCheckable |
                                QtCore.Qt.ItemIsEnabled)
            if dataset in self.datatypes:
                child_item.setCheckState(0, QtCore.Qt.Checked)
            else:
                child_item.setCheckState(0, QtCore.Qt.Unchecked)
            self.datatypes_treeview.addTopLevelItem(child_item)

    def get_default_datatype(self, service_name, uri):
        '''Returns a random datatype from the list of available datatypes
        associated with a single service to use as the 'default'
        '''
        global _cida_datatypes
        self.store_datasets(service_name, uri)
        datasets = list(_cida_datatypes[service_name]['URIs'][uri]["datasets"].iterkeys())
        if datasets:
            return datasets[0]
        else:
            return ''

    def get_uri_date(self, service_name, uri, which_one="start"):
        '''Returns the start and end data for a given service and datatype
        '''
        global _cida_datatypes
        if not _cida_datatypes[self.module.name]['URIs'][uri].has_key(which_one + 'Date'):
            self.store_time_range(service_name, uri)

        if which_one.lower() == "start":
            return _cida_datatypes[self.module.name]['URIs'][uri]['start_date']
        elif which_one.lower() == "end":
            return _cida_datatypes[self.module.name]['URIs'][uri]['end_date']

    def store_time_range(self, service_name, uri, dataType=None):
        global _cida_datatypes

        self.store_datasets(service_name, uri)

        dataType = self.get_default_datatype(service_name, uri)

        if not uri or not dataType:
            _cida_datatypes[service_name]['URIs'][uri]['start_date'] = ''
            _cida_datatypes[service_name]['URIs'][uri]['end_date'] = ''
        elif not _cida_datatypes[service_name]['URIs'][uri].has_key('start_date'):
            timeRange = pyGDP.getTimeRange(uri, dataType)
            _cida_datatypes[service_name]['URIs'][uri]['start_date'] = timeRange[0]
            _cida_datatypes[service_name]['URIs'][uri]['end_date'] = timeRange[1]

    def changed_field(self):
        self.URI = str(self.URI_combobox.currentText())
        self.store_datasets(self.module.name, self.URI)
        self.store_time_range(self.module.name, self.URI)
        self.update_datatypes()
        self.populate_service_config()
#          self.state_changed = True

    def changed_checked_field_values(self):
        treeviewIter = QtGui.QTreeWidgetItemIterator(self.datatypes_treeview)
        self.datatypes = []
        while treeviewIter.value():
            item = treeviewIter.value()
            if item.checkState(0) == QtCore.Qt.Checked:
                self.datatypes.append(str(item.text(0)))

            treeviewIter += 1
#          self.state_changed = True

    def startDateChanged(self):
        self.startDate = str(self.startDateText.text())
#          self.state_changed = True

    def endDateChanged(self):
        self.endDate = str(self.endDateText.text())
#          self.state_changed = True

    def setMinDateLabel(self):
        minStart = _cida_datatypes[self.module.name]['URIs'][self.URI]['start_date']
        self.startdate_label.setText("Start Date: \n(min = " + minStart + ")")

    def setMaxDateLabel(self):
        max_end = _cida_datatypes[self.module.name]['URIs'][self.URI]['end_date']
        self.enddate_label.setText("End Date: \n(max = " + max_end + ")")

    def disconnect_all(self):
        try:
            self.URI_combobox.currentIndexChanged.disconnect()
        except TypeError:
            pass
        try:
            self.datatypes_treeview.itemChanged.disconnect()
        except TypeError:
            pass
        try:
            self.endDateText.textChanged.disconnect()
        except TypeError:
            pass
        try:
            self.startDateText.textChanged.disconnect()
        except TypeError:
            pass

#      def saveTriggered(self, *args, **kwargs):
#          self.save_changes()
#          self.disconnect_all()
#
#
#      def resetTriggered(self):
#          self.cancel_changes()
#          self.disconnect_all()

class Shapefile(Module):
    '''A Shapefile with parameters needed by GDP
    i.e. the ability to specify a field and specific values in that field for running
    summary statistics.  Also handles the upload of the file to the GDP server if one
    with that name isn't already there.  Will provide bad results in the case of identically
    named files.
    '''
    _input_ports = [('File', '(edu.utah.sci.vistrails.basic:Path)'),
                    ('Field', '(edu.utah.sci.vistrails.basic:String)'),
                    ('Value', '(edu.utah.sci.vistrails.basic:String)',
                                                 {'defaults':'["all_values"]'})]
    _output_ports = [('ShapefileParameters',
                          "(gov.usgs.GeoDataPortal:ShapefileParameters:Other)")]

    def compute(self):
        output_dict = {}

        #  check if the specified Shapefile already exists on the server
        shp_fname = self.getInputFromPort("File").name
        shp_fname = utils.getFileRelativeToCurrentVT(shp_fname)

        if shp_fname.endswith(".shp"):
            #  we'll assume that this a shapefile
            pass
        elif SpatialUtilities.isRaster(shp_fname):
            #  this is a raster write out a shapefile with the extent.
            raster_short_name = SpatialUtilities.getRasterShortName(shp_fname)

            tmp_shpname = os.path.join(utils.get_root_dir(), raster_short_name + ".shp")
            convert_raster_to_shapefile_env(shp_fname, tmp_shpname)
            shp_fname = tmp_shpname

        if not shapefile_already_on_server(shp_fname):
            upload_shapefile(shp_fname)

        output_dict["File"] = get_server_name(shp_fname)
        output_dict["local_fname"] = shp_fname
        output_dict["Field"] = self.getInputFromPort("Field")
        if self.hasInputFromPort("Value"):
            output_dict["Value"] = eval(self.getInputFromPort("Value"))
            if 'all_values' in output_dict["Value"]:
                output_dict["Value"] = ['all_values']
        else:
            output_dict["Value"] = ['all_values']

        output_dict['bbox'] = get_bbox_from_shape_params(output_dict)

        self.setResult('ShapefileParameters', output_dict)

class GDPShapeFileConfiguration(StandardModuleConfigurationWidget):
    '''The edit config gui thats can be used to specify Shapefile parameters
    '''
    def __init__(self, module, controller, parent=None):

        StandardModuleConfigurationWidget.__init__(self, module, controller,
                   parent)
        self.setWindowTitle("Shapefile configuration")


        self.shapefile_fname = utils.getPortValue(self, "File")
        if self.shapefile_fname:
            self.fields = self.get_fields(utils.getPortValue(self, "File"))
            self.checkedFieldValues = utils.getPortValue(self, "Value")
            self.field = utils.getPortValue(self, "Field")
            if not self.field and len(self.fields) > 0:
                self.field = self.fields[0]
        else:
            self.fields = []
            self.checkedFieldValues = []
            self.field = ''

        self.build_gui()

    def get_fields(self, fname):
        '''returns a list of the fields in a Shapefile
        '''
        if fname:
            fname = utils.getFileRelativeToCurrentVT(fname)
        if fname == '':
            return []
        else:
            driver = ogr.GetDriverByName("ESRI Shapefile")
            datasource = driver.Open(fname, 0)
            layer = datasource.GetLayer(0)
            layer_def = layer.GetLayerDefn()

            fields = []
            for i in range(layer_def.GetFieldCount()):
                fields.append(layer_def.GetFieldDefn(i).GetName())

            datasource.Destroy()
            return fields

    def get_field_values(self, fname, field_name):
        '''returns a list of the unique values in a single field
        of a Shapefile
        '''
        fname = utils.getFileRelativeToCurrentVT(fname)

        if fname == '':
            return []

        driver = ogr.GetDriverByName('ESRI Shapefile')
        datasource = driver.Open(fname, 0)
        layer = datasource.GetLayer(0)

        unique_vals = set([])
        feature = layer.GetNextFeature()
        while feature:
            unique_vals.add(feature.GetField(field_name))
            feature.Destroy()
            feature = layer.GetNextFeature()
        datasource.Destroy()
        return list(unique_vals)

#          f = open(fname.replace(".shp", ".dbf"), "rb")
#          inputReader = utils.dbfreader(f)
#
#          index = self.fields.index(field_name)
#          inputReader.next()
#          inputReader.next()
#          fieldVals = []
#          for row in inputReader:
#              fieldVals.append(str(row[index]).strip())
#
#          f.close()
#          return list(set(fieldVals))

    def build_gui(self):
        '''Constructs the pyQT Qui that is displayed in the configure popup
        '''
        QtGui.QWidget.__init__(self)

        main_layout = QtGui.QVBoxLayout()

        file_layout = QtGui.QHBoxLayout()
        file_label = QtGui.QLabel("Shapefile: ")
        file_layout.addWidget(file_label)
        self.file_text = QtGui.QLineEdit(self)
        self.file_text.setText(self.shapefile_fname)
        self.file_text.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        file_layout.addWidget(self.file_text)
        browse_button = QtGui.QPushButton("browse", self)
        browse_button.clicked.connect(self.select_file)
        file_layout.addWidget(browse_button)
        self.file_text.editingFinished.connect(self.set_new_shapefile)
        main_layout.addLayout(file_layout)

        uri_layout = QtGui.QHBoxLayout()
        uri_label = QtGui.QLabel("Available Fields: ")
        uri_layout.addWidget(uri_label)
        self.shapefile_fields = QtGui.QComboBox(self)


        uri_layout.addWidget(self.shapefile_fields)
        main_layout.addLayout(uri_layout)

        QtCore.QObject.connect(self.shapefile_fields, QtCore.SIGNAL("currentIndexChanged(QString)"), self.changed_field)

        datatype_layout = QtGui.QHBoxLayout()
        datatype_label = QtGui.QLabel("Available Values: ")
        datatype_layout.addWidget(datatype_label)
        self.datatypes_treeview = QtGui.QTreeWidget(self)
        self.datatypes_treeview.setColumnCount(1)
        self.datatypes_treeview.setSortingEnabled(True)
        self.datatypes_treeview.headerItem().setText(0, "short name")
        self.datatypes_treeview.setColumnWidth(0, 200)
        self.datatypes_treeview.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        if self.shapefile_fname:
            self.populate_fields()
            self.populate_datatypes()
        self.datatypes_treeview.itemChanged.connect(self.changed_checked_field_values)

        datatype_layout.addWidget(self.datatypes_treeview)
        main_layout.addLayout(datatype_layout)

        save_layout = QtGui.QHBoxLayout()
        save_layout.setMargin(5)

        self.OK = QtGui.QPushButton('&OK', self)
        self.OK.setFixedWidth(110)
        save_layout.addWidget(self.OK)
        self.Cancel = QtGui.QPushButton('&Cancel', self)
        self.Cancel.setFixedWidth(110)
        save_layout.addWidget(self.Cancel)
        main_layout.addLayout(save_layout)
        self.connect(self.OK, QtCore.SIGNAL('clicked(bool)'),
                     self.save_changes)
        self.connect(self.Cancel, QtCore.SIGNAL('clicked(bool)'),
                     self.close)

        self.setLayout(main_layout)

    def select_file(self):
        fname = QtGui.QFileDialog.getOpenFileNameAndFilter(self,
                                                "Shapefile (*.shp)")
        self.file_text.setText(fname[0])
        self.set_new_shapefile()

    def set_new_shapefile(self):
#          utils.update_vistrail(self, "File", [str(self.file_text.text())])
        self.populate_fields()
        self.populate_datatypes()

    def populate_fields(self):
        self.fields = self.get_fields(self.shapefile_fname)

        self.shapefile_fields.blockSignals(True)
        self.shapefile_fields.clear()
        self.shapefile_fields.blockSignals(False)

        self.shapefile_fields.blockSignals(True)
        for field in self.fields:
            if not field is None:
                self.shapefile_fields.addItem(field)
        self.shapefile_fields.blockSignals(False)

        try:
            cur_index = [i for i in range(self.shapefile_fields.count()) if self.shapefile_fields.itemText(i) == self.field][0]
        except IndexError:
            cur_index = 0

        self.shapefile_fields.setCurrentIndex(cur_index)

    def populate_datatypes(self):
        field_values = self.get_field_values(utils.getPortValue(self, 'File'),
                                           self.field)
        field_values.insert(0, 'all_values')

        self.datatypes_treeview.clear()
        for fieldValue in field_values:
            child_item = QtGui.QTreeWidgetItem([str(fieldValue)])
            child_item.setFlags(QtCore.Qt.ItemIsUserCheckable |
                                QtCore.Qt.ItemIsEnabled)
            if str(fieldValue) in self.checkedFieldValues:
                child_item.setCheckState(0, QtCore.Qt.Checked)
            else:
                child_item.setCheckState(0, QtCore.Qt.Unchecked)
            self.datatypes_treeview.addTopLevelItem(child_item)

    def changed_field(self):
        self.field = str(self.shapefile_fields.currentText())
        self.values = self.get_field_values(utils.getPortValue(self, 'File'),
                                           self.field)
        self.populate_datatypes()
#          utils.update_vistrail(self, "Field", [self.field])

    def changed_checked_field_values(self):
        treeviewIter = QtGui.QTreeWidgetItemIterator(self.datatypes_treeview)
        self.checkedFieldValues = []
        while treeviewIter.value():
            item = treeviewIter.value()
            if item.checkState(0) == QtCore.Qt.Checked:
                self.checkedFieldValues.append(str(item.text(0)))
            treeviewIter += 1
#          utils.update_vistrail(self, "Value", self.checkedFieldValues)

    def saveTriggered(self):
        self.save_changes()

    def resetTriggered(self):
        self.close()

    def save_changes(self):
        functions = [('Value', [str(self.checkedFieldValues)])]
        self.controller.update_functions(self.module, functions)
        functions = [("Field", [self.field])]
        self.controller.update_functions(self.module, functions)
        functions = [("File", [self.shapefile_fname])]
        self.controller.update_functions(self.module, functions)
        self.state_changed = False
        self.close()

    def ok_selected(self):
        self.save_changes()
        self.close()

def convert_raster_to_shapefile_env(rasterfname, outfname):
    '''These services need a shapefile to load onto the server.
    This function creates one with the envelope of a raster.
    '''
    tr = SpatialUtilities.SAHMRaster(rasterfname)

    outDriver = ogr.GetDriverByName("ESRI Shapefile")

    #  Remove output shapefile if it already exists
    if os.path.exists(outfname):
        outDriver.DeleteDataSource(outfname)

    #  Create the output shapefile
    outDataSource = outDriver.CreateDataSource(outfname)
    outLayer = outDataSource.CreateLayer("test", geom_type=ogr.wkbPolygon)

    #  Add an ID field
    idField = ogr.FieldDefn("id", ogr.OFTInteger)
    outLayer.CreateField(idField)

    #  Create the feature and set values
    featureDefn = outLayer.GetLayerDefn()
    feature = ogr.Feature(featureDefn)

    #  Create ring
    ring = ogr.Geometry(ogr.wkbLinearRing)

    ring.AddPoint(tr.gWest, tr.gNorth)
    ring.AddPoint(tr.gEast, tr.gNorth)
    ring.AddPoint(tr.gEast, tr.gSouth)
    ring.AddPoint(tr.gWest, tr.gSouth)
    ring.AddPoint(tr.gWest, tr.gNorth)

    #  Create polygon
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)

    feature.SetGeometry(poly)
    feature.SetField("id", 1)
    outLayer.CreateFeature(feature)

    #  Close DataSource
    outDataSource.Destroy()

    #  write out a prj
    wgs84_prj = osr.SpatialReference()
    wgs84_prj.ImportFromEPSG(4326)  #
    wgs84_prj.MorphToESRI()

    f = open(outfname.replace(".shp", ".prj"), "w")
    f.write(wgs84_prj.ExportToWkt())
    f.close()

def shapefile_already_on_server(shp_fname):
    '''Checks if a Shapefile with the given name is already on
    the GDP server.
    '''
    shapefiles = pyGDP.getShapefiles()
    if shp_fname in shapefiles:
        return True
    if os.path.exists(shp_fname):
        serverName = "upload:" + get_server_name(shp_fname)
        if serverName in shapefiles:
            return True
    return False

def get_server_name(shp_fname):
    '''converts a file path of a Shapefile to the string format used by GDP
    '''
    return os.path.splitext(os.path.basename(shp_fname))[0]

def upload_shapefile(shp_fname):
    '''Uploads a polygon Shapefile to the GDP server for analysis
    '''
    outdir = tempfile.gettempdir()
    justfname = os.path.splitext(os.path.split(shp_fname)[1])[0]
    out_fname = os.path.join(outdir, justfname)

    zip_shp = pyGDP.shapeToZip(shp_fname, out_fname)
    zip_shp = zip_shp.replace("\\", "/")

    return pyGDP.uploadShapeFile(zip_shp)

class ShapefileParameters(Dictionary):
    '''A dictionary of parameters that define the file and data subset to use
    for a service call.

    This is given a specific subclass only for port type connection enforcement
    '''

class DataServiceParameters(Dictionary):
    '''A dictionary of parameters that define the data service to use
    for a service call.

    This is given a specific subclass only for port type connection enforcement
    '''

def pyGDP_module_compute(instance):
    '''This function is the compute method for all of the dynamically generated
    pyGDP data service modules.

    It creates a dictionary of all the port values selected.
    '''

    output_dict = {}
    for port in instance._input_ports:
        port_contents = instance.forceGetInputListFromPort(port[0])
        if port[0] == 'dataType' and len(port_contents) == 1:
            output_dict[port[0]] = [port_contents[0]]
        elif len(port_contents) == 1:
            output_dict[port[0]] = port_contents[0]
        elif len(port_contents) > 1:
            #  multiple entries found store them all
            output_dict[port[0]] = port_contents
        else:
            #  this will fill it with the default value
            output_dict[port[0]] = instance.getInputFromPort(port[0])

    instance.setResult('data_service_parameters', output_dict)

################################################################################
#  tool modules

class AverageBioclims(Module):
    '''Creates average tiffs of
    '''
    _input_ports = [('file_list', '(edu.utah.sci.vistrails.basic:List)'),
                         ('bioclims', '(edu.utah.sci.vistrails.basic:List)', {'defaults':'["all"]'}),
                         ('start_year', '(edu.utah.sci.vistrails.basic:List)', {'defaults':'["first"]'}),
                         ('end_year', '(edu.utah.sci.vistrails.basic:List)', {'defaults':'["last"]'}),
                         ]
    _output_ports = [('output_file_dict', '(edu.utah.sci.vistrails.basic:Dictionary)'), ]

    def compute(self):

        file_list = self.forceGetInputFromPort('file_list')
        bioclims = self.forceGetInputFromPort('bioclims', 'all')
        if bioclims == 'all':
            bioclims = set([int(f.split("_")[-2]) for f in file_list])

        years = set([int(f.split('_')[-1].replace(".tif", "")) for f in file_list])

        start_year = self.forceGetInputFromPort('start_year', 'first')
        if start_year == 'first':
            start_year = min(years)

        end_year = self.forceGetInputFromPort('end_year', 'last')
        if end_year == 'last':
            end_year = max(years)


        source_dir = os.path.split(file_list[0])[0]
        dir_for_output = os.path.join(source_dir, "bioclim_aves")
        if not os.path.exists(dir_for_output):
            os.makedirs(dir_for_output)

        output_dict = {}
        for bioclim in bioclims:
            fnames = []
            for year in range(start_year, end_year):
                this_fname = "_".join(["bioclim", str(bioclim), str(year) + ".tif"])
                this_file = [fname for fname in file_list if fname.endswith(this_fname)][0]
                fnames.append(this_file)

            outfname = os.path.join(dir_for_output, "_".join(["bioclim",
                                            str(bioclim), "ave", str(start_year),
                                            str(end_year) + ".tif"]))
            if not os.path.exists(outfname):
                SpatialUtilities.average_geotifs(fnames, outfname)
            output_dict[bioclim] = outfname
            print "Done with: ", bioclim

        self.setResult('output_file_dict', output_dict)


def build_pyGDP_service_modules():
    '''This module is dynamically generates a single VisTraisl module
    for each of the non provisional datasets listed by the pyGDP function
    pyGDP.getDataSetURI().

    '''
    new_classes = {}
    dataset_uris = pyGDP.getDataSetURI()

    global _cida_datatypes

    #  hardwired addition of additional server datasets.
    dataset_uris.insert(1, ["GDP_Service", "This module is for THREDDS and OPeNDAP URIs not covered by the predefined convenience modules available in this package.",
                         ['']])

    services_fname = os.path.join(os.path.dirname(__file__), 'DynamicServicesLookup.csv')
    with open(services_fname) as f:
        f.readline()  #  ignore first line (header)
        service_names = dict(csv.reader(f, delimiter=','))
    service_names["GDP_Service"] = "GDP_Service"

    for dataSetURI in dataset_uris[1:]:
        if service_names.has_key(dataSetURI[0]):
            short_name = service_names[dataSetURI[0]]
        else:
            print "new service skipped: ", service_names[dataSetURI[0]]
            short_name = 'skip'

        if short_name != 'skip':
            m_doc = dataSetURI[1]
            _cida_datatypes[short_name] = {}
            _cida_datatypes[short_name]['abstract'] = m_doc
            _cida_datatypes[short_name]['URIs'] = {}
            for uri in dataSetURI[2]:
                _cida_datatypes[short_name]['URIs'][uri.replace("http", "dods")] = {}

            m_inputs = [('URI', '(edu.utah.sci.vistrails.basic:String)',
                         {'defaults':'["' + dataSetURI[2][0] + '"]'}),
                        ('dataType', '(edu.utah.sci.vistrails.basic:List)'),
                        ('startDate', '(edu.utah.sci.vistrails.basic:String)'),
                        ('endDate', '(edu.utah.sci.vistrails.basic:String)'), ]
            m_outputs = [('data_service_parameters',
                        "(gov.usgs.GeoDataPortal:DataServiceParameters:Other)")]
            klass_dict = {}
            klass_dict["compute"] = pyGDP_module_compute

            module_doc = "This module represents a single data provider listed by the GeoDataPortal"
            module_doc += "\n\nGDP Title:  " + dataSetURI[0]
            module_doc += "\n\nGDP Abstract:\n\t"
            module_doc += m_doc
            module_doc += "\n\nThe input ports for this module provide means of selecting the "
            module_doc += "\nindividual data type(s) will be returned as well as limiting the "
            module_doc += "\ntemporal extent of the result. "
            module_doc += "\n\nThe ports types are free text strings which require exacting "
            module_doc += "\nvalues dependent on the underlying dataset format."
            module_doc += "\nAdding or editing these values by hand is possible but not recommended."
            module_doc += "\nA user-friendly interface for changing these values is provided by "
            module_doc += "\nclicking on the module configure button."

            m_class = new_module(Module, short_name, klass_dict, module_doc)
            m_class.URI = dataSetURI[2][0]
            m_class._input_ports = utils.expand_ports(m_inputs)
            m_class._output_ports = utils.expand_ports(m_outputs)
            m_dict = {'moduleColor':INPUT_COLOR, 'moduleFringe':INPUT_FRINGE}
            m_dict['configureWidgetType'] = GDPServiceConfiguration
            m_dict['namespace'] = "data_services"
            new_classes[short_name] = (m_class, m_dict)
    return new_classes.values()

def initialize():
    '''package initialization routine
    '''
    utils.set_globals(identifier, configuration)

    session_dir = configuration.cur_session_folder
    if not os.path.exists(configuration.cur_session_folder):
        orig_session_dir = session_dir
        session_dir = tempfile.mkdtemp(prefix="gdp_session_dir_")
        print("!" * 79)
        print("The previous session directory: " + orig_session_dir + " no longer exists on the file system!")
        print("Defaulting to a random temporary location: " + session_dir)
        print("!" * 79)
    utils.set_root_dir(session_dir)


    if configuration.cur_WPS_URL != "default":
        pyGDP.wpsUrl = configuration.cur_WPS_URL

INPUT_COLOR = (0.76, 0.76, 0.8)
INPUT_FRINGE = [(0.0, 0.0),
                    (0.25, 0.0),
                    (0.0, 1.0)]

_modules = [  #  Abstract modules only used internally
            (pyGDP_function , {'abstract': True, 'namespace': 'Other'}),
             (picklists.Stat, {'abstract': True, 'namespace': 'Other'}),
             (ShapefileParameters, {'abstract': True, 'namespace': 'Other'}),
             (DataServiceParameters, {'abstract': True, 'namespace': 'Other'}),
            #  service modules
            (feature_weighted_grid_statistics, {'namespace': 'processing_services'}),
            (SubmitFeatureCoverageOPenDAP, {'namespace': 'processing_services'}),
            (SubmitCustomBioclim, {'namespace': 'processing_services'}),
            #  Inputs
            (Shapefile, {'configureWidgetType': GDPShapeFileConfiguration,
                         'namespace': 'vector_inputs'}),
            #  Tools
            (ParseGDPOutput.ParseFWGSOutput, {'namespace': 'tools'}),
            (AverageBioclims, {'namespace': 'tools'}),
           ]
_modules.extend(build_pyGDP_service_modules())

