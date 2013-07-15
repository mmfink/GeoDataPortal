import os
import glob
import zipfile
import tempfile

import dateutil.parser

import struct, datetime, decimal, itertools

from core.modules.vistrails_module import Module, ModuleError, ModuleConnector, new_module
from core.modules.basic_modules import File, Directory, Path, new_constant, Constant
from core.modules.basic_modules import String

from PyQt4 import QtCore, QtGui

identifier = 'gov.usgs.GeoDataPortal' 

from enum_widget import build_enum_widget

import pyGDP as _pyGDP
pyGDP = _pyGDP.pyGDPwebProcessing()

global CIDA_dataTypes
''' This is a global dictionary that stores all parameters from CIDA
since there is a cost for each query we are caching the returned values 
in this dictionary so we only have to make each request once per session.
so that we don't have to make requests multiple times.
The format is {serviceName: {'abstract':<abstract>,
                            'URIs':[<URI1>, <URI2>,...]
                            'dataTypes':{datasetName:{'startDate':<date>,
                                        'endDate':<date>}
                        }}}
'''



def shapefileAlreadyOnServer(shpFName):
    '''Checks if a shapefile with the given name is already on 
    the GDP server.
    '''
    shapefiles = pyGDP.getShapefiles()
    if shpFName in shapefiles:
        return True
    if os.path.exists(shpFName):
        serverName = "upload:" +  getServerName(shpFName)
        if serverName in shapefiles:
            return True
    return False

def getServerName(shpFName):
    '''converts a file path of a shapefile to the string format used by GDP
    '''
    return os.path.splitext(os.path.basename(shpFName))[0]


def uploadShapeFile(shpFName):
        '''Uploads a polygon shapefile to the GDP server for analysis
        '''
        outDir = tempfile.gettempdir()
        justName = os.path.splitext(os.path.split(shpFName)[1])[0]
        outFname = os.path.join(outDir, justName)
    
        zipShp = pyGDP.shapeToZip(shpFName, outFname)
        zipShp = zipShp.replace("\\", "/")
    
        shpfile = pyGDP.uploadShapeFile(zipShp)
        
class featureWeightedGridStatistics(Module):
        _input_ports = [('ShapeFileParameters', '(edu.utah.sci.vistrails.basic:Dictionary)'),
                        ('DataServiceParameters', '(edu.utah.sci.vistrails.basic:Dictionary)'),
                        ('Statistic', '(gov.usgs.GeoDataPortal:Stat:Other)', {'defaults':'["MEAN"]'}),
                        ('summarizeTimestep', '(edu.utah.sci.vistrails.basic:Boolean)', {'defaults':'["False"]'}),
                        ('summarizeFeatureAttribute', '(edu.utah.sci.vistrails.basic:Boolean)', {'defaults':'["False"]'})]
        _output_ports = [('outputFile', '(edu.utah.sci.vistrails.basic:File)')]
        
        def compute(self):
            tmpOutDir = self.interpreter.filePool.create_directory()
            os.chdir(tmpOutDir.name)
            print os.getcwd()
            
            shapeParams = self.getInputFromPort('ShapeFileParameters')
            dataServiceParams = self.getInputFromPort('DataServiceParameters')
            
            geoType = shapeParams['File']
            dataSetURI = dataServiceParams['URI']
            varID = dataServiceParams['dataType']
            startTime = dataServiceParams['startDate']
            endTime = dataServiceParams['endDate']
            
            kwargs = {}
            kwargs["attribute"] = shapeParams['Field']
            
            if 'all_values' in shapeParams['Value']:
                kwargs["value"] = 'all_values'
            else:
                kwargs["value"] = shapeParams['Value']
            
            kwargs["stat"] = self.forceGetInputListFromPort("Statistic")
            if kwargs["stat"] == []:
                kwargs["stat"] = "MEAN"
            kwargs["timeStep"] = str(self.forceGetInputFromPort("summarizeTimestep", False)).lower()
            kwargs["summAttr"] = str(self.forceGetInputFromPort("summarizeFeatureAttribute", False)).lower()
            
            outfile = pyGDP.submitFeatureWeightedGridStatistics("upload:" + geoType, dataSetURI, varID, startTime, endTime, **kwargs)
            print "Done"

            f = File()
            f.name = os.path.join(tmpOutDir.name, outfile)
            f.upToDate = True

            self.setResult('outputFile', f)
           
