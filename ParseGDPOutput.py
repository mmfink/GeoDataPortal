'''
This file contains a vistrails module used to parse the GDP output into a 
variety of formats

Created on Feb 6, 2014

@author: talbertc
'''
import csv, os

from vistrails.core.modules.vistrails_module import Module

import utils

class ParseFWGSOutput(Module):
    '''converts the output format returned by GDP into something more easily used
    by other workflows
    '''
    _input_ports = [('input_csv', '(edu.utah.sci.vistrails.basic:Path)')]
    _output_ports = [('outputs_dictionary', '(edu.utah.sci.vistrails.basic:Dictionary)')]
    
    def compute(self):
        output_dict = parse_fwgs_output(self.getInputFromPort("input_csv").name,
                                        utils.get_root_dir())
        
        self.setResult('outputs_dictionary', output_dict)
        
#should this functionality be moved directly into pyGDP?
def parse_fwgs_output(gdp_output, output_dir):
    '''This function parses a single GDP output from the feature weighted grid
    statistic into multiple files.
    
    output_dir is the directory to store all outputs in
    '''
    gdp_csv_reader = csv.reader(open(gdp_output, "rb"))
    
    output = {}
    cur_output_writer = None
    for row in gdp_csv_reader:
        if row[0][0] == "#":
            #we have a new dataset
            print "starting on:", row[0][2:]
            output_fname = os.path.join(output_dir, row[0][2:] + ".csv")
            cur_output_writer = csv.writer(open(output_fname, "wb"))
            subheader1 = gdp_csv_reader.next()
            outheader = ['TIMESTEP']
            outheader.extend(subheader1[1:])
            cur_output_writer.writerow(outheader)
            subheader2 = gdp_csv_reader.next() #ignore this one
            output[row[0][2:]] = output_fname
        else:
            cur_output_writer.writerow(row)
            
    return output
    
    
