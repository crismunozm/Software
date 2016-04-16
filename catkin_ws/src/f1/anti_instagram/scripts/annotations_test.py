#!/usr/bin/env python
from anti_instagram import AntiInstagram, logger, wrap_test_main
from anti_instagram.AntiInstagram import ScaleAndShift, calculate_transform
from duckietown_utils.expand_variables import expand_environment
from duckietown_utils.jpg import (image_clip_255, image_cv_from_jpg_fn,
    make_images_grid)
from duckietown_utils.locate_files_impl import locate_files
from line_detector.LineDetector import LineDetector
import cv2
import os
import scipy.io

def examine_dataset(dirname, out):
    logger.info(dirname)
    dirname = expand_environment(dirname)

    jpgs = locate_files(dirname, '*.jpg')
    mats = locate_files(dirname, '*.mat')

    logger.debug('I found %d jpgs and %d mats' % (len(jpgs), len(mats)))

    if len(jpgs) == 0:
        msg = 'Not enough jpgs.'
        raise ValueError(msg)

#     if len(mats) == 0:
#         msg = 'Not enough mats.'
#         raise ValueError(msg)

    first_jpg = sorted(jpgs)[0]
    logger.debug('Using jpg %r to learn transformation.' % first_jpg)

    first_jpg_image = image_cv_from_jpg_fn(first_jpg)


    success, health, parameters = calculate_transform(first_jpg_image)

    s = ""
    s += 'success: %s\n' % str(success)
    s += 'health: %s\n' % str(health)
    s += 'parameters: %s\n' % str(parameters)
    w = os.path.join(out, 'learned_transform.txt')
    with open(w, 'w') as f:
        f.write(s)
    logger.info(s)
    
    transform = ScaleAndShift(**parameters)
    
    for j in jpgs:
        shape = (200, 160)

        name = 'nearest'
        interpolation = cv2.INTER_NEAREST

        run_detection(transform, j, out, shape=shape,
                      interpolation=interpolation, name=name)

        name = 'cubic'
        interpolation = cv2.INTER_CUBIC

        run_detection(transform, j, out, shape=shape,
                      interpolation=interpolation, name=name)

    for m in mats:
        logger.debug(m)
        jpg = os.path.splitext(m)[0] + '.jpg'
        if not os.path.exists(jpg):
            msg = 'JPG %r for mat %r does not exist' % (jpg, m)
            logger.error(msg)
#             raise ValueError(msg)
        else:
            test_pair(transform, jpg, m, out)
        
def run_detection(transform, jpg, out, shape, interpolation,
                  name):
    image = image_cv_from_jpg_fn(jpg)


    image = cv2.resize(image, shape, interpolation=interpolation)
#     bgr = bgr[bgr.shape[0] / 2:, :, :]


    image_detections = line_detection(image)
    transformed = transform(image)

    transformed_clipped = image_clip_255(transformed)
    transformed_detections = line_detection(transformed_clipped)

    if not os.path.exists(out):
        os.makedirs(out)
    bn = os.path.splitext(os.path.basename(jpg))[0]

    def write(postfix, im):
        zoom = 4
        s = (im.shape[1] * zoom, im.shape[0] * zoom)
        imz = cv2.resize(im, s, interpolation=cv2.INTER_NEAREST)

        fn = os.path.join(out, '%s.%s.%s.png' % (bn, name, postfix))
        cv2.imwrite(fn, imz)

#     write('orig', image)
#     write('transformed', transformed)
#     write('transformed_clipped', transformed_clipped)
#     write('orig.detected', image_detections)
#     write('transformed.detected', transformed_detections)

    together = make_images_grid([image,  # transformed,
                                 transformed_clipped,
                       image_detections,
                       transformed_detections], cols=None, pad=10, bgcolor=[1, 1, 1])
    write('together', together)


def test_pair(transform, jpg, mat, out):
    """ 
        jpg = filename
        mat = filename
    """

    data = scipy.io.loadmat(mat)
    regions = data['regions'].flatten()
    for r in regions:
        logger.info('region')
        x = r['x'][0][0].flatten()
        y = r['y'][0][0].flatten()
        mask = r['mask'][0][0]
        print 'x', x
        print 'y', y
        print 'mask shape', mask.shape
        print 'type', r['type']
        print 'color', r['color']

        # XXX: to finish

def line_detection(bgr):
    detector = LineDetector()
    detector.setImage(bgr)

    # detect lines and normals
    lines_white, normals_white = detector.detectLines('white')
    lines_yellow, normals_yellow = detector.detectLines('yellow')
    lines_red, normals_red = detector.detectLines('red')

    # draw lines
    detector.drawLines(lines_white, (0, 0, 0))
    detector.drawLines(lines_yellow, (255, 0, 0))
    detector.drawLines(lines_red, (0, 255, 0))

    # draw normals
    detector.drawNormals(lines_yellow, normals_yellow)
    detector.drawNormals(lines_white, normals_white)
    detector.drawNormals(lines_red, normals_red)

    return detector.getImage()

#    cv2.imwrite('lines_with_normal.png', detector.getImage())


def anti_instagram_annotations_test():
    base = "${DUCKIETOWN_DATA}/phase3-misc-files/so1/"

    base = expand_environment(base)
    dirs = locate_files(base, '*.iids1', alsodirs=True)

    for d in dirs:
        import getpass
        uname = getpass.getuser()
        out = os.path.join(os.path.dirname(d), uname, os.path.basename(d) + '.v')
        if not os.path.exists(out):
            os.makedirs(out)
        examine_dataset(d, out)


if __name__ == '__main__':
    wrap_test_main(anti_instagram_annotations_test) 