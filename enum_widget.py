###############################################################################
##
## Copyright (C) 2010-2012, USGS Fort Collins Science Center. 
## All rights reserved.
## Contact: talbertc@usgs.gov
##
## This file is part of the Software for Assisted Habitat Modeling package
## for VisTrails.
##
## "Redistribution and use in source and binary forms, with or without 
## modification, are permitted provided that the following conditions are met:
##
##  - Redistributions of source code must retain the above copyright notice, 
##    this list of conditions and the following disclaimer.
##  - Redistributions in binary form must reproduce the above copyright 
##    notice, this list of conditions and the following disclaimer in the 
##    documentation and/or other materials provided with the distribution.
##  - Neither the name of the University of Utah nor the names of its 
##    contributors may be used to endorse or promote products derived from 
##    this software without specific prior written permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
## AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
## THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
## PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
## CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
## EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; 
## OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
## WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR 
## OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
## ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
##
## Although this program has been used by the U.S. Geological Survey (USGS), 
## no warranty, expressed or implied, is made by the USGS or the 
## U.S. Government as to the accuracy and functioning of the program and 
## related program material nor shall the fact of distribution constitute 
## any such warranty, and no responsibility is assumed by the USGS 
## in connection therewith.
##
## Any use of trade, firm, or product names is for descriptive purposes only 
## and does not imply endorsement by the U.S. Government.
###############################################################################

from PyQt4 import QtCore, QtGui
from core.modules.constant_configuration import ConstantWidgetMixin

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
