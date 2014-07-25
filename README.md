ntv2generator
=============

Python package for generating valid NTv2 binary files (usable in PROJ4) based on an external high accuracy transformation service.

Workflow:
1. Use Generator (from pointgenerator) to generate a matrix of points covering the relevant area. The relevant area is read from an external GIS data sources (in any format supported by you local installation of OGR) and needs to contain a single polygon in the EPSG:4326 projection (WGS84, Geographic projection). Due to the different ways of defining a projection in different software, the script will not always correctly detect the input projection. In such situation, you can force the generator to skip verification of the input.
Points are generated for the entire bounding box, but only the points inside the area will be further processed. Points outside the are will have no shifts.
Currently, the points are generated in the format required by TransDatRo v4.04 (the official transformation software provided by the Romanian Cadastre Agency). In case you use another transformation service that requires a different format, you have to write your own formatter.

2. Convert the points generated above using your preffered high accuracy transformation service (probably provided by you national Cadastre Agency)

3. Convert the results back to EPSG:4326 using PROJ4 tools (such as cs2cs), but manually setting parameters to remove any datum transformation. (Planned: Python script that does that for you. You'll probably still have to write your own reader, nevertheless).

4. Compute the differences between the original points and the points resulting following the succesive transformations at point 2 and 3.

5. Generate a binary NTv2 file using NTv2File (from ntv2writer). The NTv2 file can then be used in your preferred software using the PROJ4 library.

TODO:
* Automate steps 3 and 4
* Create script linking steps 3, 4 and 5, and possibly 1.


