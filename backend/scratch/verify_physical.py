import math

# Building dimensions
width_m = 42.0
height_m = 24.0
corridor_y = 12.0 # Central corridor at Y=12m

print("=" * 80)
print("TRUE PHYSICAL GEOMETRY ANALYSIS (42.0m x 24.0m Building)")
print("=" * 80)

# True physical coordinates of rooms on Typical Floor:
# Building has 2 exit stairs:
# Exit S-01 (West): Door at X=3.0m, Y=12.0m
# Exit S-02 (East): Door at X=39.0m, Y=12.0m

# In DXF (generate_dubai_dxfs.py):
# North offices (Y from 14.0m to 23.5m):
#   OPEN OFFICE NORTH: X from 3.0m to 23.0m, Centroid = (13.0m, 18.75m), Door at (13.0m, 14.0m)
#     Internal path to door: 18.75 - 14.0 = 4.75m
#     Door to corridor: 14.0 - 12.0 = 2.0m
#     Corridor to Exit S-01 (West at X=3.0m): 13.0 - 3.0 = 10.0m
#     True Total Travel Distance = 4.75 + 2.0 + 10.0 = 16.75m!
#
#   OPEN OFFICE EAST: X from 23.0m to 39.0m, Centroid = (31.0m, 18.75m), Door at (31.0m, 14.0m)
#     Internal path to door: 18.75 - 14.0 = 4.75m
#     Door to corridor: 14.0 - 12.0 = 2.0m
#     Corridor to Exit S-02 (East at X=39.0m): 39.0 - 31.0 = 8.0m
#     True Total Travel Distance = 4.75 + 2.0 + 8.0 = 14.75m!

# South meeting rooms (Y from 0.5m to 10.0m):
#   MEETING ROOM 1A: X from 3.0m to 10.0m, Centroid = (6.5m, 5.25m), Door at (6.5m, 10.0m)
#     Internal path: 10.0 - 5.25 = 4.75m
#     Door to corridor: 12.0 - 10.0 = 2.0m
#     Corridor to Exit S-01: 6.5 - 3.0 = 3.5m
#     True Total Travel Distance = 4.75 + 2.0 + 3.5 = 10.25m!
#
#   MEETING ROOM 1D (Eastmost South): X from 31.0m to 39.0m, Centroid = (35.0m, 5.25m)
#     Internal path: 4.75m
#     Door to corridor: 2.0m
#     Corridor to Exit S-02: 39.0 - 35.0 = 4.0m
#     True Total Travel Distance = 4.75 + 2.0 + 4.0 = 10.75m!

# In PDF layout (where normalized coordinates represent % of the sheet):
# PDF percentage coordinates mapped to physical meters:
# OPEN OFFICE EAST: centroid = (71.56%, 59.75%)
# Physical centroid X = 0.7156 * 42.0 = 30.05m
# Physical centroid Y = 0.5975 * 24.0 = 14.34m
# Exit S-02 at (79.41% * 42.0, 42.1% * 24.0) = (33.35m, 10.10m)
# Physical distance from (30.05, 14.34) to Exit S-02 (33.35, 10.10):
#   = dx + dy along corridor = (33.35 - 30.05) + (14.34 - 12.0) + (12.0 - 10.10) = 3.3m + 2.34m + 1.9m ≈ 7.54m!
# (Or if escaping to West Exit S-01 at 0.2339 * 42 = 9.82m):
#   = (30.05 - 9.82) + 2.34m + 1.9m ≈ 24.47m!

print("Calculations complete.")
