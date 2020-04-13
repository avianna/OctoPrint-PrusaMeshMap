# coding=utf-8

# We work with coordinates relative to the dashed line on the
# skilkscreen on the MK52 heatbed: print area coordinates. Note
# this doesn't exactly line up with the steel sheet, so we have to
# adjust for that when generating the background image, below.
# Points are measured from the middle of the PINDA / middle of the
# 4 probe circles on the MK52.

MESH_NUM_POINTS_X = 7
MESH_NUM_MEASURED_POINTS_X = 3
MESH_NUM_POINTS_Y = 7
MESH_NUM_MEASURED_POINTS_Y = 3
BED_SIZE_X = 250
BED_SIZE_Y = 210

# These values come from mesh_bed_calibration.cpp
BED_PRINT_ZERO_REF_X = 2
BED_PRINT_ZERO_REF_Y = 9.4

# Mesh probe points, in print area coordinates
# We assume points are symmetrical (i.e a rectangular grid)
MESH_FRONT_LEFT_X = 37 - BED_PRINT_ZERO_REF_X
MESH_FRONT_LEFT_Y = 18.4 - BED_PRINT_ZERO_REF_Y

MESH_REAR_RIGHT_X = 245 - BED_PRINT_ZERO_REF_X
MESH_REAR_RIGHT_Y = 210.4 - BED_PRINT_ZERO_REF_Y

# Offset of the marked print area on the steel sheet relative to
# the marked print area on the MK52. The steel sheet has margins
# outside of the print area, so we need to account for that too.

SHEET_OFFS_X = -11
# Technically SHEET_OFFS_Y is -2 (sheet is BELOW (frontward to) that on the MK52)
# However, we want to show the user a view that looks lined up with the MK52, so we
# ignore this and set the value to zero.
SHEET_OFFS_Y = 0
SHEET_MARGIN_LEFT = 0
SHEET_MARGIN_RIGHT = 0

# The SVG of the steel sheet (up on Github) is not symmetric as the actual one is
SHEET_MARGIN_FRONT = 17
SHEET_MARGIN_BACK = 14

sheet_left_x = -(SHEET_MARGIN_LEFT + SHEET_OFFS_X)
sheet_right_x = sheet_left_x + BED_SIZE_X + SHEET_MARGIN_LEFT + SHEET_MARGIN_RIGHT
sheet_front_y = -(SHEET_MARGIN_FRONT + SHEET_OFFS_Y)
sheet_back_y = sheet_front_y + BED_SIZE_Y + SHEET_MARGIN_FRONT + SHEET_MARGIN_BACK

mesh_range_x = MESH_REAR_RIGHT_X - MESH_FRONT_LEFT_X
mesh_range_y = MESH_REAR_RIGHT_Y - MESH_FRONT_LEFT_Y

mesh_delta_x = mesh_range_x / (MESH_NUM_POINTS_X - 1)
mesh_delta_y = mesh_range_y / (MESH_NUM_POINTS_Y - 1)
