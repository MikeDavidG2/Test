#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mgrue
#
# Created:     25/01/2017
# Copyright:   (c) mgrue 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from PIL import Image
import os

def main():
    orig_jpg_path = r'U:\grue\Scripts\GitHub\DPW-Sci-Monitoring\Data\Sci_Monitoring_pics'
    prod_jpg_path = r'U:\grue\Scripts\GitHub\DPW-Sci-Monitoring\Data\Sci_Monitoring_pics_rotated'

    Rotate_Images(orig_jpg_path, prod_jpg_path)
    ##Rotate_Images1(orig_jpg_path, prod_jpg_path)

def Rotate_Images(orig_jpg_path, prod_jpg_path):
    img_filename = '%s/PEN-009__3_A.jpg' % orig_jpg_path
    img_obj = Image.open(img_filename)
    img_obj.open(img_filename)
    im.show()





def Rotate_Images1(orig_jpg_path, prod_jpg_path):
    print os.curdir
    images = os.listdir(orig_jpg_path)
    os.chdir(orig_jpg_path)
    print os.curdir
    for image in images:
        if image.endswith('.jpg'):
            print 'Image: ' + image
            img_path = orig_jpg_path + '\\' + image
            print 'image Path: ' + img_path

            im = Image.open(image)

            im.rotate(90).show()

if __name__ == '__main__':
    main()
