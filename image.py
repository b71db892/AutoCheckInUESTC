import numpy as np


class IMG:
    def __init__(self, img_id=None, md5=None, base64_src=None, win_start=None,
                 win_end=None, cooked_id=None, raw_id=None, cv2_ndarray=None, cv2_img=None):
        self.img_id = img_id
        self.md5 = md5
        self.base64_src = base64_src
        self.win_start = win_start
        self.win_end = win_end
        self.cooked_id = cooked_id
        self.raw_id = raw_id
        self.cv2_ndarray = cv2_ndarray
        self.cv2_img = cv2_img

    def copy(self, img_id=None, md5=None, base64_src=None, win_start=None,
             win_end=None, cooked_id=None, raw_id=None, cv2_ndarray=None, cv2_img=None):
        """
         copy and update
        """
        arr = np.array(self.cv2_ndarray, dtype=np.uint8) if type(self.cv2_ndarray) == np.ndarray else self.cv2_ndarray
        img = self.cv2_img.copy() if type(self.cv2_img) == np.ndarray else self.cv2_img
        new = IMG(img_id=img_id if img_id else self.img_id,
                  md5=md5 if md5 else self.md5,
                  base64_src=base64_src if base64_src else self.base64_src,
                  win_start=win_start if win_start else self.win_start,
                  win_end=win_end if win_end else self.win_end,
                  cooked_id=cooked_id if cooked_id else self.cooked_id,
                  raw_id=raw_id if raw_id else self.raw_id,
                  cv2_ndarray=cv2_ndarray if cv2_ndarray is not None else arr,
                  cv2_img=cv2_img if cv2_img is not None else img
                  )
        return new

    def win(self, win=None):
        if win and len(win) == 2:
            self.win_start, self.win_end = win
            return self
        else:
            return [self.win_start, self.win_end]