def expand_ports(port_list):
    new_port_list = []
    for port in port_list:
        port_spec = port[1]
        if type(port_spec) == str: # or unicode...
            if port_spec.startswith('('):
                port_spec = port_spec[1:]
            if port_spec.endswith(')'):
                port_spec = port_spec[:-1]
            new_spec_list = []
            for spec in port_spec.split(','):
                spec = spec.strip()
                parts = spec.split(':', 1)
#                print 'parts:', parts
                namespace = None
                if len(parts) > 1:
                    mod_parts = parts[1].rsplit('|', 1)
                    if len(mod_parts) > 1:
                        namespace, module_name = mod_parts
                    else:
                        module_name = parts[1]
                    if len(parts[0].split('.')) == 1:
                        id_str = 'edu.utah.sci.vistrails.' + parts[0]
                    else:
                        id_str = parts[0]
                else:
                    mod_parts = spec.rsplit('|', 1)
                    if len(mod_parts) > 1:
                        namespace, module_name = mod_parts
                    else:
                        module_name = spec
                    id_str = identifier
                if namespace:
                    new_spec_list.append(id_str + ':' + module_name + \
                                         ':' + namespace)
                else:
                    new_spec_list.append(id_str + ':' + module_name)
            port_spec = '(' + ','.join(new_spec_list) + ')'
        new_port_list.append((port[0], port_spec) + port[2:])
#    print new_port_list
    return new_port_list

def pyGDP_module_compute(instance):
        output_dict = {}
        for port in instance._input_ports:
            output_dict[port[0]] = instance.getInputFromPort(port[0])
        
        instance.setResult('DataServiceParameters', output_dict)

def build_pyGDP_service_modules():
    new_classes = {}
    dataSetURIs = pyGDP.getDataSetURI()
    modules = []
    
    global CIDA_dataTypes
    CIDA_dataTypes = {}
    
    #hardwired addition of additional server datasets.
    dataSetURIs.append(["hayhoe", "No abstract provided", ['dods://cida-eros-thredds1.er.usgs.gov:8082/thredds/dodsC/dcp/conus_grid.w_meta.ncml']])
    
    print "Available gridded datasets"
    for dataSetURI in dataSetURIs[1:]:
        name_arr = dataSetURI[0].strip().split()
        class_base = ''.join(n.capitalize() for n in name_arr)
        m_name = class_base.split("/")[-1].split(".")[0]
        
        
        if not m_name.startswith("**provisional"):
            m_doc = dataSetURI[1]
            CIDA_dataTypes[m_name] = {}
            CIDA_dataTypes[m_name]['abstract'] = m_doc
            CIDA_dataTypes[m_name]['URIs'] = [uri.replace("http", "dods") if "/dodsC/" in uri else uri for uri in dataSetURI[2]]
            print dataSetURI[2]
            
            m_inputs = [('URI', '(edu.utah.sci.vistrails.basic:String)', {'defaults':'["' + dataSetURI[2][0] + '"]'}),
                        ('dataType', '(edu.utah.sci.vistrails.basic:String)'),
                        ('startDate', '(edu.utah.sci.vistrails.basic:String)'),
                        ('endDate', '(edu.utah.sci.vistrails.basic:String)'),]
            m_outputs = [('DataServiceParameters', '(edu.utah.sci.vistrails.basic:Dictionary)')]
            klass_dict = {}
            klass_dict["compute"] = pyGDP_module_compute
            
            m_class = new_module(Module, m_name, klass_dict, m_doc)
            m_class.URI = dataSetURI[2][0]
            m_class._input_ports = expand_ports(m_inputs)
            m_class._output_ports = expand_ports(m_outputs)
            m_dict = {'moduleColor':input_color, 'moduleFringe':input_fringe}
            m_dict['configureWidgetType'] = GDPServiceConfiguration
            new_classes[m_name] = (m_class, m_dict)
    return new_classes.values()
  
