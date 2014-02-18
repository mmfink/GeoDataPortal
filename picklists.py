'''
Created on Feb 6, 2014

@author: talbertc
'''


try:
    from vistrails.core.modules.basic_modules import String
except ImportError:
    from core.modules.basic_modules import String
    
from PyQt4 import QtCore, QtGui
from vistrails.gui.modules.constant_configuration import ConstantWidgetMixin

class EnumWidget(QtGui.QComboBox, ConstantWidgetMixin):
    param_values = []
    def __init__(self, param, parent=None):
        """__init__(param: core.vistrail.module_param.ModuleParam,
                    parent: QWidget)


        """
        contents = param.strValue
        contentType = param.type
        QtGui.QComboBox.__init__(self, parent)
        ConstantWidgetMixin.__init__(self, param.strValue)
        # want to look up in registry based on parameter type
        
        self._silent = False
        self.addItem('')
        for val in self.param_values:
            self.addItem(val)


        curIdx = self.findText(contents)
        if curIdx != -1:
            self.setCurrentIndex(curIdx)
        self._contentType = contentType
        self.connect(self,
                     QtCore.SIGNAL('currentIndexChanged(int)'),
                     self.indexChanged)


    def contents(self):
        curIdx = self.currentIndex()
        if curIdx == -1:
            print '*** ""'
            return ''
        print '*** "%s"' % str(self.itemText(curIdx))
        return str(self.itemText(curIdx))


    def setContents(self, strValue, silent=True):
        curIdx = self.findText(strValue)
        if silent:
            self._silent = True
        self.setCurrentIndex(curIdx)
        if not silent:
            self.update_parent()
        else:
            self._silent = False


    def indexChanged(self, index):
        if not self._silent:
            self.update_parent()

def build_enum_widget(name, param_values):
    return type(name, (EnumWidget,), {'param_values': param_values})

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
