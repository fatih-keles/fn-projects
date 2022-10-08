import io
# import json
import logging
import oci
# import uuid
import cv2
# import os
import sys, traceback
import numpy as np
import sys
import imutils

import io
# import json
import logging
import oci
# import uuid
import cv2
# import os
import sys, traceback
import numpy as np
import sys

# detected_faces = face_cascade.detectMultiScale(image=image, scaleFactor=1.3, minNeighbors=4)
# draw_found_faces(detected_faces, original_image, (0, 255, 0)) # RGB - green
def draw_found_faces(detected, image, color: tuple):
    for (x, y, width, height) in detected:
        cv2.rectangle(
            image,
            (x, y),
            (x + width, y + height),
            color,
            thickness=2
        )

def unsharp_mask(image, kernel_size=(5, 5), sigma=1.0, amount=1.0, threshold=0):
    """Return a sharpened version of the image, using an unsharp mask."""
    blurred = cv2.GaussianBlur(image, kernel_size, sigma)
    sharpened = float(amount + 1) * image - float(amount) * blurred
    sharpened = np.maximum(sharpened, np.zeros(sharpened.shape))
    sharpened = np.minimum(sharpened, 255 * np.ones(sharpened.shape))
    sharpened = sharpened.round().astype(np.uint8)
    if threshold > 0:
        low_contrast_mask = np.absolute(image - blurred) < threshold
        np.copyto(sharpened, image, where=low_contrast_mask)
    return sharpened

def edge_mask(image):
    """Return a edge masked version of the image"""
    kernel_edge = np.array([[-1, -1, -1],
                   [-1, 10,-1],
                   [-1, -1, -1]])
    edge_masked = cv2.filter2D(src=image, ddepth=-1, kernel=kernel_edge)
    return edge_masked

image_name = sys.argv[1]
image_original = cv2.imread(image_name, cv2.IMREAD_COLOR)

# img_normalized = np.zeros((image.shape[:2]))
# img_normalized = cv2.normalize(image, img_normalized, 0, 255, cv2.NORM_MINMAX)

# img_sharpened = unsharp_mask(image)
# img_edge_masked = edge_mask(image)

image_processed = image_original

image_gray = cv2.cvtColor(image_processed, cv2.COLOR_BGR2GRAY)

# Sharpen
kernel_sharpen = np.array([[0, -1, 0],
                   [-1, 5,-1],
                   [0, -1, 0]])

# face cascades 
face_cascades = [
    cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml'),
    cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_licence_plate_rus_16stages.xml'),
]
face_cascades_colors = [
    (255, 0, 0),(0, 255, 0),(0, 0, 255),(0, 0, 0),(255, 255, 255),
]

# eyes cascades 
eyes_cascades = [
    cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml'),
    cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml')
]
eyes_cascades_colors = [
    (255, 255, 255),(255, 255, 255)
]

h, w = image_original.shape[:2]
kernel_width = (w//30) | 1
kernel_height = (h//30) | 1


i=0
for face_cascade in face_cascades:
    faces = face_cascade.detectMultiScale(image_gray, scaleFactor=1.1, minNeighbors=5)
    print("{0} {1}".format(face_cascade, faces))
    for x, y, w, h in faces:
        cv2.rectangle(image_processed, (x, y), (x+w, y+h), face_cascades_colors[i], 2);
        
        face_rectangle = image_processed[y:y+h, x:x+w]
        blurred_face = cv2.GaussianBlur(face_rectangle, (kernel_width, kernel_height), 0)
        image_processed[y:y+h, x:x+w] = blurred_face
    i=i+1

# i=0
# for eyes_cascade in eyes_cascades:
#     eyes = eyes_cascade.detectMultiScale(image_gray, scaleFactor=1.1, minNeighbors=5)
#     print("{0} {1}".format(eyes_cascade, eyes))
#     for x, y, w, h in eyes:
#         cv2.rectangle(image_processed, (x, y), (x+w, y+h), eyes_cascades_colors[i], 1);
#     i=i+1

cv2.imwrite(image_name+".out.jpg",image_processed)

        # face_roi = image[y:y+h, x:x+w]
        # # print(face_roi)
        # blurred_face = cv2.GaussianBlur(face_roi, (kernel_width, kernel_height), 0)
        # # print(blurred_face)
        # image[y:y+h, x:x+w] = blurred_face