from gui.modules.module_configure import StandardModuleConfigurationWidget      
class GDPServiceConfiguration(StandardModuleConfigurationWidget):
    def __init__(self, module, controller, parent=None):
        
        StandardModuleConfigurationWidget.__init__(self, module, controller, 
                   parent)
        self.setWindowTitle(module.name)
        
        global CIDA_dataTypes
        
        self.storeDataTypes(self.module.name)
        
        self.URI = getPortValue(self, "URI")
        if not self.URI:
            self.URI = CIDA_dataTypes[self.module.name]["URIs"][0]
            updateVisTrail(self, "URI", [self.URI])
            
        self.dataTypes = getPortValList(self, "dataType")
        if not self.dataTypes:
            self.dataTypes = [self.getDefaultDataType(self.module.name),]
            updateVisTrail(self, "dataType", self.dataTypes)
        
        for dataType in self.dataTypes:
            self.storeTimeRange(self.module.name, dataType)
            
        for d in ["start", "end"]:
            self.__dict__[d + "Date"] = getPortValue(self, d + "Date")
            if not self.__dict__[d + "Date"]:
                self.__dict__[d + "Date"] = self.getDataTypeDate(self.module.name, self.dataTypes[0], d)
                updateVisTrail(self, d + "Date", [self.__dict__[d + "Date"]])
    
        self.build_gui()    
    
    def build_gui(self):
        
        global CIDA_dataTypes
        
        QtGui.QWidget.__init__(self)
    
        layout = QtGui.QVBoxLayout()
    
        urilayout = QtGui.QHBoxLayout()
        uriLabel = QtGui.QLabel("Available URIs: ")
        urilayout.addWidget(uriLabel)
        self.URI_combobox = QtGui.QComboBox(self)
        self.URI_combobox.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        for uri in CIDA_dataTypes[self.module.name]["URIs"]:
            if not uri is None:
                self.URI_combobox.addItem(uri)
        try:
            curIndex = [i for i in range(self.URI_combobox.count()) if self.URI_combobox.itemText(i)==self.URI][0]
        except IndexError:
            curIndex = -1
            
        self.URI_combobox.setCurrentIndex(curIndex)
        urilayout.addWidget(self.URI_combobox)
        layout.addLayout(urilayout)
        
        QtCore.QObject.connect(self.URI_combobox, QtCore.SIGNAL("currentIndexChanged(QString)"), self.changedURICombo)
        
        dataTypelayout = QtGui.QHBoxLayout()
        dataTypeLabel = QtGui.QLabel("Available Data Types: ")
        dataTypelayout.addWidget(dataTypeLabel)
        self.dataTypes_treeview = QtGui.QTreeWidget(self)
        self.dataTypes_treeview.setColumnCount(2)
        self.dataTypes_treeview.setSortingEnabled(True)
        self.dataTypes_treeview.headerItem().setText(0, "short name")
        self.dataTypes_treeview.setColumnWidth(0,200)
        self.dataTypes_treeview.headerItem().setText(1, "description")
        self.dataTypes_treeview.setColumnWidth(1, 125)
        
        self.dataTypes_treeview.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        for dataType in CIDA_dataTypes[self.module.name]["dataTypes"].iterkeys():
            longName = CIDA_dataTypes[self.module.name]["dataTypes"][dataType]["longName"]
            child_item = QtGui.QTreeWidgetItem([dataType, longName])
            child_item.setFlags(QtCore.Qt.ItemIsUserCheckable |
                                QtCore.Qt.ItemIsEnabled)
            if dataType in self.dataTypes:
                child_item.setCheckState(0, QtCore.Qt.Checked)
            else:
                child_item.setCheckState(0, QtCore.Qt.Unchecked)
            self.dataTypes_treeview.addTopLevelItem(child_item)
            
        self.dataTypes_treeview.itemChanged.connect(self.changedDataTypeCombo)
#        curIndex = [i for i in range(self.dataTypes_combobox.count()) if 
#                    self.dataTypes_combobox.itemText(i)==self.getLongDataTypeName(self.dataTypes)][0]
#                    
#                    
#        self.dataTypes_combobox.setCurrentIndex(curIndex)
        dataTypelayout.addWidget(self.dataTypes_treeview)
        layout.addLayout(dataTypelayout)
        
