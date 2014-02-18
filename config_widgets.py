# ###############################################################################
# ##
# ## Copyright (C) 2010-2012, USGS Fort Collins Science Center. 
# ## All rights reserved.
# ## Contact: talbertc@usgs.gov
# ##
# ## This file is part of the Software for Assisted Habitat Modeling package
# ## for VisTrails.
# ##
# ## "Redistribution and use in source and binary forms, with or without 
# ## modification, are permitted provided that the following conditions are met:
# ##
# ##  - Redistributions of source code must retain the above copyright notice, 
# ##    this list of conditions and the following disclaimer.
# ##  - Redistributions in binary form must reproduce the above copyright 
# ##    notice, this list of conditions and the following disclaimer in the 
# ##    documentation and/or other materials provided with the distribution.
# ##  - Neither the name of the University of Utah nor the names of its 
# ##    contributors may be used to endorse or promote products derived from 
# ##    this software without specific prior written permission.
# ##
# ## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
# ## AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
# ## THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
# ## PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
# ## CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
# ## EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
# ## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; 
# ## OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
# ## WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR 
# ## OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
# ## ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
# ##
# ## Although this program has been used by the U.S. Geological Survey (USGS), 
# ## no warranty, expressed or implied, is made by the USGS or the 
# ## U.S. Government as to the accuracy and functioning of the program and 
# ## related program material nor shall the fact of distribution constitute 
# ## any such warranty, and no responsibility is assumed by the USGS 
# ## in connection therewith.
# ##
# ## Any use of trade, firm, or product names is for descriptive purposes only 
# ## and does not imply endorsement by the U.S. Government.
# ###############################################################################
# 
# from PyQt4 import QtCore, QtGui
# import os
# import dateutil.parser
# import datetime
# 
# import pyGDP as _pyGDP
# pyGDP = _pyGDP.pyGDPwebProcessing()
# 
# from vistrails.core.modules.module_configure import StandardModuleConfigurationWidget
# from vistrails.core.modules.constant_configuration import ConstantWidgetMixin
# 
# class GDPDataWidget(QtGui.QTreeWidget):
#     
#     def __init__(self, p_value, URI, parent=None):
#         
# 
#         QtGui.QTreeWidget.__init__(self, parent)
#         self.URI = URI
#         self.setColumnCount(2)
#         self.setSelectionBehavior(QtGui.QTreeView.SelectRows)
# 
#         self.tree_items = {}
# #        for source, data_list in self.available_tree.iteritems():
# #            #print source, file_list
# #            source_item = QtGui.QTreeWidgetItem([source])
# #            self.addTopLevelItem(source_item)
# #            for dataset in data_list:
# #                child_item = QtGui.QTreeWidgetItem([dataset])#, resVal, aggVal])
# #                child_item.setFlags(QtCore.Qt.ItemIsUserCheckable |
# #                                    QtCore.Qt.ItemIsEnabled)
# #                child_item.setCheckState(0, QtCore.Qt.Unchecked)
# #                source_item.addChild(child_item)
# #                self.tree_items[curVal] = child_item
# #        self.set_values(p_value)
# 
#     def set_values(self, str_value):
#         #print 'set_values:', str_value 
#         values = []
# #        if str_value:
# #            values = eval(str_value)
# #        files = {}
# #        for k in self.tree_items.iterkeys():
# #            files[k[0]] = k[1:]
# #        for value in values:
# #            if value[0] in files.keys():
# #                try:
# #                    oldValue = (value[0], files[value[0]][0], files[value[0]][1])
# #                    self.tree_items[oldValue].setCheckState(0, QtCore.Qt.Checked)
# #                    item = self.itemWidget(self.tree_items[oldValue], 2)
# #                    if value[1] == '1':
# #                        item.setCheckState(QtCore.Qt.Checked)
# #                    else:
# #                        item.setCheckState(QtCore.Qt.Unchecked)
# ##                    item = self.itemWidget(self.tree_items[oldValue], 3)
# ##                    item.setCurrentIndex(self.resamplingMethods.index(value[2]))
# ##                    item = self.itemWidget(self.tree_items[oldValue], 4)
# ##                    item.setCurrentIndex(self.aggregationMethods.index(value[3]))
# #                except ValueError:
# #                    pass
#     
#     def get_values(self):
#         #print 'get_values:'
#         values = []
# #        for value, item in self.tree_items.iteritems():
# #            #print value, item
# #            if item.checkState(0) == QtCore.Qt.Checked:
# #                if self.itemWidget(item, 2).checkState() == QtCore.Qt.Checked:
# #                    categorical = '1'
# #                    resampleMethod = 'NearestNeighbor'
# #                    aggMethod = 'Majority'
# #                else:
# #                    categorical = '0'
# #                    resampleMethod = 'Bilinear'
# #                    aggMethod = 'Mean'
# ##                resampleMethod = str(self.itemWidget(item, 3).currentText())
# ##                aggMethod = str(self.itemWidget(item, 4).currentText())
# #                   
# #                values.append((value[0], categorical, resampleMethod, aggMethod))
# ##        print 'get_vals = ', str(values)
#         return str(values)
#                
# class GDPDataConfigurationWidget(GDPDataWidget, 
#                                        ConstantWidgetMixin):
#     
#     def __init__(self, param, URI, parent=None):
#         """__init__(param: core.vistrail.module_param.ModuleParam,
#                     parent: QWidget)
# 
#         Initialize the line edit with its contents. Content type is limited
#         to 'int', 'float', and 'string'
# 
#         """
# #        PredictorListWidget.__init__(self, param.strValue, URI, 
# #                                     parent)
#         ConstantWidgetMixin.__init__(self, param.strValue)
#         # assert param.namespace == None
#         # assert param.identifier == 'edu.utah.sci.vistrails.basic'
# #         self.available_tree = available_tree
# #         self.setColumnCount(2)
# #         for source, file_list in self.available_tree.iteritems():
# #             source_item = QtGui.QTreeWidgetItem([source])
# #             self.addTopLevelItem(source_item)
# #             for (file, desc) in file_list:
# #                 child_item = QtGui.QTreeWidgetItem([file, desc])
# #                 child_item.setFlags(QtCore.Qt.ItemIsUserCheckable |
# #                                     QtCore.Qt.ItemIsEnabled)
# #                 child_item.setCheckState(0, QtCore.Qt.Unchecked)
# #                 source_item.addChild(child_item)
# 
#         contents = param.strValue
#         contentType = param.type
# 
#         # need to deserialize contents and set tree widget accordingly
#         # self.setText(contents)
#         self._contentType = contentType
# #         self.connect(self,
# #                      QtCore.SIGNAL('returnPressed()'),
# #                      self.update_parent)
# 
#     def contents(self):
#         """contents() -> str
#         Re-implement this method to make sure that it will return a string
#         representation of the value that it will be passed to the module
#         As this is a QLineEdit, we just call text()
# 
#         """
#         return self.get_values()
# 
#     def setContents(self, strValue, silent=True):
#         """setContents(strValue: str) -> None
#         Re-implement this method so the widget can change its value after 
#         constructed. If silent is False, it will propagate the event back 
#         to the parent.
#         As this is a QLineEdit, we just call setText(strValue)
#         """
#         self.set_values(strValue)
#         if not silent:
#             self.update_parent()
# 
#     def sizeHint(self):
#         return QtCore.QSize(912, 912)
#     
#     def minimumSizeHint(self):
#         return self.sizeHint()
#     
#     ###########################################################################
#     # event handlers
# 
#     def focusInEvent(self, event):
#         """ focusInEvent(event: QEvent) -> None
#         Pass the event to the parent
# 
#         """
#         self._contents = self.get_values()
#         if self.parent():
#             QtCore.QCoreApplication.sendEvent(self.parent(), event)
#         QtGui.QTreeWidget.focusInEvent(self, event)
# 
#     def focusOutEvent(self, event):
#         self.update_parent()
#         QtGui.QTreeWidget.focusOutEvent(self, event)
#         if self.parent():
#             QtCore.QCoreApplication.sendEvent(self.parent(), event)
# 
# class GDPDataConfiguration(StandardModuleConfigurationWidget):
#     # FIXME add available_dict as parameter to allow config
#     def __init__(self, module, controller, URI, parent=None):
#         StandardModuleConfigurationWidget.__init__(self, module, controller, 
#                                                    parent)
#         self.URI = URI
#         # set title
#         if module.has_annotation_with_key('__desc__'):
#             label = module.get_annotation_by_key('__desc__').value.strip()
#             title = '%s (%s) Module Configuration' % (label, module.name)
#         else:
#             title = '%s Module Configuration' % module.name
#         self.setWindowTitle(title)
# #        self.build_gui(URI)
# #        self.DataTypeList.setCurrentItem(self.DataTypeList.item(0))
# 
#     def show(self):
#         StandardModuleConfigurationWidget.show()
#         self.build_gui(self.URI)
#         self.DataTypeList.setCurrentItem(self.DataTypeList.item(0))
# 
#     def build_gui(self, URI):
#         self.p_value = ''
#         for function in self.module.functions:
#             if function.name == 'value':
#                 self.p_value = function.parameters[0].strValue
#         
#         self.DataTypeList = QtGui.QListWidget()
#         self.DataTypeList.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
# 
#         dataTypes = pyGDP.getDataType(URI, False)
#         for dataType in dataTypes:
#             item = QtGui.QListWidgetItem(dataType)
#             self.DataTypeList.addItem(item)
#         
#         layout = QtGui.QVBoxLayout()
#         self.lblTitle = QtGui.QLabel("Available Data Types")
#         layout.addWidget(self.lblTitle)
#         
#         layout.addWidget(self.DataTypeList)
# 
#         self.dateRangeLabel = QtGui.QLabel("\n\nAvailable range = 10/10/1900 - 10/10/2099")
#         layout.addWidget(self.dateRangeLabel)
# 
#         self.dateLayout = QtGui.QHBoxLayout()
#         self.startDateLabel = QtGui.QLabel("Start Date:")
#         self.startDateEdit = QtGui.QLineEdit("")
#         self.startDateEdit.setInputMask(r"00/00/0000")
#         self.dateLayout.addWidget(self.startDateLabel)
#         self.dateLayout.addWidget(self.startDateEdit)
#         self.endDateLabel = QtGui.QLabel("End Date:")
#         self.endDateEdit = QtGui.QLineEdit("")
#         self.endDateEdit.setInputMask(r"00/00/0000")
#         self.dateLayout.addWidget(self.endDateLabel)
#         self.dateLayout.addWidget(self.endDateEdit)
#         layout.addLayout(self.dateLayout)
# 
#         self.buttonLayout = QtGui.QHBoxLayout()
#         self.okButton = QtGui.QPushButton('&OK', self)
#         self.okButton.setFixedWidth(110)
#         self.buttonLayout.addWidget(self.okButton)
#         
# 
#         layout.addLayout(self.buttonLayout)
#         self.connect(self.okButton, QtCore.SIGNAL('clicked(bool)'), 
#                      self.okTriggered)
#         self.connect(self.DataTypeList, QtCore.SIGNAL('itemSelectionChanged()'),
#                     self.selectionChanged)
#         self.setLayout(layout)
# 
#     def selectionChanged(self):
#         self.updateDateRange()
#         
#     def updateDateRange(self):
#         curItem = self.DataTypeList.currentItem().text()
#         timeRange = pyGDP.getTimeRange(self.URI, str(curItem))
#         
#         startDate = dateutil.parser.parse(timeRange[0])
#         endDate = dateutil.parser.parse(timeRange[1])
#         self.startDateEdit.setText(startDate.strftime('%m%d%Y'))
#         self.endDateEdit.setText(endDate.strftime('%m%d%Y'))
#         self.dateRangeLabel.setText("\nAvailible Range:  " +
#                                     startDate.strftime('%m/%d/%Y') + " - " +
#                                     endDate.strftime('%m/%d/%Y') +
#                                     "\nMM\DD\YYYY format")
# 
#     def okTriggered(self):
#         output = {}
#         ['URI', 'dataType', 'startDate', 'endDate']
#         output['URI'] = self.URI
#         output['dataType'] = str(self.DataTypeList.currentItem().text())
#         output['startDate'] = datetime.datetime(int(self.startDateEdit.text()[-4:]), int(self.startDateEdit.text()[:2]), int(self.startDateEdit.text()[3:5]))
#         output['endDate'] = datetime.datetime(int(self.endDateEdit.text()[-4:]), int(self.endDateEdit.text()[:2]), int(self.endDateEdit.text()[3:5]))
#         str_value = str(output)
#         if str_value != self.p_value:
#             functions = [('value', [str_value])]
#             self.controller.update_functions(self.module, functions)
#         self.close()
# 
#     def sizeHint(self):
#         return QtCore.QSize(912, 912)
#     
# 
# def get_GDPData_widget(class_name, URI):
#     def __init__(self, param, parent=None):
#         GDPDataConfigurationWidget.__init__(self, param, URI, parent)
#     class_name += "_GDPDataWidget"
#     widget_class = type(class_name, (GDPDataConfigurationWidget,),
#                         {'__init__': __init__})
#     return widget_class
# 
# def get_GDPData_config(class_name, URI):
#     def __init__(self, module, controller, parent=None):
#         GDPDataConfiguration.__init__(self, module, controller, URI, 
#                                             parent)
#     class_name += "_GDPDataListConfig"
#     widget_class = type(class_name, (GDPDataConfiguration,),
#                         {'__init__': __init__})
#     return widget_class
# 
# class GDPShapeFileWidget(QtGui.QTreeWidget):
#     
#     def __init__(self, p_value, URI, parent=None):
#         
# 
#         QtGui.QTreeWidget.__init__(self, parent)
#         self.URI = URI
#         self.setColumnCount(2)
# 
#         self.tree_items = {}
# 
#     def set_values(self, str_value):
#         #print 'set_values:', str_value 
#         values = []
#     
#     def get_values(self):
#         #print 'get_values:'
#         values = []
#         return str(values)
#                
# class GDPShapeFileConfigurationWidget(GDPDataWidget, 
#                                        ConstantWidgetMixin):
#     
#     def __init__(self, param, URI, parent=None):
#         """__init__(param: core.vistrail.module_param.ModuleParam,
#                     parent: QWidget)
# 
#         Initialize the line edit with its contents. Content type is limited
#         to 'int', 'float', and 'string'
# 
#         """
# #        PredictorListWidget.__init__(self, param.strValue, URI, 
# #                                     parent)
#         ConstantWidgetMixin.__init__(self, param.strValue)
# 
#         contents = param.strValue
#         contentType = param.type
# 
#         self._contentType = contentType
# 
#     def contents(self):
#         """contents() -> str
#         Re-implement this method to make sure that it will return a string
#         representation of the value that it will be passed to the module
#         As this is a QLineEdit, we just call text()
# 
#         """
#         return self.get_values()
# 
#     def setContents(self, strValue, silent=True):
#         """setContents(strValue: str) -> None
#         Re-implement this method so the widget can change its value after 
#         constructed. If silent is False, it will propagate the event back 
#         to the parent.
#         As this is a QLineEdit, we just call setText(strValue)
#         """
#         self.set_values(strValue)
#         if not silent:
#             self.update_parent()
# 
#     def sizeHint(self):
#         return QtCore.QSize(912, 912)
#     
#     def minimumSizeHint(self):
#         return self.sizeHint()
#     
#     ###########################################################################
#     # event handlers
# 
#     def focusInEvent(self, event):
#         """ focusInEvent(event: QEvent) -> None
#         Pass the event to the parent
# 
#         """
#         self._contents = self.get_values()
#         if self.parent():
#             QtCore.QCoreApplication.sendEvent(self.parent(), event)
#         QtGui.QTreeWidget.focusInEvent(self, event)
# 
#     def focusOutEvent(self, event):
#         self.update_parent()
#         QtGui.QTreeWidget.focusOutEvent(self, event)
#         if self.parent():
#             QtCore.QCoreApplication.sendEvent(self.parent(), event)
# 
# class GDPShapeFileConfiguration(StandardModuleConfigurationWidget):
#     # FIXME add available_dict as parameter to allow config
#     def __init__(self, module, controller, URI, parent=None):
#         StandardModuleConfigurationWidget.__init__(self, module, controller, 
#                                                    parent)
#         self.URI = URI
#         # set title
#         if module.has_annotation_with_key('__desc__'):
#             label = module.get_annotation_by_key('__desc__').value.strip()
#             title = '%s (%s) Module Configuration' % (label, module.name)
#         else:
#             title = '%s Module Configuration' % module.name
#         self.setWindowTitle(title)
# #        self.build_gui(URI)
# #        self.DataTypeList.setCurrentItem(self.DataTypeList.item(0))
# 
#     def show(self):
#         StandardModuleConfigurationWidget.show()
#         self.build_gui()
#         self.DataTypeList.setCurrentItem(self.DataTypeList.item(0))
# 
#     def build_gui(self):
#         self.p_value = ''
#         for function in self.module.functions:
#             if function.name == 'value':
#                 self.p_value = function.parameters[0].strValue
#         
#         self.DataTypeList = QtGui.QListWidget()
#         self.DataTypeList.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
# 
#         dataTypes = []
#         for dataType in dataTypes:
#             item = QtGui.QListWidgetItem(dataType)
#             self.DataTypeList.addItem(item)
#         
#         layout = QtGui.QVBoxLayout()
#         self.lblTitle = QtGui.QLabel("Available Data Types")
#         layout.addWidget(self.lblTitle)
#         
#         layout.addWidget(self.DataTypeList)
# 
#         self.dateRangeLabel = QtGui.QLabel("\n\nAvailable range = 10/10/1900 - 10/10/2099")
#         layout.addWidget(self.dateRangeLabel)
# 
#         self.dateLayout = QtGui.QHBoxLayout()
#         self.startDateLabel = QtGui.QLabel("Start Date:")
#         self.startDateEdit = QtGui.QLineEdit("")
#         self.startDateEdit.setInputMask(r"00/00/0000")
#         self.dateLayout.addWidget(self.startDateLabel)
#         self.dateLayout.addWidget(self.startDateEdit)
#         self.endDateLabel = QtGui.QLabel("End Date:")
#         self.endDateEdit = QtGui.QLineEdit("")
#         self.endDateEdit.setInputMask(r"00/00/0000")
#         self.dateLayout.addWidget(self.endDateLabel)
#         self.dateLayout.addWidget(self.endDateEdit)
#         layout.addLayout(self.dateLayout)
# 
#         self.buttonLayout = QtGui.QHBoxLayout()
#         self.okButton = QtGui.QPushButton('&OK', self)
#         self.okButton.setFixedWidth(110)
#         self.buttonLayout.addWidget(self.okButton)
#         
# 
#         layout.addLayout(self.buttonLayout)
#         self.connect(self.okButton, QtCore.SIGNAL('clicked(bool)'), 
#                      self.okTriggered)
#         self.connect(self.DataTypeList, QtCore.SIGNAL('itemSelectionChanged()'),
#                     self.selectionChanged)
#         self.setLayout(layout)
# 
#     def selectionChanged(self):
#         self.updateDateRange()
#         
#     def updateDateRange(self):
#         curItem = self.DataTypeList.currentItem().text()
#         timeRange = pyGDP.getTimeRange(self.URI, str(curItem))
#         
#         startDate = dateutil.parser.parse(timeRange[0])
#         endDate = dateutil.parser.parse(timeRange[1])
#         self.startDateEdit.setText(startDate.strftime('%m%d%Y'))
#         self.endDateEdit.setText(endDate.strftime('%m%d%Y'))
#         self.dateRangeLabel.setText("\nAvailible Range:  " +
#                                     startDate.strftime('%m/%d/%Y') + " - " +
#                                     endDate.strftime('%m/%d/%Y') +
#                                     "\nMM\DD\YYYY format")
# 
#     def okTriggered(self):
#         output = {}
#         ['URI', 'dataType', 'startDate', 'endDate']
#         output['URI'] = self.URI
#         output['dataType'] = str(self.DataTypeList.currentItem().text())
#         output['startDate'] = datetime.datetime(int(self.startDateEdit.text()[-4:]), int(self.startDateEdit.text()[:2]), int(self.startDateEdit.text()[3:5]))
#         output['endDate'] = datetime.datetime(int(self.endDateEdit.text()[-4:]), int(self.endDateEdit.text()[:2]), int(self.endDateEdit.text()[3:5]))
#         str_value = str(output)
#         if str_value != self.p_value:
# #            print 'okTriggered:', str_value
#             functions = [('value', [str_value])]
#             self.controller.update_functions(self.module, functions)
#         self.close()
# 
#     def sizeHint(self):
#         return QtCore.QSize(912, 912)
#     
# 
# def get_GDPShapeFile_widget(class_name, URI):
#     def __init__(self, param, parent=None):
#         GDPDataConfigurationWidget.__init__(self, param, URI, parent)
#     class_name += "_GDPDataWidget"
#     widget_class = type(class_name, (GDPDataConfigurationWidget,),
#                         {'__init__': __init__})
#     return widget_class
# 
# def get_GDPShapeFile_config(class_name, URI):
#     def __init__(self, module, controller, parent=None):
#         GDPDataConfiguration.__init__(self, module, controller, URI, 
#                                             parent)
#     class_name += "_GDPDataListConfig"
#     widget_class = type(class_name, (GDPDataConfiguration,),
#                         {'__init__': __init__})
#     return widget_class
