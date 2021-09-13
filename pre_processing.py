import cv2
import numpy
import math
from pdf2image import convert_from_path as conversion
import os
import pikepdf
from joblib import load



def clip_pdf(pdf_path):

    pdf = pikepdf.open(pdf_path, "rb", allow_overwriting_input=True)
    length = len(pdf.pages)

    upper = load('ML_models/upper_bound.joblib')
    lower = load('ML_models/lower_bound.joblib')

    upper_bound = upper.predict(numpy.array([length]).reshape(1, -1))[0]
    lower_bound = lower.predict(numpy.array([length]).reshape(1, -1))[0]

    upper_bound = int(upper_bound)
    lower_bound = int(lower_bound)

    del pdf.pages[upper_bound + 1:]
    del pdf.pages[:lower_bound]

    pdf.save(pdf_path)

def detect_skew(greyscale_img):


    non_absolute_black_coordinates = numpy.column_stack(numpy.where(greyscale_img > 0))
    skew_angle = cv2.minAreaRect(non_absolute_black_coordinates)[-1]

    if skew_angle == 90:
        return 0
    if skew_angle < -45:
        return -(90+skew_angle)
 
    return -skew_angle

def deal_with_skew(skew_angle, greyscale_img):


    height, width = greyscale_img.shape
    img_center = (width / 2, height / 2)

    rotationMatrix = cv2.getRotationMatrix2D(img_center, skew_angle, 1.0)
    rotated_img = cv2.warpAffine(greyscale_img,
                                rotationMatrix,
                                (width, height),
                                borderMode = cv2.BORDER_REFLECT)
    
    return rotated_img


def pdf_to_png(filepath):

    # clip-pdf if required 
    clip_pdf(filepath)

    # some font sizes are small on balance sheets e.g (font_size < 8) and so it is recommended in this case
    # to increase DPI to 400-600. The claimed accuracy benefits are not present in this application, as noted
    # from confidence ratings on OCR output. To maintain speed DPI is kept at 300 
    pages = conversion(filepath, 400)
    image_counter = 1

    filepath = filepath.strip(".pdf")

    for page in pages:
        page.save(f"{filepath}-{image_counter}.png", 'PNG')
        image_counter += 1
    

def pre_process(png_filepath):
        
    png_files = []
    png_header_files = []

    print(png_filepath)
    i = 1
    while os.path.isfile(f"{png_filepath}-{i}.png"):
        png_files.append(f"{png_filepath}-{i}.png")
        png_header_files.append(f"{png_filepath}-{i}-header.png")
        i += 1

    
    i = 1
    for png_file in png_files:
        
        # read in the png image with the greyscale flag on 
        img = cv2.imread(png_file, cv2.IMREAD_GRAYSCALE)

        page_height = img.shape[0]

        # find header and margin sizes
        top_quarter = round(0.25 * page_height)

        # not normally an issue with companies house but, I have included skew correction in case
        skew_angle = detect_skew(img)
        if skew_angle != 0:
            img = deal_with_skew(skew_angle, img)
        
        #Some have staple and puncture markes on page border - this solves for this issue
        # with very low risk of losing information 
        # [top: bottom, left: right]
        crop_img = img[200: top_quarter, 100:-100]


        # OTSU Binarizastion and inverting the image for morphological transformations 
        threshold, binary = cv2.threshold(crop_img,0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

        #opening (erosions followed by dilation) gets rid of white noise and restores text boundaries
        opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, numpy.ones((2,2), numpy.uint8))

        dilation = cv2.dilate(opening ,numpy.ones((1,1), numpy.uint8) ,iterations = 1)
        
        # Undo inversion 
        transformed_image = cv2.bitwise_not(dilation)
        
        # over-write
        cv2.imwrite(png_file.strip(".png") + "-header.png", transformed_image)

    return png_header_files