#        QtCore.QObject.connect(self.dataTypes_combobox, QtCore.SIGNAL("currentIndexChanged(QString)"), self.changedDataTypeCombo)
        
        minStart = CIDA_dataTypes[self.module.name]["dataTypes"][self.dataTypes[0]]['startDate']
        self.startDateLabel = QtGui.QLabel("Start Date: \n(min = " + minStart +  ")")
        startlayout = QtGui.QHBoxLayout()
        startlayout.addWidget(self.startDateLabel)
        self.startDateText = QtGui.QLineEdit(self)
        self.startDateText.setText(self.startDate)
        self.startDateText.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        startlayout.addWidget(self.startDateText)
        layout.addLayout(startlayout)
        
        QtCore.QObject.connect(self.startDateText, QtCore.SIGNAL("textChanged(QString)"), self.changedDataTypeCombo)
        
        maxEnd = CIDA_dataTypes[self.module.name]["dataTypes"][self.dataTypes[0]]['endDate']
        self.endDateLabel = QtGui.QLabel("End Date: \n(max = " + maxEnd +  ")")
        endlayout = QtGui.QHBoxLayout()
        endlayout.addWidget(self.endDateLabel)
        self.endDateText = QtGui.QLineEdit(self)
        self.endDateText.setText(self.endDate)
        self.endDateText.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        endlayout.addWidget(self.endDateText)
        layout.addLayout(endlayout)
    
        QtCore.QObject.connect(self.endDateText, QtCore.SIGNAL("textChanged(QString)"), self.endDateChanged)
      
        self.setLayout(layout)
    

    
    def storeDataTypes(self, serviceName):
        global CIDA_dataTypes
        if not CIDA_dataTypes[serviceName].has_key("dataTypes"):
            dataTypes = []
            while not dataTypes and CIDA_dataTypes[serviceName]['URIs']:
                URI = CIDA_dataTypes[serviceName]['URIs'][0]
                dataTypes = dict(zip(pyGDP.getDataType(URI), pyGDP.getDataLongName(URI)))
                if not dataTypes:
                    CIDA_dataTypes[serviceName]['URIs'].pop(0)
                
            CIDA_dataTypes[serviceName]["dataTypes"] = {}
            for dataType, longName in dataTypes.iteritems():
                print dataType, longName
                CIDA_dataTypes[serviceName]["dataTypes"][dataType] = {'longName':longName}
    
    def getDefaultDataType(self, serviceName):
        global CIDA_dataTypes
        return CIDA_dataTypes[self.module.name]["dataTypes"].iterkeys().next()
    
    def getDataTypeDate(self, serviceName, dataTypeName, strWhich):
        global CIDA_dataTypes
        dataType = CIDA_dataTypes[self.module.name]["dataTypes"][dataTypeName]
        if not dataType.has_key(strWhich + 'Date'):
            self.storeTimeRange(serviceName, dataTypeName)
            
        if strWhich.lower() == "start":
            return dataType['startDate']
        elif strWhich.lower() == "end":
            return dataType['endDate']
    
    def storeTimeRange(self, serviceName, dataType=None):
        global CIDA_dataTypes
        if dataType is None:
            dataType = self.getDefaultDataType(serviceName)
        
        if not CIDA_dataTypes[serviceName]["dataTypes"][dataType].has_key('startDate'):
            timeRange = pyGDP.getTimeRange(CIDA_dataTypes[serviceName]['URIs'][0], self.dataTypes[0])
            CIDA_dataTypes[serviceName]["dataTypes"][dataType]['startDate'] = timeRange[0]
            CIDA_dataTypes[serviceName]["dataTypes"][dataType]['endDate'] = timeRange[1]

    def changedURICombo(self):
        self.URI = str(self.URI_combobox.currentText())
        updateVisTrail(self, "URI", [self.URI])

    def changedDataTypeCombo(self):
        treeviewIter = QtGui.QTreeWidgetItemIterator(self.dataTypes_treeview)
        self.dataTypes = []
        while treeviewIter.value():
            item = treeviewIter.value()
            if item.checkState(0) == QtCore.Qt.Checked:
                self.dataTypes.append(str(item.text(0)))

            treeviewIter += 1
        updateVisTrail(self, "dataType", self.dataTypes)
        
    def startDateChanged(self):
        self.startDate = str(self.startDateText.text())
        updateVisTrail(self, "startDate", [self.startDate])
        
    def endDateChanged(self):
        self.endDate = str(self.endDateText.text())
        updateVisTrail(self, "endDate", [self.endDate])
        
    def setMinDateLabel(self):
        minStart = CIDA_dataTypes[self.module.name]["dataTypes"][self.dataTypes[0]]['startDate']
        self.startDateLabel.setText("Start Date: \n(min = " + minStart +  ")")
        
    def setMaxDateLabel(self):
        minStart = CIDA_dataTypes[self.module.name]["dataTypes"][self.dataTypes[0]]['endDate']
        self.startDateLabel.setText("End Date: \n(max = " + minStart +  ")")
     
