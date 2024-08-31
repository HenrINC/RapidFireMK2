from yesman import PS3

import cv2
import fire


def main(fast=True, **kwargs):
    ps3 = PS3(**kwargs)
    while True:
        try:
            screenshot = ps3.get_screenshot(fast=fast)
        except Exception as e:
            pass
        cv2.imshow("screenshot", screenshot)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cv2.destroyAllWindows()


fire.Fire(main)
