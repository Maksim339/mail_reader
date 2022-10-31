import cv2
import numpy as np
from pyzbar.pyzbar import decode


class Preprocessing:
    def __init__(self):
        pass

    @staticmethod
    def rotate_image(image, angle):
        """
        Поворот изображения
        :param image: изображение в numpy array
        :param angle: угол поворота, число
        :return: повернутое изображение в numpy array
        """
        print('start rotate')
        (h, w) = image.shape[:2]
        (cX, cY) = (w / 2, h / 2)
        rot_mat = cv2.getRotationMatrix2D((cX, cY), angle, 1.0)
        cos = np.abs(rot_mat[0, 0])
        sin = np.abs(rot_mat[0, 1])
        nW = int((h * sin) + (w * cos))
        nH = int((h * cos) + (w * sin))
        rot_mat[0, 2] += (nW / 2) - cX
        rot_mat[1, 2] += (nH / 2) - cY
        rotated = cv2.warpAffine(image, rot_mat, (nW, nH))
        return rotated

    @staticmethod
    def left_angle(image):
        height, width = image.shape[:2]
        start_row, start_col = int(0), int(0)
        end_row = int(height * .25)  # размер стороны квадрата
        cropped_top = image[start_row: end_row, start_col:end_row]
        cropped_left_angle = cv2.resize(cropped_top, (500, 500))
        return cropped_left_angle

    @staticmethod
    def crop_detect(image):
        opl = np.array([])
        original = np.copy(image)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # перевод изобр. в оттенки серого
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))  # размер ядра qr кода
        close = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel, iterations=2)
        cnts = cv2.findContours(close, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # поиск контуров
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        for c in cnts:
            peri = cv2.arcLength(c, True)  # периметр контура
            approx = cv2.approxPolyDP(c, 0.04 * peri, True)
            x, y, w, h = cv2.boundingRect(approx)  # контуры qr
            cv2.rectangle(image, (x, y), (x + w, y + h), (36, 255, 12), 3)  # рисует контуры на исходном изобр.
            opl = original[y:y + h, x:x + w]  # обрезка qr
            if opl.size > 0:
                cv2.imwrite('/tmp/ROI.png', opl)

        return opl

    @staticmethod
    def twist(image, num):
        """
        Вращение до распознавания не более трех раз
        :param image: изображение numpy array
        :param num: значение переменной tw из cv_start
        :return:
        """
        print('start twist')
        img = None
        if num == 0:
            img = Preprocessing.rotate_image(image, 90)
        elif num == 1:
            img = Preprocessing.rotate_image(image, 180)
        elif num == 2:
            img = Preprocessing.rotate_image(image, 270)
        return img


class GetQRCode(Preprocessing):
    def __init__(self, page: str):
        super().__init__()
        self.page = page
        self.image = None

    def qr_code_decoding(self):
        blur_factor = 1
        self.image = cv2.imread(self.page)
        qr_code_info = decode(self.image)
        while blur_factor < 9 or not qr_code_info:
            final_image = cv2.GaussianBlur(
                self.page,
                (blur_factor, blur_factor),
                0
            )
            final_image = Preprocessing.left_angle(image=final_image)
            left_angle_image = Preprocessing.crop_detect(image=final_image)
            cropped_image = Preprocessing.crop_detect(left_angle_image)
            qr_code_info = decode(cropped_image)
            if not qr_code_info:
                flip = 0
                while not qr_code_info and flip < 3:
                    image = Preprocessing.twist(flip, flip)
                    left_angle_img = Preprocessing.left_angle(image)
                    img = Preprocessing.crop_detect(left_angle_img)
                    qr_code_info = decode(img)
                    flip += 1
            blur_factor += 2
        return qr_code_info


def utc_time(email_date):
    email_date_utc = dateutil.parser.parse(str(email_date))
    email_date_utc = email_date_utc.astimezone(pytz.utc)
    email_date_utc = email_date_utc.replace(tzinfo=pytz.UTC) - email_date_utc.utcoffset()
    email_date = time.mktime(email_date_utc.timetuple())
    return email_date
