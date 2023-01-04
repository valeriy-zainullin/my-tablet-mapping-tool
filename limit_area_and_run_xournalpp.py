#!/usr/bin/python3

# Устанавливает 1:1 физическое соответствие экрана и графического планшета в правом верхнем углу экрана.
# И запускает xournalpp, изменив его ширину и высоту.

# https://askubuntu.com/a/1174076
# https://unix.stackexchange.com/questions/5999/setting-the-window-dimensions-of-a-running-application

MONITOR_DIAG_INCHES = 15.6
MONITOR_RATIO_ROWS = 9
MONITOR_RATIO_COLS = 16

MONITOR_RESOLUTION_ROWS = 1080
MONITOR_RESOLUTION_COLS = 1920

# С сайта производителя и с коробки
TABLET_WIDTH_INCHES = 4.8
TABLET_HEIGHT_INCHES = 3
SCALE_TABLET = 1.5
ROTATE_TABLET_TIMES = 3 # Количество вращений планшета на 90 градусов против часовой стрелки. 4 -- тождественное преобразование.

# Посмотреть в xinput, нажав предварительно все кнопки по одному разу.
TABLET_POINTERS = ['HUION Huion Tablet_RTE-100 Pen (0)', 'HUION Huion Tablet_RTE-100 Eraser (0)']

screen_used_area_width_inches = TABLET_WIDTH_INCHES * SCALE_TABLET
screen_used_area_height_inches = TABLET_HEIGHT_INCHES * SCALE_TABLET

if ROTATE_TABLET_TIMES % 2 == 1:
  screen_used_area_width_inches, screen_used_area_height_inches = screen_used_area_height_inches, screen_used_area_width_inches

import math

monitor_unit_length_inches = MONITOR_DIAG_INCHES / math.sqrt(MONITOR_RATIO_COLS ** 2 + MONITOR_RATIO_ROWS ** 2)
monitor_width_inches = monitor_unit_length_inches * MONITOR_RATIO_COLS
monitor_height_inches = monitor_unit_length_inches * MONITOR_RATIO_ROWS

offset_x_inches = monitor_width_inches - screen_used_area_width_inches
offset_y_inches = 0 # monitor_height_inches - TABLET_HEIGHT_INCHES for bottom right corner

# Матрица преобразования координат от libinput применяется к координатам от устройства, они превращаются в
#   координаты экрана. Мы создаём её как композицию нескольких матриц линейных отображений.
conversions = []

# Если есть вращение, то надо преобразовать координаты в координаты СК области, она ориентирована,
#   соответствует СК на поверхности устройства. Координаты пока номированы относительно размеров устройства.
# Можно выписать такой массив, но поскольку координаты отнормированы, получается удобно, что просто
#   можно просто на эту матрицу несколько раз умножить.
rotations = (
  ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
  ((0, 1, 0), (-1, 0, 1), (0, 0, 1)),  
)
for i in range(ROTATE_TABLET_TIMES):
    conversions.append(rotations[1])
# Перевод из координат устройства, нормированных относительно размеров устройства,
#   в координаты СК области, нормированные относительно её размера. Просто
#   оставляем как есть, на самом деле. Т.к. у нас уже как раз координата в
#   процентах размерности области.
# Из координат СК области, но нормированных относительно её размера, в координаты в её же СК, но
#   нормированные относительно размеров экрана. Для этого сначала переводим в абсолютные, а потом
#   нормируем по-новому.
normalize_region_cords_mtx = (
  (1 * screen_used_area_width_inches / monitor_width_inches, 0, 0),
  (0, 1 * screen_used_area_height_inches / monitor_height_inches, 0),
  (0, 0, 1),
)
conversions.append(normalize_region_cords_mtx)
# Из нормированных координат отсительно СК области, нормированные относительно размера экрана,
#   в координаты экрана, нормированные относительно размера экрана.
convert_to_region_cords_mtx = (
  (1, 0, offset_x_inches / monitor_width_inches),
  (0, 1, offset_y_inches / monitor_height_inches),
  (0, 0, 1),
)
conversions.append(convert_to_region_cords_mtx)

def mtx_prod(lhs, rhs):
  lhs_rows = len(lhs)
  lhs_cols = len(lhs[0])
  rhs_rows = len(rhs)
  rhs_cols = len(rhs[0])

  assert lhs_cols == rhs_rows
  result = [[0 for col in range(rhs_cols)] for row in range(lhs_rows)]
  for i in range(lhs_rows):
    for j in range(rhs_cols):
      for k in range(rhs_rows):
        result[i][j] += lhs[i][k] * rhs[k][j]
  return result

mtx = (
  (1, 0, 0),
  (0, 1, 0),
  (0, 0, 1)
)
for conversion in conversions:
  mtx = mtx_prod(conversion, mtx)

import os
for pointer in TABLET_POINTERS:
  array = ' '.join((' '.join(map(str, row)) for row in mtx))
  os.system("xinput set-prop '%s' --type=float 'Coordinate Transformation Matrix' %s" % (pointer, array))

win_size_cols = screen_used_area_width_inches / monitor_width_inches * MONITOR_RESOLUTION_COLS
win_size_rows = screen_used_area_height_inches / monitor_height_inches * MONITOR_RESOLUTION_ROWS

if ROTATE_TABLET_TIMES % 2 == 1:
  win_size_cols, win_size_rows = win_size_rows, win_size_cols

os.system("bash -c 'nohup xournalpp > /dev/null 2>&1 &'")

import time
# Wait for the window to open.
time.sleep(5)

os.system("xdotool search --name 'Xournal\+\+$' windowsize %d %d" % (int(win_size_cols), int(win_size_rows)))

# Doesn't work correctly for me, I move manually to the upper right corner.
target_pos = (MONITOR_RESOLUTION_COLS - int(win_size_cols), 0) # (MONITOR_RESOLUTION_COLS - int(win_size_cols), MONITOR_RESOLUTION_ROWS - int(win_size_rows)) for bottom right corner
os.system("xdotool search --name 'Xournal\+\+$' windowmove %d %d" % target_pos)
