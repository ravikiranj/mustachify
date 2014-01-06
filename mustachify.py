#!/usr/bin/python

import cv
import errno
import getopt
import math
import os
import sys
from PIL import Image

########################################################################
#                           CONFIG VARIABLES                           #
########################################################################

# 0 = top of head, 1 = chin
MUSTACHE_VERTICAL_POSITION_RATIO = 0.71

# Vertical offset - use for fine adjustments
# 0 = no adjust, 1 = move up 1 nose height
MUSTACHE_VERTICAL_POSITION_FINE_OFFSET = 0.08

# 0 = point, 1 = width of face
MUSTACHE_TO_FACE_SIZE_RATIO = 0.6

DEFAULT_MUSTACHE_WIDTH = 50

DEFAULT_MUSTACHE_IMAGE_FILE = "mustache_03.png"

########################################################################
#                         END CONFIG VARIABLES                         #
########################################################################


# XML Haar cascade file paths
EYES = "cascades/haarcascade_eye.xml"
NOSE = "cascades/haarcascade_mcs_nose.xml"
FACE = "cascades/haarcascade_frontalface_default.xml"

DEBUG_MODE = False


def usage():
    print """mustachify.py [-i input file] [-o output file] [options]

Options:
    -h, --help                Display usage information
    -i, --inputfile           Input image file
    -o, --outputfile          Output image file
    -m, --mustache            Mustache image file
    -d, --debug               Print debugging information and overlay debugg
ing rectangles on image"""


def detect_features(image, cascade, minsize):
    features = []
    storage = cv.CreateMemStorage()
    loaded_cascade = cv.Load(cascade)

    detected = cv.HaarDetectObjects(image, loaded_cascade, storage, 1.2, 2,
                                    cv.CV_HAAR_DO_CANNY_PRUNING, minsize)
    if DEBUG_MODE:
        print "\t\tFound: " + str(detected)
    if detected:
        for (x, y, w, h), n in detected:
            features.append((x, y, w, h))
    return features


def draw_rectangle(image, (x, y, w, h), color):
    cv.Rectangle(image, (x, y), (x+w, y+h), color)


