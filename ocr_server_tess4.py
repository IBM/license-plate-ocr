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
from scipy import ndimage
import statistics
import sys
from datetime import datetime
from db2_script import Db2Connection, BColors


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
        lprs = [r for r in results if r['label'] == 'license_plate']
        plates = []
        if len(lprs) > 0:
            print(results)
            for lpr in lprs:
                plates.append(process_image(image, lpr))
        else:
            print("no license_plates found")
            # TODO, remove following line after testing
            process_image(image)


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

DEBUG = False


def process_image(image, lpr=None):
    if lpr:
        cropped_frame = image[int(lpr['ymin']): int(lpr['ymax']), int(lpr['xmin']): int(lpr['xmax'])]
    else:
        cropped_frame = image
    # detect edges in frame
    grayImage = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)
    dst = cv2.Canny(grayImage, 0, 150)
    ret, threshcanny = cv2.threshold(dst, 127, 255, 0)
    ret, thresh = cv2.threshold(grayImage, 127, 255, 0)
    ret, threshbin = cv2.threshold(grayImage, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # get contours
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    c = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(c)
    # calculate angle to rotate image
    rect = cv2.minAreaRect(c)  # rect[2] contains angle
    box = cv2.boxPoints(rect)
    # sort by y values
    y_sorted = box[np.argsort(box[:, 1]), :]
    tp_cs = np.sort(y_sorted[2:], axis=0)
    angle = np.rad2deg(np.arctan2(tp_cs[1][1] - tp_cs[0][1], tp_cs[1][0] - tp_cs[0][0]))
    # if tilted right, rotate left (counter-clockwise)
    if y_sorted[2:][0][0] > y_sorted[2:][1][0]:
        angle = - angle
    # rotate image
    # print(f"rotating by {angle} degrees")
    rotated_image = ndimage.rotate(cropped_frame, angle)
    rotated_thresh = ndimage.rotate(thresh, angle)
    contours, hierarchy = cv2.findContours(rotated_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    c = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(c)
    cropped_rotated_thresh = rotated_thresh[y:y + h, x:x + w]
    cropped_rotated_image = rotated_image[y:y + h, x:x + w]
    # cv2.drawContours(rotated_image, [c], -1, (0,255,0), 1)
    '''
    thin out border
    white out lines that are > 90% black (in case of plate that touches border).
    high mean implies row/column is mostly white.
    '''
    columns_mean = np.mean(cropped_rotated_thresh, axis=0)
    rows_mean = np.mean(cropped_rotated_thresh, axis=1)
    # whiteout rows and columns that are mostly black, assuming those are borders
    row_border_threshold = 50
    border_rows = np.where(rows_mean < row_border_threshold)
    cropped_rotated_thresh[[border_rows], :] = 255
    # whiteout rows and columns that are mostly black, assuming those are borders
    column_border_threshold = 25
    border_columns = np.where(columns_mean < column_border_threshold)
    cropped_rotated_thresh[:, [border_columns]] = 255
    contours, hierarchy = cv2.findContours(cropped_rotated_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    inverted_thresh = cv2.bitwise_not(cropped_rotated_thresh)
    dst = cv2.Canny(inverted_thresh, 50, 150)
    edge_contours, hierarchy = cv2.findContours(dst, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    areas = list(map(cv2.contourArea, edge_contours))
    boxes = list(map(cv2.boundingRect, edge_contours))
    # get index of contours that are taller than they are wide
    letters = list(filter(lambda box: ((box[2] * box[3]) > 100) and (box[2] * 3 > box[3] > box[2]), boxes))
    letters_y = [l[1] for l in letters]
    letters_h = [l[3] for l in letters]
    # y_median = statistics.median(letters_y)
    h_median = int(statistics.median(letters_h))  # + 3)
    range_threshold = (h_median / 4)  # 5
    # print(range_threshold)
    # y_median_range = range(int(y_median - range_threshold), int(y_median + range_threshold))
    h_median_range = range(int(h_median - range_threshold), int(h_median + range_threshold))
    # x, y, w, h
    # print(h_median_range)
    letters_reduced = list(filter(lambda box: box[3] in h_median_range, letters))
    # print(letters_reduced)
    # con_idx = list(map( boxes.index, letters))
    stencil = np.ones(cropped_rotated_thresh.shape, dtype=np.uint8) * 255
    # cropped_rotated_image_rgb = cv2.cvtColor(cropped_rotated_image, cv2.COLOR_BGR2RGB)
    for l in letters_reduced:
        x, y, w, h = l
        stencil[y:y + h, x:x + w] = cropped_rotated_thresh[y:y + h, x:x + w]
    # process ocr
    tess_config = "-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    text = pytesseract.image_to_string(stencil, config=tess_config, lang="License+eng")
    if len(text) > 0:
        result = {"result": text}
        db2.write_data(auth_token, text)
    else:
        result = {"result": "no text recognized"}
    print(result)
    # numpy_vertical = np.vstack((cropped_rotated_thresh, cropped_rotated_image))
    if DEBUG:
        bin_to_image = lambda img: cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        row1 = np.hstack((cropped_rotated_image, bin_to_image(cropped_rotated_thresh)))
        row2 = np.hstack((bin_to_image(dst), bin_to_image(stencil)))  # cropped_rotated_image
        stages = np.vstack((row1, row2))
        timestamp = datetime.now().strftime("%m%d_%H%M%S")
        cv2.imwrite(timestamp + '.png', stages)
    return result


def showImage(img, name='win'):
    cv2.imshow(name, img)
    cv2.waitKey(1)


def run(server_class=HTTPServer, handler_class=S, addr="0.0.0.0", port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print("starting server on port " + str(port))
    httpd.serve_forever()


# Creating a DB2 Instance
credentials = json.loads(os.environ['CREDENTIALS'])
db2 = Db2Connection(credentials)
# Authenticate with the database
auth_req = db2.authenticate()
auth_token = auth_req.json()["token"]
# Check if required tables already exists; if not - create new tables
schema_info = db2.schema_info(auth_token)
if not schema_info["Logs"]:
    db2.create_table(auth_token, db2.logs_table)
if not schema_info["Emp"]:
    db2.create_table(auth_token, db2.employee_details_table)

if len(sys.argv) > 1:
    filename = sys.argv[1]
    print(filename[0])
    image = cv2.imread(filename)
    process_image(image)
else:
    run()
