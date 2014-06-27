'''
Created on Feb 6, 2014

@author: talbertc
'''
import os
import re
import struct, datetime, decimal, itertools
import pickle
import datetime

from PyQt4 import QtGui, QtCore

from vistrails.core.cache.hasher import sha_hash
from vistrails.core.packagemanager import get_package_manager
from vistrails.core.modules.vistrails_module import ModuleError
from vistrails.core.modules.basic_modules import File, Directory, Path
from vistrails.gui import application

global _roottempdir
_rootempdir = None

def set_globals(id=None, config=None):
    global identifier, configuration
    identifier = id
    configuration = config

def _set_root_dir(session_dir):
    global _roottempdir
    _roottempdir = session_dir

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
        elif fname == '':
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

def create_dir_module(dname, d=None):
    if d is None:
        d = Directory()
    d.name = dname
    d.upToDate = True
    return d

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

    configWidget.state_changed = True
#      configWidget.emit(QtCore.SIGNAL("stateChanged"))
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





def get_outfname(run_info, subfolder="", runname=""):
    '''We need to retain a cache of previous sucessfull runs
    in order to do this we store a pickled dictionary where:
        key = unique file name ../sessiondir/<run_type>/<uri(shortened)>/<dataset(shortened)>_start_end.nc
        value = hash of all the relevant info
    '''
    uri_shortened = run_info['uri']
    for junk in ['http:', 'dods:', "/", " ", ".ncml", ".nc", ".", ":8080", ":", "-"]:
        uri_shortened = uri_shortened.replace(junk, "")

    dataset = run_info['var_id'].replace("/", "").replace(".", "").replace("\\", "").replace(" ", "_")

    sub_dir = os.path.join(subfolder, "GDPdata_" + run_info['request_type'])
    
    geotype = run_info['geotype'].replace(" ", "_")
    sub_dir2 = get_geo_dname(sub_dir, geotype, run_info['other'])
    
    out_dir = os.path.join(get_root_dir(), sub_dir, sub_dir2, uri_shortened)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if runname:
        dataset = runname + "_" + dataset
        
    start = run_info['start'].split("T")[0]
    end = run_info['end'].split("T")[0]
    timerange = start + "_to_" + end

    out_fname = get_final_fname(sub_dir, dataset, timerange) + ".nc"
    out_fname_rel = os.path.join(sub_dir, sub_dir2, uri_shortened, out_fname)
    out_fname_abs = os.path.join(get_root_dir(), out_fname_rel)


    already_run = os.path.exists(out_fname_abs) and check_hash_entry_pickle(out_fname_rel)

    return out_fname_rel, already_run

def get_geo_dname(geofolder, geotype, otherdata):
    '''given a geometry type (i.e upload:some_shapefile)
    and a dictionary of the column/features we'll be using
    returns a short fname in the format:
    some_shapefile_n where in is a unique number, incremented once for each time
    a new column/feature is used.
    
    This info is stored in a pickled dict in the geofolder
    '''
    geofolder_abs = os.path.join(get_root_dir(), geofolder)
    if not os.path.exists(geofolder_abs):
        os.makedirs(geofolder_abs)

    feature_geoms = get_hash_entry_pickle(geotype, geofolder_abs, "geo.dat")
    if not feature_geoms:
        feature_geoms = {}


    other_geo = sha_hash()
    other_geo.update(str(otherdata))
    other_geo_hash = other_geo.hexdigest()

    if feature_geoms.has_key(other_geo_hash):
        dname = geotype + "_" + str(feature_geoms[other_geo_hash])
    else:
        vals = [v for k, v in feature_geoms.iteritems() if k != 'date_run']
        if vals:
            next_val = max(vals)+1
        else:
            next_val = 1 
        feature_geoms[other_geo_hash] = next_val
        dname = geotype + "_" + str(next_val)
        write_hash_entry_pickle(geotype, feature_geoms, geofolder_abs, "geo.dat")
        
    return dname

