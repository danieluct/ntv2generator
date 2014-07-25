""" 
    This file is part of ntv2generator.

    ntv2generator is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    ntv2generator is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with ntv2generator.  If not, see <http://www.gnu.org/licenses/>.
"""

import datetime
import os
import struct


def _format_8bit_str(input_string):
    return "{0:<8}".format(input_string[:8])


def _format_ntv2_record(name, value, type_='f', binary_format=True):
    if name == "RECORD":
        if binary_format:
            return struct.pack("<4f",*value)
        else:
            return " ".join(["{0:6f}".format(x) for x in value]) + "\n"
    else:
        if type_ == "s":
            if binary_format:
                return struct.pack("<8s8s",
                                    _format_8bit_str(name),
                                    _format_8bit_str(value))
            else:
                return (_format_8bit_str(name) + " " +
                        _format_8bit_str(value) + "\n")
        elif type_ == "i":
            if binary_format:
                return struct.pack("<8si4x",
                                    _format_8bit_str(name),
                                    value)
            else:
                return _format_8bit_str(name) + " " + str(int(value)) + "\n"
        elif type_ == "f":
            if binary_format:
                return struct.pack("<8sd",
                                    _format_8bit_str(name),
                                    value)
            else:
                return (_format_8bit_str(name) + " " +
                        "{0:4f}".format(value) + "\n")
        else:
            raise Exception("Unknown record format!")


class CRSDef:
    def __init__(self, name, major_axis, minor_axis):
        self.name = name
        self.major_axis = major_axis
        self.minor_axis = minor_axis

ETRS89_CRS = CRSDef("ETRS89", 6378137.000, 6356752.314)


class BoundingBox:
    def __init__(self, north, south, west, east):
        self.north = north
        self.south = south
        self.east = east
        self.west = west

        
class NTv2File:
    def __init__(self,
                 coord_unit="SECONDS"):                 
        self.has_overview = False            
        self.added_sub_files = 0
        self.subfiles_dict ={}
        
        if coord_unit not in ["SECONDS", "MINUTES", "DEGREES"]:
            raise Exception("Unknown unit for coordinates!")
        else:
            self.gridshift_data_type = coord_unit
            
    def set_ref_systems(self, crs_from, crs_to, overwrite=False):
        if self.has_overview and not overwrite:
            raise Exception("Header was previously set!")
            
        self.crs_from = crs_from
        self.crs_to = crs_to
        self.has_overview = True
        
    def add_subfile(self, subFile, overwrite=False):
        if subFile.name in self.subfiles_dict.keys() and not overwrite:
            raise Exception(
                "Subfile with name {0} already exists!".format(subFile.name)
                )
        if (subFile.parent != "NONE"
            and subFile.parent not in self.subfiles_dict.keys()):
            raise Exception(
                "Parent with name {0} was not defined!".format(subFile.name)
                )        
        self.subfiles_dict[subFile.name] = subFile
        
    def create_subfile(self, name, parent='NONE'):
        if name in self.subfiles_dict.keys() and not overwrite:
            raise Exception(
                "Subfile with name {0} already exists!".format(subFile.name)
                )
        if parent!= "NONE" and subFile.parent not in self.subfiles_dict.keys():
            raise Exception(
                "Parent with name {0} was not defined!".format(subFile.name)
                )
        subFile = NTv2SubFile(name, parent)
        self.subfiles_dict[name] = subFile
        return subFile
        
    def write_to_file(self, path, name, f_format='b',
                    overwrite=False):                    
        self.file_name = os.path.join(path, name)        
        if os.path.exists(self.file_name) and not overwrite:
            raise Exception("File already exists!")

        if f_format == 'a' or f_format == 'A':
            binary_format = False
        elif f_format == 'b' or f_format == 'B':
            binary_format = True
        else:
            raise Exception("Unknown format!")

        if not self.has_overview:
            raise Exception("Header info was not set!")        
        if not self.subfiles_dict.keys():
            raise Exception("No subfiles have been defined!")       
            
        if binary_format:
            output_file = open(self.file_name, "wb")
        else:
            output_file = open(self.file_name, "w")
            
        self._write_header(output_file, binary_format)        
        for key in self.subfiles_dict.keys():
            self.subfiles_dict[key].write_to_file(output_file, binary_format)           
        self._write_eof(output_file, binary_format)
        output_file.close()

    def _write_eof(self, output_file, binary_format=True):
        if binary_format:
            output_file.write(struct.pack("<8s8x", "END    "))
        else:
            output_file.write("END")
        
    def _write_header(self, output_file, binary_format=True):                            
        if not self.has_overview:
            raise Exception("No overview file defined!")
                            
        output_file.write(_format_ntv2_record("NUM_OREC", 11,
                                              'i', binary_format))
        output_file.write(_format_ntv2_record("NUM_SREC", 11,
                                              'i', binary_format))                            
        output_file.write(_format_ntv2_record("NUM_FILE",
                                              len(self.subfiles_dict.keys()),
                                              'i', binary_format))
        output_file.write(_format_ntv2_record("GS_TYPE",
                                              self.gridshift_data_type,
                                              's', binary_format))
        output_file.write(_format_ntv2_record("VERSION", "NTv2.0",
                                              's', binary_format))                           
        output_file.write(_format_ntv2_record("SYSTEM_F", self.crs_from.name,
                                              's', binary_format))
        output_file.write(_format_ntv2_record("SYSTEM_T", self.crs_to.name,
                                              's', binary_format))
        output_file.write(_format_ntv2_record("MAJOR_F ",
                                              self.crs_from.major_axis,
                                              'f', binary_format))
        output_file.write(_format_ntv2_record("MINOR_F ",
                                              self.crs_from.minor_axis,
                                              'f', binary_format))
        output_file.write(_format_ntv2_record("MAJOR_T ",
                                              self.crs_to.major_axis,
                                              'f', binary_format))
        output_file.write(_format_ntv2_record("MINOR_T ",
                                              self.crs_to.minor_axis,
                                              'f', binary_format))
        if not binary_format:
            output_file.write("\n")


