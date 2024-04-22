import tkinter as tk
import pygetwindow as gw
import cv2
import numpy as np
from tkinter import filedialog
from PIL import Image, ImageTk
from mss import mss
import os
import threading
import pickle

# Глобальные переменные для хранения списка шаблонов и их сценариев
templates = []
template_scripts = {}
data_file = "data.pkl"

def load_data():
    global templates, template_scripts
    if os.path.exists(data_file):
        with open(data_file, "rb") as f:
            data = pickle.load(f)
            templates = data.get("templates", [])
            template_scripts = data.get("template_scripts", {})

def save_data():
    data = {"templates": templates, "template_scripts": template_scripts}
    with open(data_file, "wb") as f:
        pickle.dump(data, f)

def get_open_window_names():
    # Получаем список всех окон на рабочем столе и фильтруем пустые строки
    all_windows = [window for window in gw.getAllTitles() if window.strip()]
    return all_windows

def process_window(window_name):
    try:
        # Получаем объект окна по его имени
        window = gw.getWindowsWithTitle(window_name)[0]

        # Получаем координаты и размеры окна
        left, top, width, height = window.left, window.top, window.width, window.height

        # Создаем объект mss для захвата видео с этого окна
        monitor = {"left": left, "top": top, "width": width, "height": height}
        with mss() as sct:
            show_image = True  # Флаг, указывающий, нужно ли показывать изображение
            while True:
                
                # Захватываем кадр видео с экрана окна
                frame = np.array(sct.grab(monitor))

                # Копируем кадр для рисования шаблонов
                frame_with_templates = frame.copy()

                # Рисуем прямоугольники вокруг каждого шаблона
                for template_path in template_scripts.keys():
                    template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
                    # Ищем шаблон на кадре
                    result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
                    # Устанавливаем пороговое значение
                    threshold = 0.8
                    # Находим точки, где значение корреляции превышает порог
                    loc = np.where(result >= threshold)
                    # Рисуем прямоугольники вокруг найденных объектов
                    for pt in zip(*loc[::-1]):
                        bottom_right = (pt[0] + template.shape[1], pt[1] + template.shape[0])
                        cv2.rectangle(frame_with_templates, pt, bottom_right, (0, 255, 0), 2)
                        # Проверяем, есть ли сценарий для этого шаблона
                        script_path = template_scripts.get(template_path)
                        if script_path:
                            # Выполняем сценарий, используя информацию о шаблоне, например, его координаты
                            execute_script(script_path, window=window, left=left, top=top, width=width,
                                            height=height,
                                            template_path=template_path, template_width=template.shape[1],
                                            template_height=template.shape[0], template_location=pt)
                            print("Скрипт был вызван в файле main.py")
                            break

                if show_image:
                    cv2.imshow(window_name, frame_with_templates)

                # Если пользователь нажимает клавишу "q", выходим из цикла
                key = cv2.waitKey(1)
                if key & 0xFF == ord("q"):
                    break
                elif key == ord("s"):  # Если нажата клавиша "s", переключаем флаг
                    show_image = not show_image

        # Закрываем окно OpenCV
        cv2.destroyWindow(window_name)
    except IndexError:
        print("Окно не найдено.")

def open_modal_windows():
    selected_windows = listbox.curselection()
    for index in selected_windows:
        selected_window = listbox.get(index)
        # Запуск отдельного потока для обработки окна
        thread = threading.Thread(target=process_window, args=(selected_window,))
        thread.start()

def add_template():
    # Открываем файл с изображением шаблона
    template_path = filedialog.askopenfilename()
    if template_path:
        # Загружаем изображение шаблона и добавляем его в список шаблонов
        template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
        templates.append(template)
        # Отображаем изображение шаблона и путь до скрипта на главном окне
        display_template(template_path)
        
        # Создаем кнопку для добавления сценария к данному шаблону
        add_script_to_template_button = tk.Button(root, text="Добавить сценарий", 
                                                   command=lambda: add_script_to_template(template_path))
        add_script_to_template_button.pack(pady=5)
        
        # Сохраняем данные
        save_data()

def add_script_to_template(template_path):
    # Открываем файл сценария
    script_path = filedialog.askopenfilename(filetypes=[("Python files", "*.py")])
    if script_path:
        # Получаем имя файла сценария
        script_name = os.path.basename(script_path)
        # Добавляем сценарий в словарь template_scripts с ключом по имени файла шаблона
        template_scripts[os.path.basename(template_path)] = script_path
        print(f"Сценарий {script_name} добавлен к шаблону {os.path.basename(template_path)}.")
        
        # Сохраняем данные
        save_data()

def display_template(template_path):
    global templates, template_scripts
    # Преобразуем изображение в формат, который можно отобразить в Tkinter
    template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
    img = cv2.cvtColor(template, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    img = ImageTk.PhotoImage(image=img)

    # Создаем метку для отображения изображения
    label = tk.Label(root, image=img)
    label.image = img
    label.pack(pady=5)

    # Получаем путь до скрипта, привязанного к этому шаблону
    script_path = template_scripts.get(os.path.basename(template_path), "Нет скрипта")

    # Создаем метку для отображения пути до скрипта
    script_label = tk.Label(root, text=f"Скрипт: {script_path}")
    script_label.pack()

def execute_script(script_path, **kwargs):
    # Выполнение сценария
    try:
        # Открываем файл сценария и читаем его содержимое
        with open(script_path, "r") as script_file:
            script_code = script_file.read()
        
        # Создаем локальное пространство имен для выполнения сценария
        script_globals = {
            **kwargs  # Добавляем дополнительные переданные параметры
        }
        
        # Выполняем сценарий в созданном локальном пространстве имен
        exec(script_code, script_globals)
    except Exception as e:
        print(f"Ошибка при выполнении сценария {script_path}: {e}")

# Создание главного окна
root = tk.Tk()
root.title("Выбор окна")

# Загрузка данных
load_data()

# Создание списка окон с возможностью множественного выбора
window_names = get_open_window_names()
listbox = tk.Listbox(root, selectmode=tk.MULTIPLE)
for window_name in window_names:
    listbox.insert(tk.END, window_name)
listbox.pack(pady=5)

# Создание кнопки для открытия выбранных окон
button = tk.Button(root, text="Открыть выбранные окна для захвата", command=open_modal_windows)
button.pack(pady=5)

# Создание кнопки для добавления шаблона
add_template_button = tk.Button(root, text="Добавить шаблон", command=add_template)
add_template_button.pack(pady=5)

# Запуск главного цикла
root.mainloop()