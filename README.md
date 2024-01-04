# pygcdl

Python interface for the Geospatial Common Data Library.

To run the script client_example.py, you must first unzip the sample datafiles, ie:

$ unzip sample_data/subset_counties*.zip

Each of the sample files contains a collection of polygons representing the boundaries of counties in California. The geometries have the following properties:

1: five counties, each a single polygons, union < 80% of convex hull
2: five counties, all adjacent, single polygons
3: nineteen counties, one disjoint from the rest, union > 80% of convex hull, single polygons
4: one county that includes islands, multipolygon
5: five counties, adjacent, one single multipolygon
6: single polygon
7: two adjacent polygons, union < 80% of convex hull
8: five counties, adjacent, split into two multipolygons, one multipolygon has two polygons that are not touching
