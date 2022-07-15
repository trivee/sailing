#!/usr/bin/env python3
#
# A small script to calculate distances and bearings for a multi-leg course.
#
# route.py <route.csv> <date>
#
# route.csv should contain three columns: waypoint name, latitude, longitude.
#
# This code is public domain.

# standard library
import csv, sys, datetime

# https://github.com/NOAA-ORR-ERD/lat_lon_parser
# Code for parsing lat-long coordinates in "various" formats
import lat_lon_parser

# https://github.com/dateutil/dateutil/
# dateutil - powerful extensions to datetime
import dateutil.parser

# https://github.com/pyproj4/pyproj
# Python interface to PROJ (cartographic projections and coordinate transformations library).
import pyproj

# https://github.com/space-physics/wmm2020
# WMM2020 World Magnetic Model... in simple, object-oriented Python
import wmm2020

# nautical mile in meters
NM = 1852

# input arguments
if len(sys.argv) != 3:
	print("route.py <route.csv> <date>")
	exit()

# parse route waypoints
route_points = []
with open(sys.argv[1]) as route_csv:
	reader = csv.reader(route_csv, skipinitialspace=True)
	for row in reader:
		point = {}
		point["name"] = row[0]
		point["lat"]  = lat_lon_parser.parse(row[1])
		point["lon"]  = lat_lon_parser.parse(row[2])
		route_points.append(point)

# parse the date
route_date = dateutil.parser.parse(sys.argv[2])
year = route_date.year
date_jan1 = datetime.datetime(year, 1, 1)
date_next_jan1 = datetime.datetime(year+1, 1, 1)
year_fraction = (route_date - date_jan1) / (date_next_jan1 - date_jan1)
route_year_dec = year + year_fraction

# distance calculator
geod = pyproj.Geod(ellps="WGS84")

# calculate and print the route
for leg in range(len(route_points)-1):
	start_point = route_points[leg]
	end_point   = route_points[leg+1]
	start_lat = start_point["lat"]
	start_lon = start_point["lon"]
	end_lat   = end_point["lat"]
	end_lon   = end_point["lon"]

	# notice the lon/lat input order
	# calculate the azimuths and distance
	fw_az_true, bk_az_true, dist = geod.inv(start_lon, start_lat, end_lon, end_lat)

	# correct the azimuth to be between 0 and 360
	if fw_az_true < 0.0:
		fw_az_true += 360.0

	# get magnetic declination at the starting point
	start_mag = wmm2020.wmm_point(start_lat, start_lon, 0.0, route_year_dec)
	start_decl = start_mag["decl"]

	# declination must be subtracted and corrected if needed
	fw_az_magnetic = fw_az_true - start_decl
	if fw_az_magnetic < 0.0:
		fw_az_magnetic += 360.0
	elif fw_az_magnetic >= 360.0:
		fw_az_magnetic -= 360.0

	# print the route leg information
	print(f'Leg {leg}: from {start_point["name"]} to {end_point["name"]}')
	print(f'\tStart:    {lat_lon_parser.to_str_deg_min(start_lat)} {lat_lon_parser.to_str_deg_min(start_lon)}')
	print(f'\tEnd:      {lat_lon_parser.to_str_deg_min(end_lat)} {lat_lon_parser.to_str_deg_min(end_lon)}')
	print(f'\tBearing:  {fw_az_true:.0f}° (T)  {fw_az_magnetic:.0f}° (M) ')
	print(f'\tDistance: {dist/NM:.1f} nm')

