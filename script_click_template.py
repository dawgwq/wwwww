import pyautogui
import time

# Функция для нахождения центра шаблона и клика по нему
def find_template_center_and_click(template_location, template_width, template_height, window):
    # Вычисляем координаты центра шаблона относительно окна
    template_center_x = template_location[0] + template_width // 2
    template_center_y = template_location[1] + template_height // 2
    
    # Вычисляем абсолютные координаты центра шаблона на экране
    abs_x = window.left + template_center_x
    abs_y = window.top + template_center_y

    # Производим клик по центру шаблона
    pyautogui.click(x=abs_x, y=abs_y)


find_template_center_and_click(template_location, template_width, template_height, window)
time.sleep(1)