class NTv2SubFile:
    def __init__(self, name, parent ='NONE'):
        self.name = name
        self.parent = parent
        self.bbox_set = False
        self.inc_set = False
        self.dates_set = False
        self.gs_count = 0
        self.gs_list = []
        
    def set_limits(self, bounding_box, overwrite=False):
        if self.bbox_set and not overwrite:
            raise Exception("Subfile limits have already been set!")
        self.bounding_box = bounding_box
        self.bbox_set = True
        
    def set_coord_increment(self, lat_increment,
                          long_increment, overwrite=False):
        if not self.bbox_set:
            raise Exception(
                "Subfile limits have to be set before setting increments!"
                ) 
        if self.inc_set and not overwrite:
            raise Exception(
                "Subfile coordinate increments have already been set!"
                )
        
        self.lat_increase = lat_increment
        self.long_increase = long_increment
        self.inc_set = True
        self.gs_count = int(
                    (abs(self.bounding_box.north-self.bounding_box.south)/
                     self.lat_increase)
                    + 1
                    )* int(
                    (abs(self.bounding_box.east-self.bounding_box.west)/
                     self.long_increase)
                    + 1)
        
    def set_dates(self, create_date, update_date=None, overwrite=False):
        if self.dates_set and not overwrite:
            raise Exception("Subfile date have already been set!")
        
        self.date_created = create_date
        if update_date is None:
            self.date_updated = self.date_created
        else:
            self.date_updated = update_date
        self.dates_set = True

    def set_gridshifts(grid_shift_array, overwrite=False):
        if not self.bbox_set or not self.inc_set:
            raise Exception(
                "Subfile limits and increments have to be set before "
                "setting grid shifts!"
                ) 
        if self.gs_list and not overwrite:
            raise Exception("Grid shift have already been set!")
        if len(grid_shift_array) < self.gs_count:
            raise Exception(
                "Input array does not contain enough grid shifts. "
                "Required entries: {0}.".format(self.gc_count)
                )
        self.gs_list = grid_shift_array

    def clear_gridshifts():
        self.gs_list = []

    def add_gridshift(latitude_shift, longitude_shift,
                     latitude_accuracy, longitude_accuracy):
        if len(self.gs_list) + 1 > self.gs_count:
            raise Exception("All grid shifts have already been added!")
        else:
            self.gs_list.append([
                latitude_shift, longitude_shift,
                latitude_accuracy, longitude_accuracy
                ])                
        
    def write_to_file(self, output_file, binary_format=True):
        if not self.bbox_set:
            raise Exception(
                "Subfile limits have to be set before saving subfile!"
                )
        if not self.inc_set:
            raise Exception(
                "Subfile increments have to be set before saving subfile!"
                )
        if not self.dates_set:
            raise Exception(
                "Subfile dates have to be set before saving subfile!"
                )
        if len(self.gs_list) < self.gs_count:
            raise Exception(
                "All grid shift points have to be added before saving "
                "subfile " + self.name + "! "
                "Current entries: {0}. Expected: {1}".format(len(self.gs_list),
                                                             self.gs_count))
        self._write_header(output_file, binary_format)
        for grid_shift in self.gs_list:
            self._write_record(output_file,
                             grid_shift[0], grid_shift[1],
                             grid_shift[2], grid_shift[3],
                             binary_format)
        if not binary_format:
            output_file.write("\n")
        
    def _write_header(self, output_file, binary_format=True):
        if not self.bbox_set:
            raise Exception(
                "Subfile limits have not been set!"
                )
        if not self.inc_set:
            raise Exception(
                "Subfile coordinate increments have not been set!"
                )
        if not self.dates_set:
            raise Exception(
                "Subfile dates have not been set!"
                )
        if self.gs_count == 0:
            raise Exception(
                "There is something wrong with the limits and/or increments!"
                )
        
        output_file.write(_format_ntv2_record("SUB_NAME", self.name,
                                           "s", binary_format))
        output_file.write(_format_ntv2_record("PARENT", self.parent,
                                           "s", binary_format))
        output_file.write(_format_ntv2_record("CREATED ",
                                           self.date_created.strftime("%d%m%Y"),
                                           "s", binary_format))
        output_file.write(_format_ntv2_record("UPDATED ",
                                           self.date_updated.strftime("%d%m%Y"),
                                           "s", binary_format))        
        output_file.write(_format_ntv2_record("S_LAT", self.bounding_box.south,
                                           "f", binary_format))
        output_file.write(_format_ntv2_record("N_LAT", self.bounding_box.north,
                                              "f", binary_format))
        output_file.write(_format_ntv2_record("E_LONG",
                                              self.bounding_box.east*-1,
                                              "f", binary_format))
        output_file.write(_format_ntv2_record("W_LONG",
                                              self.bounding_box.west*-1,
                                              "f", binary_format))
        output_file.write(_format_ntv2_record("LAT_INC", self.lat_increase,
                                           "f", binary_format))
        output_file.write(_format_ntv2_record("LONG_INC", self.long_increase,
                                           "f", binary_format))
        output_file.write(_format_ntv2_record("GS_COUNT", self.gs_count,
                                           "i", binary_format))
        if not binary_format:
            output_file.write("\n")    
        
    def _write_record(output_file,
                    latitude_shift, longitude_shift,
                    latitude_accuracy, longitude_accuracy,
                    binary_format=True):
        output_file.write(_format_ntv2_record("RECORD",
                            [
                                latitude_shift, longitude_shift,
                                latitude_accuracy, longitude_accuracy
                            ],
                            "f", binary_format))

   
def _test():
    f_test = NTv2File()
    crs_from = CRSDef("Stereo70", 6378245.0, 6356863.019)
    crs_to = ETRS89_CRS
    f_test.set_ref_systems(crs_from, crs_to)

    subFile = f_test.create_subfile("ANCPI+TNS")
    bounding_box = BoundingBox(174422.502, 156677.502, 72415.3775, 107465.3775)
    lat_inc = 35.0
    long_inc = 50.0
    subFile.set_limits(bounding_box)
    subFile.set_coord_increment(lat_inc, long_inc)
    subFile.set_dates(datetime.datetime.now())

    f_test.write_to_file(r"D:\Data\Data\ntv2",
                       "test2.txt", f_format='a',
                       overwrite=True)

