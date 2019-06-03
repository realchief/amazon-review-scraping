import numpy as np
import argparse
import cv2
import os
from PIL import Image
import pytesseract
import urllib

def get_captcha_temp_root():
    temp_root = os.path.dirname(os.path.realpath(__file__))
    temp_root = os.path.join(temp_root, "temp")
    try:
        if not os.path.isdir(temp_root):
            os.makedirs(temp_root)
        return temp_root
    except:
        pass

    return ""

pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files (x86)\\Tesseract-OCR\\tesseract"
captcha_resolve_temp_root = get_captcha_temp_root()

def get_file_title(path):
    return os.path.splitext(path)[0]

def captcha_solver(path, threshold=245):
    image = cv2.imread(path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    colmean = image.sum(axis=0)/70
    colmean_index = np.where(colmean < threshold)
    min_val = np.min(colmean_index)
    max_val = np.max(colmean_index)

    colmean_index = list(colmean_index)
    separators = []

    prefix = get_file_title(path) + "_"

    for i in np.arange(0,len(colmean_index[0]) - 1):
        if colmean_index[0][i] != colmean_index[0][i+1] - 1:
            separators.append(colmean_index[0][i])

    if len(separators) == 5:
        cv2.imwrite(os.path.join(captcha_resolve_temp_root, prefix + 'Digit1.jpg'), image[:,min_val:separators[0]])
        cv2.imwrite(os.path.join(captcha_resolve_temp_root, prefix + 'Digit2.jpg'), image[:,separators[0]+1:separators[1]])
        cv2.imwrite(os.path.join(captcha_resolve_temp_root, prefix + 'Digit3.jpg'), image[:,separators[1]+1:separators[2]])
        cv2.imwrite(os.path.join(captcha_resolve_temp_root, prefix + 'Digit4.jpg'), image[:,separators[2]+1:separators[3]])
        cv2.imwrite(os.path.join(captcha_resolve_temp_root, prefix + 'Digit5.jpg'), image[:,separators[3]+1:separators[4]])
        cv2.imwrite(os.path.join(captcha_resolve_temp_root, prefix + 'Digit6.jpg'), image[:,separators[4]+1:max_val])

        string = []
        for i in np.arange(1,7):
            img = Image.open(os.path.join(captcha_resolve_temp_root, prefix + 'Digit%d.jpg' % i))
            # converted to have an alpha layer
            im2 = img.convert('RGBA')
            if i in [1,3,5]:
                # rotated image
                rot = im2.rotate(15, expand=1)
            else:
                # rotated image
                rot = im2.rotate(-15, expand=1)
            # a white image same size as rotated image
            fff = Image.new('RGBA', rot.size, (255,)*4)
            # create a composite image using the alpha layer of rot as a mask
            out = Image.composite(rot, fff, rot)

            img_path = os.path.join(captcha_resolve_temp_root, prefix + 'pic%d.jpg' % i)
            out.convert(img.mode).save(img_path)

            char = pytesseract.image_to_string(Image.open(img_path),
                    config='-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ -psm 10')[0].upper()

            os.remove(img_path)

            if i == 1:
                string = char
            else:
                string += char
    else:
        string = ""

    return string

def resolve_captcha(url):
    captcha_string = ""
    try:
        filename = url[url.rfind('/') + 1:]
        captcha_path = os.path.join(get_captcha_temp_root(), filename)
        urllib.request.urlretrieve(url, captcha_path)

        captcha_string = captcha_solver(captcha_path)
        os.remove(captcha_path)
    except:
        pass

    return captcha_string