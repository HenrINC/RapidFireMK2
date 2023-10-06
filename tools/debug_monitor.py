from ps3_lib import PS3, PS3_CFW_INFOS

import cv2
import fire

def main(url):
    ps3 = PS3(url)
    infos = {}
    while True:
        screenshot = ps3.get_screenshot(fast=False)
        # text_height = 30
        # for i, info in enumerate(PS3_CFW_INFOS):
        #     text_height += 30
        #     cv2.putText(screenshot, info.value + ps3.get_info(info), (0 , text_height), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        cv2.imshow("screenshot", screenshot)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

fire.Fire(main)