class shapefile(Module):
    '''A shapefile with parameters needed by GDP
    i.e. the ability to specify a field and specific values in that field for running 
    summary statistics.  Also handles the upload of the file to the GDP server if one 
    with that name isn't already there.  Will provide bad results in the case of identically
    named files.
    '''
    _input_ports = [('File', '(edu.utah.sci.vistrails.basic:Path)'),
                    ('Field', '(edu.utah.sci.vistrails.basic:String)'),
                    ('Value', '(edu.utah.sci.vistrails.basic:String)',{'defaults':'["all_values"]'})]
    _output_ports = [('ShapeFileParameters', '(edu.utah.sci.vistrails.basic:Dictionary)')]
    
    def compute(self):
        output_dict = {}
        
        #check if the specified shapefile already exists on the server
        shpFName = self.getInputFromPort("File").name
        if not shapefileAlreadyOnServer(shpFName):
            uploadShapeFile(shpFName)
        
        output_dict["File"] = getServerName(self.getInputFromPort("File").name)
        output_dict["Field"] = self.getInputFromPort("Field")
        if self.hasInputFromPort("Value"):
            output_dict["Value"] = self.getInputListFromPort("Value")
            if 'all_values' in output_dict["Value"]:
                output_dict["Value"] = ['all_values']
        else:
            output_dict["Value"] = ['all_values']
        
        self.setResult('ShapeFileParameters', output_dict)
     
