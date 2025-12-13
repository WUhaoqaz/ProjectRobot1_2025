def show_number(num: number):
    if num == 0:
        basic.show_leds("""
            . . # # .
            . # . . #
            . # . . #
            . # . . #
            . . # # .
            """)
    elif num == 1:
        basic.show_leds("""
            . . # . .
            . . # . .
            . . # . .
            . . # . .
            . . # . .
            """)
    elif num == 2:
        basic.show_leds("""
            . # # # #
            . . . . #
            . # # # #
            . # . . .
            . # # # #
            """)
    elif num == 3:
        basic.show_leds("""
            . # # # .
            # . . . #
            . . # # .
            # . . . #
            . # # # .
            """)
    elif num == 4:
        basic.show_leds("""
            # . . # .
            # . . # .
            # # # # #
            . . . # .
            . . . # .
            """)
    elif num == 5:
        basic.show_leds("""
            # # # # #
            # . . . .
            # # # # .
            . . . . #
            # # # # .
            """)
    elif num == 6:
        basic.show_leds("""
            . # # # .
            # . . . .
            # # # # .
            # . . . #
            . # # # .
            """)
    elif num == 7:
        basic.show_leds("""
            # # # # #
            . . . # .
            . . # . .
            . # . . .
            # . . . .
            """)
    elif num == 8:
        basic.show_leds("""
            . # # # .
            # . . . #
            . # # # .
            # . . . #
            . # # # .
            """)
    elif num == 9:
        basic.show_leds("""
            . # # # .
            # . . . #
            . # # # #
            . . . . #
            . # # # .
            """)
    elif num == 10:
        basic.show_leds("""
            # . # # #
            # . # . #
            # . # . #
            # . # . #
            # . # # #
            """)
    else:
        basic.show_leds("""
            # . . . #
            . # . # .
            . . # . .
            . # . # .
            # . . . #
            """)

def update_display(face_id: number):
    global display_lock, last_stable_face
    is_playing_music = 0
    if face_id != last_stable_face and not (is_playing_music):
        display_lock = True
        if face_id == -1:
            basic.show_leds("""
                . # # # .
                # . . # .
                . . # . .
                . . . . .
                . . # . .
                """)
        else:
            show_number(face_id)
        last_stable_face = face_id
        basic.pause(350)
        display_lock = False

def on_button_pressed_a():
    global test_number
    test_number = (test_number + 1) % 11
    show_number(test_number)
input.on_button_pressed(Button.A, on_button_pressed_a)

def on_button_pressed_b():
    global test_number
    test_number = (test_number - 1) % 11
    if test_number < 0:
        test_number = 10
    show_number(test_number)
input.on_button_pressed(Button.B, on_button_pressed_b)

display_lock = False
last_stable_face = 0
test_number = 0
current_face = -2

k210_models.initialization()
basic.show_icon(IconNames.HAPPY)
basic.pause(500)
basic.clear_screen()

def on_forever():
    global current_face
    if not (display_lock):
        new_face = k210_models.face_reg()
        if new_face != current_face:
            start_time = input.running_time()
            while input.running_time() - start_time < 250:
                if k210_models.face_reg() != new_face:
                    return
            current_face = new_face
            update_display(current_face)
basic.forever(on_forever)
