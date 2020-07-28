#!/usr/local/bin/python3
from http.server import HTTPServer, BaseHTTPRequestHandler
from PIL import Image
import pytesseract
import cv2
import os
import argparse
import json
import http
import numpy as np
from  scipy import ndimage
import statistics
import sys
from datetime import datetime
import statistics
from pytesseract import Output
# import process_image

class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        self.send_response(200, 'OK')
        self.end_headers()

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        if 'content-length' in self.headers:
            # length = int(self.headers.get('content-length'))
            length = int(self.headers['Content-Length'])
            print("length: " + str(length))
            field_data = self.rfile.read(length).decode("utf-8")
            self.send_response(200, "OK")
            self.end_headers()
            data = json.loads(field_data)
        else:
            self.send_response(204, "OK")
            self.end_headers()
        results = data['results']
        image = np.array(data['image']).astype('uint8')
        # cv2.imwrite("image.png", image)
        timestamp = datetime.now().strftime("%m%d_%H%M%S")
        cv2.imwrite(timestamp + '.png', image)
        f = open('results_' + timestamp + '.txt', 'w+')
        f.write(str(results))
        f.close()
        lprs = [r for r in results if r['label'] == 'license_plate']
        plates = []
        if len(lprs) > 0:
            print(results)
            for lpr in lprs:
                plates.append(process_image(image, lpr))
            print(plates)
        else:
            print("no license_plates found")
            # TODO, remove following line after testing
            process_image(image)


# sample_res = [{'confidence': 0.9999319314956665, 'ymax': 638, 'label': 'license_plate', 'xmax': 635, 'xmin': 373, 'ymin': 588, 'polygons': [[[406, 586], [387, 590], [378, 588], [368, 590], [368, 607], [387, 610], [378, 612], [387, 614], [378, 616], [387, 618], [368, 621], [368, 636], [387, 640], [602, 640], [621, 636], [621, 623], [630, 621], [621, 619], [630, 618], [621, 616], [621, 596], [630, 594], [602, 588], [593, 590], [584, 588], [574, 590], [565, 588], [556, 590], [509, 590], [499, 592], [490, 592], [481, 590], [462, 590], [443, 586]]]}, {'confidence': 0.9998823404312134, 'ymax': 795, 'label': 'car', 'xmax': 943, 'xmin': 61, 'ymin': 276, 'polygons': [[[170, 267], [107, 304], [107, 471], [44, 508], [44, 526], [107, 563], [107, 693], [44, 730], [170, 804], [864, 804], [927, 767], [896, 749], [927, 730], [896, 712], [959, 675], [959, 600], [896, 563], [896, 378], [864, 359], [864, 304], [801, 267]]]}]


# TODO, add method to take average of
# def update_best
# plates_observed = {
#     "": {
#         plate_number: ""
#         observations: {
#             predicted_text: ""
#             time: ""
#         }
#     }
# }


DEBUG=False
WINDOW_NAME='win'

def showImage(img):
    WINDOW_NAME='win'
    cv2.imshow(WINDOW_NAME, img)
    cv2.waitKey(1)

ocr_results = []

