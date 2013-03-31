# mustachify.py

## Description
A python script that superimposes a mustache over an image of a face using facial recognition. Currently only works with images containing a front view of a single face.

## Dependencies
* [OpenCV](http://opencvlibrary.sourceforge.net)
* [PIL Imaging Library](http://www.pythonware.com/products/pil/)

## Usage
    mustachify.py [-i input file] [-o output file] [options]

    Options:
        -h, --help                Display usage information
        -i, --inputfile           Input image file
        -o, --outputfile          Output image file
        -m, --mustache            Mustache image file
        -d, --debug               Print debugging information and overlay debugging rectangles on image
