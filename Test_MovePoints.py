import arcpy

def main():
    wkg_data = r'U:\grue\Scripts\Testing_or_Developing\TestMovePoint\movePoint.gdb\points_to_move'
    move_point(wkg_data, 20, 0)



def move_point(wkg_data, x_shift=None, y_shift=None):

    with arcpy.da.UpdateCursor(wkg_data, 'Shape@XY') as cursor:
        for row in cursor:
            cursor.updateRow([[row[0][0] + (x_shift or 0),
                               row[0][1] + (y_shift or 0)]])



    ([[row[0][0], row[0][1]]])


if __name__ == '__main__':
    main()