def detect_tilt(dst):
    # get largest contour, use top two points as reference for rotation
    # pass canny
    edge_contours, hierarchy = cv2.findContours(dst, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    recs = []
    areas = {}
    max_area = 0
    for con in edge_contours:
        x,y,w,h = cv2.boundingRect(con)
        if (w > (1.7 * h)) :
            area = w * h
            if area > max_area:
                max_area = area
                c = con
    x, y, w, h = cv2.boundingRect(c)
    # calculate angle to rotate image
    rect = cv2.minAreaRect(c) # rect[2] contains angle
    box = cv2.boxPoints(rect)
    # sort by y values
    y_sorted = box[np.argsort(box[:, 1]), :]
    tp_cs = np.sort(y_sorted[2:], axis=0)
    angle = np.rad2deg(np.arctan2(tp_cs[1][1] - tp_cs[0][1], tp_cs[1][0] - tp_cs[0][0]))
    # if tilted right, rotate left (counter-clockwise)
    if y_sorted[2:][0][0] > y_sorted[2:][1][0]:
        angle = - angle
    # rotate image
    return (angle, c)
    # print(f"rotating by {angle} degrees")


def trim_border(image):
    '''
    thin out border
    white out lines that are > 90% black (in case of plate that touches border).
    high mean implies row/column is mostly white.
    '''
    np.seterr(divide='ignore', invalid='ignore')
    columns_mean = np.mean(image, axis = 0)
    rows_mean = np.mean(image, axis = 1)
    # whiteout rows and columns that are mostly black, assuming those are borders
    row_border_threshold = 10
    column_border_threshold = 25
    border_rows = np.where(rows_mean < row_border_threshold )
    border_columns = np.where(columns_mean < column_border_threshold )
    # whiteout rows and columns that are mostly black, assuming those are borders
    image[[border_rows], :] = 255
    image[:, [border_columns]] = 255
    return image

def draw_contour_color(image, contours):
    # rotated_image_copy = rotated_image.copy()
    # cropped_rotated_image_copy = cropped_rotated_image.copy()
    temp = image.copy()
    for con in contours:
        # color = (np.random.choice(range(256), size=3))
        color = (np.random.randint(0,255), np.random.randint(0,255), np.random.randint(0,255))
        rect = cv2.minAreaRect(con)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        cv2.drawContours(temp, [box], -1, color, 2)
    showImage(temp)
    return temp

def select_letter_contours(contours, horizon):
    middle_contours = []
    # going to
    threshold = 5
    for con in contours:
        intersections = len(set(range(horizon - threshold, horizon + threshold)).intersection(con.take(1,2).flatten()))
        if intersections > 0:
            middle_contours.append(con)
    # TODO, also remove contours under avg w/h using standard deviation and mean
    return middle_contours

def process_image(image, lpr=None):
    if lpr:
        cropped_frame = image.copy()[ int(lpr['ymin']) : int(lpr['ymax']), int(lpr['xmin']): int(lpr['xmax'])]
    else:
        cropped_frame = image.copy()
    cropped_frame = cv2.resize(cropped_frame.copy(), (cropped_frame.shape[1] * 5, cropped_frame.shape[0] * 5 ) )
    grayImage = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)
    dst_rbg = cv2.Canny(cropped_frame, 50, 200)
    ret, thresh = cv2.threshold(grayImage, 127, 255, 0)
    ret, threshbin = cv2.threshold(grayImage,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    # get edges of threshold
    dst = cv2.Canny(thresh, 50, 200)

    # testing
    # upped_gray = cv2.resize(grayImage, (grayImage.shape[1] * 5, grayImage.shape[0] * 5 ) )
    # ret, upped_thresh = cv2.threshold(upped_gray, 127, 255, 0)
    # dst_upped = cv2.Canny(upped_thresh, 25, 150)
    # testing

    ret, threshcanny = cv2.threshold(dst, 127, 255, 0)
    # k_size = 1
    # kernel = np.ones((k_size,k_size),np.uint8)
    # closed_dst = cv2.morphologyEx(dst, cv2.MORPH_CLOSE, kernel)
    # ret, threshcanny = cv2.threshold(closed_dst, 127, 255, 0)

    # find edges of threshold image
    # ret, threshcanny = cv2.threshold(dst, 127, 255, 0)

    # get angle of image
    angle, c = detect_tilt(threshcanny)

    # draw largest contour on image, assuming contour is plate (TODO, limit to closed contour)
    rotated_original_image = ndimage.rotate(cropped_frame.copy(), angle, cval=255)
    cv2.drawContours(cropped_frame, [c], -1, (0,255,0), 1)

    # rotate image
    rotated_image = ndimage.rotate(cropped_frame, angle, cval=255)
    rotated_thresh = ndimage.rotate(thresh.copy(), angle, cval=255)

    # get updated indices of contour location in rotated image
    indices = np.where(np.all(rotated_image == (0,255,0), axis=-1))
    max_y = max(indices[0])
    min_y = min(indices[0])
    max_x = max(indices[1])
    min_x = min(indices[1])
    w = max_x - min_x
    h = max_y - min_y
    x = min_x
    y = min_y

    # crop image (TODO, occassionally largest contour only contains partial plate)
    h_padding = 3
    w_padding = 2
    cropped_rotated_thresh = rotated_thresh.copy()[y:y+h, x:x+w]
    cropped_rotated_image = rotated_original_image.copy()[y:y+h, x:x+w]
    grayImage = cv2.cvtColor(cropped_rotated_image, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(grayImage, 127, 255, 0)

    # upsize cropped image. should mainly upsize if we want to use morphology to seperate blobs (dilate/erode)
    # also want to upsize in hopes that edges will be closed

    reduced_thresh = trim_border(thresh)
    dst = cv2.Canny(cv2.bitwise_not(reduced_thresh), 50, 150)

    '''
    remove remaining border sections
    '''
    # get horizontal lines in the bottom quarter, primarily for letters that are connected by a border
    # kernel = np.ones((1, 3), np.uint8)
    # lines = cv2.morphologyEx( bottom[:,], cv2.MORPH_OPEN, kernel, iterations=5)
    # contours, hierarchy = cv2.findContours(lines, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # cv2.drawContours(reduced_thresh[height - int(height/5):-1, :], contours, -1, (255,255,255), thickness=10)
    # filter to bottom quarter
    height = dst.shape[0]
    bottom = dst[height - int(height/5):-1, :]

    # open bottom edges horizontally (if they exist)
    if np.sum(bottom) > 0:
        kernel = np.ones((3,1),np.uint8)
        opened = cv2.morphologyEx(bottom, cv2.MORPH_OPEN, kernel)
        opened_dst = cv2.Canny(opened, 50, 150)
        dst[height - int(height/5):-1, :] = opened_dst

    # dst = cv2.Canny(reduced_thresh, 50, 150)
    contours_upped, hierarchy = cv2.findContours(dst, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    '''
    determine which contours contain letters based off approximate area
    and filter down to contours that intersect the center horizontal point
    '''
    horizon = int( reduced_thresh.shape[0] / 2)
    reduced_contours = select_letter_contours(contours_upped, horizon)
    # stencil = np.ones((upped_thresh.shape), dtype=np.uint8)*255
    stencil = np.ones( ( int(reduced_thresh.shape[0] * 1.25), int(reduced_thresh.shape[1] * 1.25))  , dtype=np.uint8)*255

    for con in reduced_contours:
        box = cv2.boundingRect(con)
        x, y, w, h = box
        stencil[y:y+h, x:x+w] = reduced_thresh[y:y+h, x:x+w]

    if os.environ.get('DEBUG'):
        bin_to_image = lambda img: cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        row1 = np.hstack(( thresh, dst ))
        row2 = np.hstack(( reduced_thresh, dst ))

        row_seperator = np.ones( (1, thresh.shape[1] * 2) , dtype=np.uint8)*127
        # row2 = np.hstack(( bin_to_image(dst), bin_to_image(stencil) )) # cropped_rotated_image

        # row3 = np.hstack( bin_to_image(stencil), np.ones((cropped_rotated_image.shape[0], stencil.shape[1] - cropped_rotated_image.shape[1])))
        stages = np.vstack((row1, row_seperator))
        stages = np.vstack((stages, row2))
        # stages = row1
        final = bin_to_image(stencil)
        # stages = bin_to_image(row1)
        timestamp = datetime.now().strftime("%m%d_%H%M%S")
        cv2.imwrite(timestamp + '_stages.png', stages)
        cv2.imwrite(timestamp + '_final.png', final)
        # cv2.imwrite(timestamp + '_lines.png', lines)

    # whitelists only work with legacy, --oem 0
    tess_config = "-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 --psm 6"
    text = pytesseract.image_to_string(stencil, config=tess_config, lang="eng")
    print(text)
    return text

def showImage(img, name='win'):
    cv2.imshow(name, img)
    cv2.waitKey(1)

def run(server_class=HTTPServer, handler_class=S, addr="0.0.0.0", port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print("starting server on port " + str(port))
    httpd.serve_forever()


if len(sys.argv) == 2:
    image_filename = sys.argv[1]
    image = cv2.imread(image_filename)
    process_image(image)
elif (len(sys.argv) == 3):
    image_filename = sys.argv[1]
    results_path = sys.argv[2]
    results = eval(open(results_path).read())
    lprs = [r for r in results if r['label'] == 'license_plate']
    image = cv2.imread(image_filename)
    process_image(image, lprs[0])
else:
    run()