def main(argv=None):
    # Process arguments
    if argv is None:
        argv = sys.argv

    input_file = ""
    output_file = ""
    mustache_file = DEFAULT_MUSTACHE_IMAGE_FILE
    DEBUG_MODE = False

    try:
        opts, args = getopt.getopt(argv[1:], "hi:o:m:d", ["help", "inputfile=", "outputfile=", "mustache=", "debug"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-i", "--inputfile"):
            input_file = arg
            try:
                with open(input_file):
                    pass
            except IOError:
                print "Error: File " + input_file + " does not exist."
                sys.exit(errno.ENOENT)
        elif opt in ("-o", "--outputfile"):
            output_file = arg
        elif opt in ("-m", "--mustache"):
            mustache_file = arg
            try:
                with open(mustache_file):
                    pass
            except IOError:
                print "Error: File " + mustache_file + " does not exist."
                sys.exit(errno.ENOENT)
        elif opt in ("-d", "--debug"):
            DEBUG_MODE = True
        else:
            usage()
            sys.exit()

    if input_file == "" or output_file == "":
        print "Error: Specify an input and output file."
        usage()

    # End argument processing

    if DEBUG_MODE:
        print "Processing " + input_file

    pil_image = Image.open(input_file)
    cv_image = cv.CreateImageHeader(pil_image.size, cv.IPL_DEPTH_8U, 3)
    cv.SetData(cv_image, pil_image.tostring())

    mustache = Image.open(os.path.join("mustaches", mustache_file))

    # calculate mustache image aspect ratio so proportions are preserved
    # when scaling it to face
    mustache_aspect_ratio = 1.0*mustache.size[0]/mustache.size[1]

    if DEBUG_MODE:
        print "\tFinding eyes:"
    eyes = detect_features(cv_image, EYES, (10, 10))
    if DEBUG_MODE:
        print "\tFinding nose:"
    noses = detect_features(cv_image, NOSE, (10, 10))
    if DEBUG_MODE:
        print "\tFinding face:"
    faces = detect_features(cv_image, FACE, (70, 70))

    if DEBUG_MODE:
        print "\tFound " + str(len(eyes)) + " eye(s), " + str(len(noses)) + \
              " nose(s), and " + str(len(faces)) + " face(s)."

    # mustache_x and mustache_y represent the top left the mustache
    mustache_w = mustache_h = mustache_x = mustache_y = mustache_angle = 0

    if len(eyes) == 2:
        #order eyes from left to right
        if eyes[0][0] > eyes[1][0]:
            temp = eyes[1]
            eyes[1] = eyes[0]
            eyes[0] = temp

        eye_L_x = eyes[0][0]
        eye_L_y = eyes[0][1]
        eye_L_w = eyes[0][2]
        eye_L_h = eyes[0][3]
        eye_R_x = eyes[1][0]
        eye_R_y = eyes[1][1]
        eye_R_w = eyes[1][2]
        eye_R_h = eyes[1][3]

        # Redefine x and y coordinates as center of eye
        eye_L_x = int(1.0 * eye_L_x + (eye_L_w / 2))
        eye_L_y = int(1.0 * eye_L_y + (eye_L_h / 2))
        eye_R_x = int(1.0 * eye_R_x + (eye_R_w / 2))
        eye_R_y = int(1.0 * eye_R_y + (eye_R_h / 2))

        mustache_angle = math.degrees(math.atan(-1.0 *
                                      (eye_R_y-eye_L_y)/(eye_R_x-eye_L_x)))

        # Don't rotate mustache if it looks like one of the eyes
        # was misplaced
        if math.fabs(mustache_angle) > 25:
            mustache_angle = 0

        if DEBUG_MODE:
                draw_rectangle(cv_image, eyes[0], (0, 255, 0))
                draw_rectangle(cv_image, eyes[1], (0, 255, 0))
                print "\tMustache angle = " + str(mustache_angle)
    else:
        mustache_angle = 0
        print "\tTwo eyes not found - using mustache angle of 0"

    if len(faces) > 0:
        face_x = faces[0][0]
        face_y = faces[0][1]
        face_w = faces[0][2]
        face_h = faces[0][3]

        # Scale mustache
        # Change MUSTACHE_TO_FACE_SIZE_RATIO to adjust mustache size
        # relative to face
        mustache_w = int(1.0 * face_w * MUSTACHE_TO_FACE_SIZE_RATIO)
        mustache_h = int(1.0 * mustache_w / mustache_aspect_ratio)

        if DEBUG_MODE:
            draw_rectangle(cv_image, faces[0], (0, 0, 255))
            print "\tMustache width = " + str(mustache_w)
    else:
        # If for some reason a face wasn't found, guess a mustache width
        # and scale
        mustache_w = DEFAULT_MUSTACHE_WIDTH
        mustache_h = int(1.0 * mustache_w / mustache_aspect_ratio)

        if DEBUG_MODE:
            print "\tNo face found - using default mustache width (" + \
                  str(mustache_w) + ")"

    # Guess location of mustache based on face
    # Change MUSTACHE_VERTICAL_POSITION_RATIO to ajust
    # vertical positioning of mustache
    def place_on_face_guessed():
        mustache_x = int(1.0 * face_x + (face_w/2)) - \
            int(1.0 * mustache_w / 2)
        mustache_y = int(1.0 * face_y +
                         (MUSTACHE_VERTICAL_POSITION_RATIO * face_h)) - \
            int(1.0 * mustache_h / 2)
        return (mustache_x, mustache_y)
        print "\tNo nose found - guessing nose center of (" + \
              str(mustache_x) + ", " + str(mustache_y) + ")"

    if len(noses) > 0:
        # If more than one nose found, take noses[0] (the one with the
        # highest confidence value)
        nose_x = noses[0][0]
        nose_y = noses[0][1]
        nose_w = noses[0][2]
        nose_h = noses[0][3]

        # Redefine x and y as center of bottom of nose
        nose_x = int(1.0 * nose_x + (nose_w / 2))
        nose_y = int(1.0 * nose_y + (nose_h / 2))

        # Check that nose is inside face
        use_nose = True
        if len(faces) > 0:
            if not (face_x < nose_x and face_x + face_w > nose_x and face_y +
               int(face_h / 3.0) < nose_y and face_y +
               int((2.0 / 3.0) * face_h) > nose_y):
                use_nose = False
                mustache_x, mustache_y = place_on_face_guessed()
        if use_nose:
            mustache_x = nose_x - int(1.0 * mustache_w / 2)
            mustache_y = nose_y + int(1.0 * mustache_h / 2 -
                                      (MUSTACHE_VERTICAL_POSITION_FINE_OFFSET *
                                       nose_w))

        if DEBUG_MODE:
            draw_rectangle(cv_image, noses[0], (255, 0, 0))
            print "\tMustache center = (" + str(mustache_x) + ", " + \
                  str(mustache_y) + ")"

    else:
        if len(faces) > 0:
            mustache_x, mustache_y = place_on_face_guessed()
        else:
            # Don't apply a mustache - not enough information available
            # Save original image and exit
            pil_image.save(output_file, "JPEG")
            sys.exit()

    # Convert image to a format that supports image overlays with alpha
    pil_image = Image.fromstring("RGB", cv.GetSize(cv_image), cv_image.tostring())

    # Redefine mustache x and y to be center of mustache
    mustache_x += int(mustache_w / 2.0)
    mustache_y += int(mustache_h / 2.0)

    # Rotate and resize the mustache
    # Rotate first so the final filter applied is ANTIALIAS
    mustache = mustache.rotate(mustache_angle, Image.BICUBIC, True)
    mrad = math.fabs(math.radians(mustache_angle))
    rotated_width = int(math.fabs(mustache_w * math.cos(mrad) + mustache_h *
                        math.sin(mrad)))
    rotated_height = int(math.fabs(mustache_w * math.sin(mrad) + mustache_h *
                         math.cos(mrad)))
    mustache = mustache.resize((rotated_width, rotated_height),
                               Image.ANTIALIAS)

    # Superimpose the mustache on the face
    pil_image.paste(mustache, (mustache_x-int(mustache.size[0] / 2.0),
                   mustache_y-int(mustache.size[1] / 2.0)), mustache)

    # Save the image into the output file
    pil_image.save(output_file, "JPEG")

if __name__ == "__main__":
    sys.exit(main())
