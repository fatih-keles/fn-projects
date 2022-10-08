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
image_original = cv2.flip(image_original, 1)

# # img_normalized = np.zeros((image.shape[:2]))
# # img_normalized = cv2.normalize(image, img_normalized, 0, 255, cv2.NORM_MINMAX)

# # img_sharpened = unsharp_mask(image)
# # img_edge_masked = edge_mask(image)

image_processed = image_original

image_gray = cv2.cvtColor(image_processed, cv2.COLOR_BGR2GRAY)

# # Sharpen
# kernel_sharpen = np.array([[0, -1, 0],
#                    [-1, 5,-1],
#                    [0, -1, 0]])

# # face cascades 
face_cascades = [
    cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'),
    cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt.xml'),
    cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml'),
    cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt_tree.xml'),
    cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml'),
    cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml'),
    cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_licence_plate_rus_16stages.xml'),
    # cv2.CascadeClassifier(cv2.data.lbpcascades + 'lbpcascade_frontalface.xml'),
    # cv2.CascadeClassifier(cv2.data.lbpcascades + 'lbpcascade_frontalface_improved.xml'),
    # cv2.CascadeClassifier(cv2.data.lbpcascades + 'lbpcascade_profileface.xml'),
]
face_cascades_colors = [
    (255, 0, 0),(0, 255, 0),(0, 0, 255),(0, 0, 0),(255, 255, 255),(255, 255, 0),(255, 0, 255),(0, 255, 255)
]

# # eyes cascades 
# eyes_cascades = [
#     cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml'),
#     cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml')
# ]
# eyes_cascades_colors = [
#     (255, 255, 255),(255, 255, 255)
# ]

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

# # i=0
# # for eyes_cascade in eyes_cascades:
# #     eyes = eyes_cascade.detectMultiScale(image_gray, scaleFactor=1.1, minNeighbors=5)
# #     print("{0} {1}".format(eyes_cascade, eyes))
# #     for x, y, w, h in eyes:
# #         cv2.rectangle(image_processed, (x, y), (x+w, y+h), eyes_cascades_colors[i], 1);
# #     i=i+1

cv2.imwrite(image_name+".out.jpg",image_processed)

#         # face_roi = image[y:y+h, x:x+w]
#         # # print(face_roi)
#         # blurred_face = cv2.GaussianBlur(face_roi, (kernel_width, kernel_height), 0)
#         # # print(blurred_face)
#         # image[y:y+h, x:x+w] = blurred_face

# fname = sys.argv[1] #'sample-images/_license_plates/amsterdam-1.png'
# img = cv2.imread(fname)
# img2 = np.zeros((img.shape[:2]))
# gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# cv2.line_descriptor_LSDDetector.createLSDDetector()
# lsd = cv2.line_descriptor_LSDDetector.createLSDDetector()

# ## draw lines 
# matrice = np.zeros((0,0))
# lines = lsd.detect(gray, 2, 1)
# for kl in lines:
#     if kl.octave == 0:
#         # cv.line only accepts integer coordinate
#         pt1 = (int(kl.startPointX), int(kl.startPointY))
#         pt2 = (int(kl.endPointX), int(kl.endPointY))
#         print(pt1 + pt2)
#         matrice.append(pt1 + pt2)
#         cv2.line(img2, pt1, pt2, [255, 0, 0], 2)

# cv2.imwrite(fname+".out.jpg",img2)
# print(matrice)
# img2 = cv2.imread(fname+".out.jpg")

# # find
# gray = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY)
# # edged = cv2.Canny(img, 170, 490)
# blurred = cv2.GaussianBlur(gray, (5, 5), 0)
# thresh = cv2.adaptiveThreshold(blurred, 255, 1, 1, 11, 2)
# thresh_color = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
# thresh = cv2.dilate(thresh,None,iterations = 15)
# thresh = cv2.erode(thresh,None,iterations = 15)

# # Find the contours
# contours,hierarchy = cv2.findContours(thresh,
#                                       cv2.RETR_TREE,
#                                       cv2.CHAIN_APPROX_SIMPLE)
# for cnt in contours:
#         x,y,w,h = cv2.boundingRect(cnt)
#         cv2.rectangle(img,
#                       (x,y),(x+w,y+h),
#                       (0,255,0),
#                       2)
# # thresh_img = cv2.threshold(image_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
# # cnts = cv2.findContours(thresh_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
# # cnts = cnts[0] if len(cnts) == 2 else cnts[1]
# # for cnt in cnts:
# #     approx = cv2.contourArea(cnt)
# #     print(approx)

# cv2.imwrite(fname+".out.jpg",img2)
# cv2.imwrite(fname+".out2.jpg",img)


