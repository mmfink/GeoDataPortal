'''
Created on Feb 6, 2014

@author: talbertc
'''
import os
import re
import struct, datetime, decimal, itertools

from PyQt4 import QtGui, QtCore

try:
    from vistrails.core.packagemanager import get_package_manager
    from vistrails.core.modules.vistrails_module import ModuleError
    from vistrails.core.modules.basic_modules import File, Directory, Path
    from vistrails.gui import application
except ImportError:
    from core.packagemanager import get_package_manager
    from core.modules.vistrails_module import ModuleError
    from core.modules.basic_modules import File, Directory, Path
    from gui import application




def set_globals(id, config):
    global identifier, configuration
    identifier = id
    configuration = config

def set_root_dir(session_dir):
    '''sets
    '''
    global _roottempdir, identifier, configuration

    _roottempdir = session_dir
    configuration.cur_session_folder = session_dir

    package_manager = get_package_manager()
    package = package_manager.get_package(identifier)
    dom, element = package.find_own_dom_element()

    configuration.write_to_dom(dom, element)

    print("*" * 79)
    print("*" * 79)
    print("GeoDataPortal output directory:   " + session_dir)
    print("*" * 79)
    print("*" * 79)

def get_root_dir():
    global _roottempdir
    return _roottempdir

def map_ports(module, port_map):
    args = {}
    for port, (flag, access, required) in port_map.iteritems():
        if required or module.hasInputFromPort(port):
            value = module.forceGetInputListFromPort(port)
            if len(value) > 1:
                raise ModuleError(module, 'Multiple items found from Port ' +
                    port + '.  Only single entry handled.  Please remove extraneous items.')
            elif len(value) == 0:
                try:
                    port_tuple = [item for item in module._input_ports if item[0] == port][0]
                    port_info = [port_type for port_type in module._input_ports if port_type[0] == port]
                    port_type = re.split("\.|:", port_info[0][1])[-1][:-1]
                    if port_type in ['Float', 'Integer', 'Boolean', 'List']:
                        value = eval(eval(port_tuple[2]['defaults'])[0])
                    else:
                        value = eval(port_tuple[2]['defaults'])[0]
                except:
                    raise ModuleError(module, 'No items found from Port ' +
                        port + '.  Input is required.')
            else:
                value = module.forceGetInputFromPort(port)

            if access is not None:
                value = access(value)
            if isinstance(value, File) or \
                        isinstance(value, Directory) or \
                        isinstance(value, Path):
                value = path_port(module, port)
            args[flag] = value
    return args

def path_port(module, portName):
    value = module.forceGetInputListFromPort(portName)
    if len(value) > 1:
        raise ModuleError(module, 'Multiple items found from Port ' +
                          portName + '.  Only single entry handled.  Please remove extraneous items.')
    value = value[0]
    path = value.name
    path = path.replace("/", os.path.sep)
    if os.path.exists(path):
        return path
    elif os.path.exists(getFileRelativeToCurrentVT(path, module)):
        return getFileRelativeToCurrentVT(path, module)
    else:
        raise RuntimeError, 'The indicated file or directory, ' + \
            path + ', does not exist on the file system.  Cannot continue!'

def getFileRelativeToCurrentVT(fname, curModule=None):
    #  This is three step approach:
    #  step 1: if fname exists assume it's the one we want and return it.
    #  step 2: Look for the file relative to the current VT.
    #        In effect loop through all the sibling and descendant folders
    #        of the vt file's parent directory and look for the base filename in each.
    #        If we find an identically named file hope for the best and return it.
    #  step 3: Do what we did in step 2 but relative to the current session folder.
    #
    #  If no fname is found in the above three steps raise an error.
    def couldntFindFile():
        msg = "Could not find file: " + fname + "\nPlease point to valid location for this file."
        if curModule is None:
            raise Exception(msg)
        else:
            raise ModuleError(curModule, msg)

    try:
        fname = fname.replace ("\\", "/")
        #  step 1
        if os.path.exists(fname):
            return fname

        #  step 2 (and then step3)
        try:
            app = application.get_vistrails_application()()
            curlocator = app.get_vistrail().locator.name
            curVTdir = os.path.split(curlocator)[0]
        except:
            curVTdir = ""

        root_dir, justfname = os.path.split(fname)
        if justfname.lower() == "hdr.adf":
            justfname = os.path.sep.join([os.path.split(root_dir)[1], justfname])
        for rootdir in [curVTdir, get_root_dir()]:
            if os.path.exists(os.path.join(rootdir, justfname)):
                return os.path.join(rootdir, justfname)
            for root, dirnames, filenames in os.walk(rootdir):
                for dirname in dirnames:
                    if os.path.exists(os.path.join(root, dirname, justfname)):
                        return os.path.join(root, dirname, justfname)

        #  we did our best but couldn't find the file
        couldntFindFile()

    except Exception, e:
        #  if something goes wrong we couldn't find the file throw an error
        couldntFindFile()
        #  Utility functions used by both of the configuration modules
def getPortValue(configWidget, portName):
    for i in xrange(configWidget.module.getNumFunctions()):
        if configWidget.module.functions[i].name == portName:
            return configWidget.module.functions[i].params[0].strValue
    return ""

def get_port_value_list(configWidget, portName):
    output = []
    for i in xrange(configWidget.module.getNumFunctions()):
        if configWidget.module.functions[i].name == portName:
            output.append(configWidget.module.functions[i].params[0].strValue)
    return output

def update_vistrail(configWidget, port, value):
    #  delete the previous list of functions
    functionsToDel = []
    for function in configWidget.module.functions:
        if function.name == port:
            functionsToDel.append(function)

    for function in functionsToDel:
        configWidget.controller.delete_function(function.db_id, configWidget.module.id)

    #  add in new ones
    port_value_list = []
    for val in value:
        port_value_list.append((port, [val]))  #  , -1, False))

    configWidget.controller.update_ports_and_functions(configWidget.module.id,
                                       [], [], port_value_list)

    configWidget.state_changed = False
    configWidget.emit(QtCore.SIGNAL("stateChanged"))
#     configWidget.emit(QtCore.SIGNAL('doneConfigure'), configWidget.module.id)

def expand_ports(port_list):
    new_port_list = []
    for port in port_list:
        port_spec = port[1]
        if type(port_spec) == str:  #  or unicode...
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