class GDPShapeFileConfiguration(StandardModuleConfigurationWidget):
    '''The edit config gui thats can be used to specify shapefile parameters
    '''
    def __init__(self, module, controller, parent=None):
        
        StandardModuleConfigurationWidget.__init__(self, module, controller, 
                   parent)
        self.setWindowTitle("shapefile configuration")
        
        self.fields = self.getFields(getPortValue(self, "File"))
        self.checkedFieldValues = getPortValList(self, "Value")
        self.field = getPortValue(self, "Field")
        if not self.field and len(self.fields) > 0:
            self.field = self.fields[0]

        self.build_gui()    
    
    def getFields(self, fname):
        '''returns a list of the fields in a shapefile
        '''
        if fname == '':
            return []
        else:
            f = open(fname.replace(".shp", ".dbf"), "rb")
            inputReader = dbfreader(f)
            header = inputReader.next()
            f.close()
            return header
    
    def getFieldValues(self, fname, fieldName):
        '''returns a list of the unique values in a single field 
        of a shapefile
        '''
        if fname == '':
            return []
        
        f = open(fname.replace(".shp", ".dbf"), "rb")
        inputReader = dbfreader(f)
        
        index = self.fields.index(fieldName)
        inputReader.next()
        inputReader.next()
        fieldVals = []
        for row in inputReader:
            fieldVals.append(str(row[index]).strip())
        
        f.close()
        return list(set(fieldVals))
    
    def build_gui(self):
        QtGui.QWidget.__init__(self)
    
        mainLayout = QtGui.QVBoxLayout()
    
        fileLayout = QtGui.QHBoxLayout()
        fileLabel = QtGui.QLabel("Shapefile: ")
        fileLayout.addWidget(fileLabel)
        self.fileText = QtGui.QLineEdit(self)
        self.fileText.setText(getPortValue(self, "File"))
        self.fileText.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        fileLayout.addWidget(self.fileText)
        browseButton = QtGui.QPushButton("browse", self)
        browseButton.clicked.connect(self.selectFile)
        fileLayout.addWidget(browseButton)
        self.fileText.editingFinished.connect(self.setNewShapefile)
        mainLayout.addLayout(fileLayout)
    
        urilayout = QtGui.QHBoxLayout()
        uriLabel = QtGui.QLabel("Available Fields: ")
        urilayout.addWidget(uriLabel)
        self.shapefileFields = QtGui.QComboBox(self)
        self.populateFields()
            
        
        urilayout.addWidget(self.shapefileFields)
        mainLayout.addLayout(urilayout)
        
        QtCore.QObject.connect(self.shapefileFields, QtCore.SIGNAL("currentIndexChanged(QString)"), self.changedURICombo)
        
        dataTypelayout = QtGui.QHBoxLayout()
        dataTypeLabel = QtGui.QLabel("Available Values: ")
        dataTypelayout.addWidget(dataTypeLabel)
        self.dataTypes_treeview = QtGui.QTreeWidget(self)
        self.dataTypes_treeview.setColumnCount(1)
        self.dataTypes_treeview.setSortingEnabled(True)
        self.dataTypes_treeview.headerItem().setText(0, "short name")
        self.dataTypes_treeview.setColumnWidth(0,200)
        
        self.populateDataTypes()
        self.dataTypes_treeview.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

            
        self.dataTypes_treeview.itemChanged.connect(self.changedDataTypeCombo)

        dataTypelayout.addWidget(self.dataTypes_treeview)
        mainLayout.addLayout(dataTypelayout)        
        self.setLayout(mainLayout)
    
    def selectFile(self):
        self.fileText.setText(QtGui.QFileDialog.getOpenFileNameAndFilter(self, 
                                                "Browse to shapefile (*.shp)"))
        self.setNewShapefile()
    
    def setNewShapefile(self):
        updateVisTrail(self, "File", [str(self.fileText.text())])
        self.populateFields()
        self.populateDataTypes()
        
    def populateFields(self):
        self.fields = self.getFields(getPortValue(self, "File")) 
        
        self.shapefileFields.clear()
        for field in self.fields:
            if not field is None:
                self.shapefileFields.addItem(field)
        try:
            curIndex = [i for i in range(self.shapefileFields.count()) if self.shapefileFields.itemText(i)==self.field][0]
        except IndexError:
            curIndex = 0
            
        self.shapefileFields.setCurrentIndex(curIndex)
        
    def populateDataTypes(self):   
        fieldValues =  self.getFieldValues(getPortValue(self, 'File'),
                                           self.field) 
        fieldValues.insert(0, 'all_values')    
        
        for fieldValue in fieldValues:
            child_item = QtGui.QTreeWidgetItem([str(fieldValue)])
            child_item.setFlags(QtCore.Qt.ItemIsUserCheckable |
                                QtCore.Qt.ItemIsEnabled)
            if fieldValue in self.checkedFieldValues:
                child_item.setCheckState(0, QtCore.Qt.Checked)
            else:
                child_item.setCheckState(0, QtCore.Qt.Unchecked)
            self.dataTypes_treeview.addTopLevelItem(child_item)
    

    
    
    def changedURICombo(self):
        self.field = str(self.shapefileFields.currentText())
        self.values = self.getFieldValues(getPortValue(self, 'File'),
                                           self.field)
        self.populateDataTypes()
        updateVisTrail(self, "Field", [self.field])

    def changedDataTypeCombo(self):
        treeviewIter = QtGui.QTreeWidgetItemIterator(self.dataTypes_treeview)
        self.dataTypes = []
        while treeviewIter.value():
            item = treeviewIter.value()
            if item.checkState(0) == QtCore.Qt.Checked:
                self.dataTypes.append(str(item.text(0)))
            treeviewIter += 1
        updateVisTrail(self, "Value", self.dataTypes)
  
  
#Utility functions used by both of the configuration modules  
def getPortValue(configWidget, portName):
    for i in xrange(configWidget.module.getNumFunctions()):
        if configWidget.module.functions[i].name==portName:
            return configWidget.module.functions[i].params[0].strValue
    return ""

def getPortValList(configWidget, portName):
    output = []
    for i in xrange(configWidget.module.getNumFunctions()):
        if configWidget.module.functions[i].name==portName:
            output.append(configWidget.module.functions[i].params[0].strValue)
    return output

