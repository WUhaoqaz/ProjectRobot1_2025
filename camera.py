import image
import lcd
import gc
import time
import sensor
from maix import KPU
from maix import GPIO
from modules import ybserial
from fpioa_manager import fm
from board import board_info

serial = ybserial()
lcd.init()
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=100)
clock = time.clock()

FACE_PIC_SIZE = 64
dst_point = [(int(38.2946 * FACE_PIC_SIZE / 112), int(51.6963 * FACE_PIC_SIZE / 112)),
             (int(73.5318 * FACE_PIC_SIZE / 112), int(51.5014 * FACE_PIC_SIZE / 112)),
             (int(56.0252 * FACE_PIC_SIZE / 112), int(71.7366 * FACE_PIC_SIZE / 112)),
             (int(41.5493 * FACE_PIC_SIZE / 112), int(92.3655 * FACE_PIC_SIZE / 112)),
             (int(70.7299 * FACE_PIC_SIZE / 112), int(92.2041 * FACE_PIC_SIZE / 112))]

anchor = (0.1075, 0.126875, 0.126875, 0.175, 0.1465625, 0.2246875,
          0.1953125, 0.25375, 0.2440625, 0.351875, 0.341875, 0.4721875,
          0.5078125, 0.6696875, 0.8984375, 1.099687, 2.129062, 2.425937)

feature_img = image.Image(size=(64, 64), copy_to_fb=False)
feature_img.pix_to_ai()

kpu = KPU()
kpu.load_kmodel("/sd/KPU/yolo_face_detect/face_detect_320x240.kmodel")
kpu.init_yolo2(anchor, anchor_num=9, img_w=320, img_h=240, net_w=320,
               net_h=240, layer_w=10, layer_h=8, threshold=0.7,
               nms_value=0.2, classes=1)

ld5_kpu = KPU()
print("ready load model")
ld5_kpu.load_kmodel("/sd/KPU/face_recognization/ld5.kmodel")

fea_kpu = KPU()
print("ready load model")
fea_kpu.load_kmodel("/sd/KPU/face_recognization/feature_extraction.kmodel")

start_processing = False
BOUNCE_PROTECTION = 50
record_ftrs = []
THRESHOLD = 80.5
recog_flag = False
msg_ = ""

def adjust_box(x, y, w, h, scale=0.08):
    x1_t = x - scale * w
    x2_t = x + w + scale * w
    y1_t = y - scale * h
    y2_t = y + h + scale * h
    x1 = int(x1_t) if x1_t > 1 else 1
    x2 = int(x2_t) if x2_t < 320 else 319
    y1 = int(y1_t) if y1_t > 1 else 1
    y2 = int(y2_t) if y2_t < 240 else 239
    cut_img_w = x2 - x1 + 1
    cut_img_h = y2 - y1 + 1
    return x1, y1, cut_img_w, cut_img_h

def show_status(img, text, is_ok=True):
    color = (0, 255, 0) if is_ok else (255, 0, 0)
    img.draw_string(0, 180, text, color=color, scale=2.0)

def key_pressed(*_):
    global start_processing
    start_processing = True
    time.sleep_ms(BOUNCE_PROTECTION)

fm.register(board_info.BOOT_KEY, fm.fpioa.GPIOHS0)
key_gpio = GPIO(GPIO.GPIOHS0, GPIO.IN)
key_gpio.irq(key_pressed, GPIO.IRQ_RISING, GPIO.WAKEUP_NOT_SUPPORT)

while True:
    gc.collect()
    clock.tick()
    img = sensor.snapshot()
    fps = clock.fps()
    kpu.run_with_output(img)
    dect = kpu.regionlayer_yolo2()
    
    if len(dect) > 0:
        for l in dect:
            x1, y1, cut_img_w, cut_img_h = adjust_box(l[0], l[1], l[2], l[3])
            face_cut = img.cut(x1, y1, cut_img_w, cut_img_h)
            face_cut_128 = face_cut.resize(128, 128)
            face_cut_128.pix_to_ai()
            out = ld5_kpu.run_with_output(face_cut_128, getlist=True)
            face_key_point = []
            for j in range(5):
                x = int(KPU.sigmoid(out[2 * j]) * cut_img_w + x1)
                y = int(KPU.sigmoid(out[2 * j + 1]) * cut_img_h + y1)
                face_key_point.append((x, y))
            T = image.get_affine_transform(face_key_point, dst_point)
            image.warp_affine_ai(img, feature_img, T)
            feature = fea_kpu.run_with_output(feature_img, get_feature=True)
            del face_key_point
            scores = []
            for j in range(len(record_ftrs)):
                score = kpu.feature_compare(record_ftrs[j], feature)
                scores.append(score)
            if len(scores):
                max_score = max(scores)
                index = scores.index(max_score)
                if max_score > THRESHOLD:
                    img.draw_string(0, 195, "persion:%d,score:%2.1f" % (index, max_score), color=(0, 255, 0), scale=2)
                    recog_flag = True
                else:
                    img.draw_string(0, 195, "unregistered,score:%2.1f" % (max_score), color=(255, 0, 0), scale=2)
            del scores
            if start_processing:
                record_ftrs.append(feature)
                print("record_ftrs:%d" % len(record_ftrs))
                if len(dect) == 1:
                    show_status(img, "Registered!")
                else:
                    show_status(img, "Only one face", False)
                start_processing = False
            if recog_flag:
                img.draw_rectangle(l[0], l[1], l[2], l[3], color=(0, 255, 0))
                recog_flag = False
                if index < 10:
                    index = "%02d" % index
                msg_ = "%s%s" % ("Y", str(index))
            else:
                img.draw_rectangle(l[0], l[1], l[2], l[3], color=(255, 255, 255))
                msg_ = "N"
            del face_cut_128
            del face_cut
    
    if len(dect) > 0:
        send_data = "$08" + msg_ + ",#"
        time.sleep_ms(5)
        serial.send(send_data)
    else:
        serial.send("#")
    
    img.draw_string(0, 0, "%2.1ffps" % fps, color=(0, 60, 255), scale=2.0)
    registered_count = len(record_ftrs)
    img.draw_string(0, 25, "Registered: %d" % registered_count, color=(255, 255, 0), scale=2.0)
    img.draw_string(0, 215, "Press BOOT to reset", color=(255, 100, 0), scale=2.0)
    lcd.display(img)

kpu.deinit()
ld5_kpu.deinit()
fea_kpu.deinit()