def get_final_fname(outfolder, dataset, timerange):
    run_info = get_hash_entry_pickle(dataset, timerange, "runinfo.dat")
    if not run_info:
        run_info = {}

    if run_info.has_key(dataset):
        fname = dataset + "_" + str(run_info[timerange])
    else:
        vals = [v for k, v in run_info.iteritems() if k != 'date_run']
        if vals:
            next_val = max(vals) + 1
        else:
            next_val = 1
        run_info[timerange] = next_val
        fname = dataset + "_" + str(next_val)
        write_hash_entry_pickle(dataset, run_info, outfolder, "runinfo.dat")

    return fname

def hash_file(fname):
    h = sha_hash()
    if os.path.exists(str(fname)):
        h.update(open(fname, "rb").read())
    else:
        h.update(str(fname))
    return h.hexdigest()

def get_picklehash_fname(directory="", datname="gdp_calls.dat"):
    global _roottempdir
    if directory == "":
        directory = _roottempdir
    fname = os.path.join(directory, datname)
    return fname

def get_hash_entry_pickle(key, directory="", datname="gdp_calls.dat"):

    picklename = get_picklehash_fname(directory, datname)

    if os.path.exists(picklename):
        with open(picklename, "rb") as f:
            hash_dict = pickle.load(f)
            return hash_dict.get(key, None)
    else:
        return None

def write_hash_entry_pickle(fname, info={}, directory="", datname="gdp_calls.dat"):

    picklename = get_picklehash_fname(directory, datname)

    info['date_run'] = datetime.datetime.now()
    if os.path.exists(picklename):
        with open(picklename, "rb") as f:
            hash_dict = pickle.load(f)
            hash_dict[fname] = info
    else:
        hash_dict = {fname:info}

    with open(picklename, "wb") as f:
        pickle.dump(hash_dict, f)

def delete_hash_entry_pickle(fname, directory=""):

    picklename = get_picklehash_fname(directory)
    if os.path.exists(picklename):
        with open(picklename, "rb") as f:
            hash_dict = pickle.load(f)
            try:
                del hash_dict[fname]
            except KeyError:
                pass
    else:
        hash_dict = {}

    with open(picklename, "wb") as f:
        pickle.dump(hash_dict, f)

def check_hash_entry_pickle(fname, directory=""):
    global _roottempdir
    if directory == "":
        directory = _roottempdir
    picklename = get_picklehash_fname(directory)
    if os.path.exists(picklename):
        with open(picklename, 'rb') as f:
            hash_dict = pickle.load(f)
            return hash_dict.has_key(fname)
    return False
#  ##methods for querying the hash dict.
#  what data do we have local?
def get_climate_models(directory='None'):
    return get_item_values('climate_model', directory=directory)

def get_emmisions_scenarios(directory='None'):
    return get_item_values('emmisions_scenario', directory=directory)

def get_experiments(directory='None'):
    return get_item_values('experiment', directory=directory)

def get_item_values(key, directory='None'):
    if not directory:
        global _roottempdir
        directory = _roottempdir
    picklename = get_picklehash_fname(directory)
    models = []
    if os.path.exists(picklename):
        with open(picklename, 'rb') as f:
            hash_dict = pickle.load(f)
            for fname, fdict in hash_dict.iteritems():
                if key in fdict:
                    models.append(fdict[key])
        return list(set(models))

def get_previous_fname(source, variable, model, scenario, experiment,
                       directory=None):
    if not directory:
        global _roottempdir
        directory = _roottempdir
    picklename = get_picklehash_fname(directory)
    matching_files = []
    if os.path.exists(picklename):
        with open(picklename, 'rb') as f:
            hash_dict = pickle.load(f)
            for fname, fdict in hash_dict.iteritems():
                var_id = fdict['var_id']
                if fdict.get('source', '') == source and \
                        fdict.get('variable', '')  == variable and \
                        fdict.get('emmisions_scenario', '') == scenario and \
                        fdict.get('climate_model', '') == model and \
                        fdict.get('experiment', '') == experiment:
                    matching_files.append(os.path.join(get_root_dir(), fname))
                    
    return matching_files


def get_bcca_info(var_id):
    info = {}
    info['source'] = var_id.split("_")[0]
    info['resolution'] = var_id.split("_")[1]
    info['variable'] = var_id.split("_")[2]
    info['time_step'] = var_id.split("_")[3]
    info['climate_model'] = var_id.split("_")[4]
    info['emmisions_scenario'] = var_id.split("_")[5]
    info['experiment'] = var_id.split("_")[6]
    return info