def updateVisTrail(configWidget, port, value):
    
    #delete the previous list of functions
    functionsToDel = []
#    for function in configWidget.module.functions:
#        if function.name == port:
#            functionsToDel.append(function)
#
#    for function in functionsToDel:
#        configWidget.controller.delete_function(function.db_id, configWidget.module.id)  
#        
#    #add in new ones
#    port_value_list = []
#    for val in value:
#        port_value_list.append((port, [val]))#, -1, False))
#    
#    configWidget.controller.update_ports_and_functions(configWidget.module.id, 
#                                       [], [], port_value_list)
#    
#    configWidget.state_changed = False
#    configWidget.emit(QtCore.SIGNAL("stateChanged"))
#    configWidget.emit(QtCore.SIGNAL('doneConfigure'), configWidget.module.id)  
  
        
#taken from http://code.activestate.com/recipes/362715-dbf-reader-and-writer/
def dbfreader(f):
    """Returns an iterator over records in a Xbase DBF file.

    The first row returned contains the mainLayout names.
    The second row contains mainLayout specs: (type, size, decimal places).
    Subsequent rows contain the data records.
    If a record is marked as deleted, it is skipped.

    File should be opened for binary reads.

    """
    
    # See DBF format spec at:
    #     http://www.pgts.com.au/download/public/xbase.htm#DBF_STRUCT
    numrec, lenheader = struct.unpack('<xxxxLH22x', f.read(32))    
    numfields = (lenheader - 33) // 32

    fields = []
    for fieldno in xrange(numfields):
        name, typ, size, deci = struct.unpack('<11sc4xBB14x', f.read(32))
        name = name.replace('\0', '')       # eliminate NULs from string   
        fields.append((name, typ, size, deci))
    yield [field[0] for field in fields]
    yield [tuple(field[1:]) for field in fields]

    terminator = f.read(1)
    assert terminator == '\r'

    fields.insert(0, ('DeletionFlag', 'C', 1, 0))
    fmt = ''.join(['%ds' % fieldinfo[2] for fieldinfo in fields])
    fmtsiz = struct.calcsize(fmt)
    for i in xrange(numrec):
        record = struct.unpack(fmt, f.read(fmtsiz))
        if record[0] != ' ':
            continue                        # deleted record
        result = []
        for (name, typ, size, deci), value in itertools.izip(fields, record):
            if name == 'DeletionFlag':
                continue
            if typ == "N":
                value = value.replace('\0', '').lstrip()
                if value == '':
                    value = 0
                elif deci:
                    value = decimal.Decimal(value)
                else:
                    value = int(value)
            elif typ == 'D':
                y, m, d = int(value[:4]), int(value[4:6]), int(value[6:8])
                value = datetime.date(y, m, d)
            elif typ == 'L':
                value = (value in 'YyTt' and 'T') or (value in 'NnFf' and 'F') or '?'
            elif typ == 'F':
                value = float(value)
            result.append(value)
        yield result
     
class Stat(String):
    '''
    This module is a required class for other modules and scripts within the
    SAHM package. It is not intended for direct use or incorporation into
    the VisTrails workflow by the user.
    '''
    _input_ports = [('value', '(gov.usgs.GeoDataPortal:Stat:Other)')]
    _output_ports = [('value_as_string', '(edu.utah.sci.vistrails.basic:String)', True)]
    _widget_class = build_enum_widget('Stat', 
                                      ['MEAN', 'MINIMUM', 'MAXIMUM', 'VARIANCE', 'STD_DEV', 'SUM', 'COUNT'])

    @staticmethod
    def get_widget_class():
        return Stat._widget_class     
        
def initialize():
    pass


input_color = (0.76, 0.76, 0.8)
input_fringe = [(0.0, 0.0),
                    (0.25, 0.0),
                    (0.0, 1.0)]

_modules = {'Data_services':build_pyGDP_service_modules(),
            'Vector_inputs':[(shapefile, {'configureWidgetType': GDPShapeFileConfiguration})],
            'Geoprocessing_services':[featureWeightedGridStatistics],
            'Other':[(Stat,{'abstract': True})]
            ,}
