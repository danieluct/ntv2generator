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

import string
import random

from osgeo import ogr,osr

import ntv2writer


def _id_generator(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

def _dec_to_dms(decimal):
        seconds = decimal*3600
        degrees = int(seconds/3600)
        seconds = seconds-(degrees*3600)
        minutes = int(seconds/60)
        seconds = seconds - minutes*60
        return "{0} {1} {2}".format(degrees,minutes,seconds)


class Generator:
        def __init__(self, input_dataset, verify_gcs=False):
                self.ds=ogr.Open(input_dataset)
                self.layer=self.ds.GetLayer()
                
                if self.layer is None:
                        raise Exception("Unable to open "+extent_file+" for reading!")
                        
                no_features=self.layer.GetFeatureCount()
                if no_features == 0:
                        raise Exception("No feature found in "+extent_file)
                elif no_features > 1:
                        raise Exception("More than one feature found in "+extent_file)

                self.wgs84=osr.SpatialReference()
                self.wgs84.ImportFromWkt(osr.SRS_WKT_WGS84)
                self.spatial_ref=self.layer.GetSpatialRef()
               
                if verify_gcs:
                        if not self.spatial_ref.IsSameGeogCS(wgs84):
                                raise Exception("Input must be in WGS84!")

                self.geom = None
                for feature in self.layer:
                    self.geom = feature.GetGeometryRef().Clone()
                    break
                if self.geom is None:
                        raise Exception("Unable to read geometry")
                geom_type=self.geom.GetGeometryType()
                if (geom_type is not ogr.wkbMultiPolygon and
                    geom_type is not ogr.wkbPolygon):
                        raise Exception("A polygon input is required!")

                self.increment_set=False
                self.points_generated=False

        def set_increments(self, lat_increment=30, long_increment=30, overwrite=False):
                if self.increment_set and not overwrite:
                        raise Exception("Coordinate increments have already been set!")
                if self.increment_set and overwrite:
                        self.points_generated=False
                env = self.geom.GetEnvelope()
                self.bbox = ntv2writer.BoundingBox(env[3]*3600,
                                              env[2]*3600,
                                              env[0]*3600,
                                              env[1]*3600)

                self.lat_count = int(abs(self.bbox.north - self.bbox.south)/lat_increment) + 1
                self.long_count = int(abs(self.bbox.east -  self.bbox.west)/long_increment) + 1
                self.bbox.north =  self.bbox.south +  self.lat_count * lat_increment
                self.bbox.east =  self.bbox.west +  self.long_count * long_increment
                self.lat_increment=lat_increment
                self.long_increment=long_increment
                self.increment_set=True

        def generate_points(self, overwrite=False):
                if not self.increment_set:
                        raise Exception("Increments not set!")

                temp_file=_id_generator(16)

                if self.points_generated and not overwrite:
                        raise Exception("Points have already been generated")

                if self.points_generated and overwrite:
                        self.t_layer.Dereference()
                        self.t_datasource.Destroy()

                
                driver = ogr.GetDriverByName('Memory')
                self.t_datasource = driver.CreateDataSource(temp_file)
                if self.t_datasource is None:
                        raise Exception("Cannot create in memory temp file")
                self.t_layer = self.t_datasource.CreateLayer("tmp", self.spatial_ref, ogr.wkbPoint)
                if self.t_layer is None:
                        raise Exception("Cannot create temp layer")

                field = ogr.FieldDefn('pointName',ogr.OFTString)
                field.SetWidth(20)
                if self.t_layer.CreateField(field) !=0:
                        raise Exception("Failed to add field to memory temp file")
                field.Destroy()

                p_idx=0
                for x in [self.bbox.south + i*self.lat_increment
                          for i in range(self.lat_count+1)]:
                        for y in [self.bbox.east - j*self.long_increment
                                   for j in range(self.long_count+1)]:
                                point = ogr.Geometry(ogr.wkbPoint)
                                point.AddPoint(y/3600., x/3600.)
                                #print x/3600., y/3600.
                                inRow = ogr.Feature(self.t_layer.GetLayerDefn())
                                inRow.SetField('pointName', 'P' + str(p_idx))
                                inRow.SetGeometryDirectly(point)
                                self.t_layer.CreateFeature(inRow)
                                inRow.Destroy()
                                p_idx = p_idx + 1
                                
                self.points_generated=True

        def select_valid_points(self):
                if not self.increment_set:
                        raise Exception("Increments not set!")
                
                self.t_layer.ResetReading()
                self.t_layer.SetSpatialFilter(self.geom)

        def dump_to_file(self, file_path, country='RO'):                
                if not self.points_generated:
                        self.generate_points()
                
                self.select_valid_points()
                if country == 'RO':
                        csv=open(file_path,"w")
                        csv.write("\n")
                        for feature in self.t_layer:
                            csv.write(feature.GetField('pointName')+","+
                                      _dec_to_dms(feature.GetGeometryRef().GetY())+","+
                                      _dec_to_dms(feature.GetGeometryRef().GetX())+"\n")
                        csv.close()
                else:
                        raise Exception("Unknow ouput format")
                
        def cleanup(self):
                self.layer.Dereference()
                self.ds.Release()
                if self.points_generated:
                        self.t_layer.Dereference()
                        self.t_datasource.Destroy()
                del self
                
                
def _test():
        gnr=Generator(r"D:\Data\Data\ntv2\ntv2generator\test_ro.shp")
        gnr.set_increments(30,30)
        gnr.dump_to_file(r"D:\Data\Data\ntv2\ntv2generator\test_ro.txt")
