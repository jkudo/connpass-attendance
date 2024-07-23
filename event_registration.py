import cv2
import numpy as np
import pytesseract
from picamera2 import Picamera2
import re
import pandas as pd
import glob
from tkinter import Tk, Label, StringVar, Frame
from PIL import Image, ImageTk

# Tesseractのパスを指定（必要に応じて変更してください）
# Windowsの場合の例:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# MacやLinuxの場合、通常はインストールパスが通っているのでこの行は必要ありません。

# Picamera2の初期化と設定
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

# 認識用の変数
last_decoded_info = None
confirmation_count = 0
confirmation_threshold = 5
confirmed_info = None
confirmed_slot_name = None
confirmed_user_name = None

# CSVファイルの読み込み
csv_file_path = '/media/pipi/CSV/event_*_participants.csv'  # ワイルドカードでファイルを検索
csv_files = glob.glob(csv_file_path)

if not csv_files:
    print("No CSV file found matching the pattern.")
    exit()

csv_file_path = csv_files[0]  # 最初に見つかったファイルを使用
print(f"Using CSV file: {csv_file_path}")

# CSVファイルの読み込み
participants_df = pd.read_csv(csv_file_path, encoding='utf-8')  # UTF-8エンコーディングを使用

# 参加ステータス列を追加
if '参加ステータス' not in participants_df.columns:
    participants_df['参加ステータス'] = ''

# 参加ステータス列を文字列型に変換
participants_df['参加ステータス'] = participants_df['参加ステータス'].astype(str)

# Tkinterの初期化
root = Tk()
root.title("認識結果")

# ウィンドウを最大化
root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))

# フレームの作成
left_frame = Frame(root)
left_frame.pack(side="left", padx=10, pady=10)
right_frame = Frame(root)
right_frame.pack(side="right", padx=10, pady=10)

# カメラ映像用のラベル
camera_label = Label(left_frame)
camera_label.pack()

# 認識結果用のラベル
text_var = StringVar()
result_label = Label(right_frame, textvariable=text_var, font=("Helvetica", 15), wraplength=600, justify='left')  # フォントサイズを変更
result_label.pack()

def update_label(text):
    text_var.set(text)
    root.update_idletasks()

def update_camera_frame():
    global last_decoded_info, confirmation_count, confirmed_info, confirmed_slot_name, confirmed_user_name
    # カメラからフレームをキャプチャ
    im = picam2.capture_array()

    # 画像をグレースケールに変換
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

    # ノイズを軽減するために画像をぼかす
    blurred = cv2.medianBlur(gray, 3)

    # OCRを使って画像からテキストを抽出
    data = pytesseract.image_to_data(blurred, lang='eng', output_type=pytesseract.Output.DICT)

    # デバッグ用に抽出されたテキストを出力
    # print("Extracted Text Data:")
    # print(data)

    # 受付番号を特定
    match = None
    for i, text in enumerate(data['text']):
        if re.match(r'\b\d{7}\b', text):
            match = text
            (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
            cv2.rectangle(im, (x, y), (x + w, y + h), (0, 255, 0), 2)
            break

    if match:
        dec_inf = match
        print(f"Extracted Number: {dec_inf}")

        # デコードされた情報の確認プロセス
        if dec_inf == last_decoded_info:
            confirmation_count += 1
        else:
            last_decoded_info = dec_inf
            confirmation_count = 1

        if confirmation_count >= confirmation_threshold:
            confirmed_info = dec_inf
            print(f"Confirmed Number: {confirmed_info}")
            confirmation_count = 0  # Reset after confirmation

            # CSVファイル内に確認済みの受付番号が存在するかをチェック
            if confirmed_info in participants_df['受付番号'].astype(str).values:
                # 該当行を取得
                participant_row = participants_df[participants_df['受付番号'].astype(str) == confirmed_info].iloc[0]
                confirmed_slot_name = participant_row['参加枠名']
                confirmed_user_name = participant_row['表示名']
                # 該当行に「参加」を追加
                participants_df.loc[participants_df['受付番号'].astype(str) == confirmed_info, '出欠ステータス'] = '出席'
                # CSVファイルに保存
                participants_df.to_csv(csv_file_path, index=False, encoding='utf-8')
                status_message = f"受付番号: {confirmed_info}\n表示名: {confirmed_user_name}\n参加枠名: {confirmed_slot_name}\nステータス: Registered and Updated"
            else:
                confirmed_slot_name = None
                confirmed_user_name = None
                status_message = f"受付番号: {confirmed_info}\nステータス: Not Registered"

            update_label(status_message)

    # Tkinterで表示するために画像を変換
    im_rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    im_pil = Image.fromarray(im_rgb)
    im_tk = ImageTk.PhotoImage(im_pil)

    # ラベルに画像を表示
    camera_label.config(image=im_tk)
    camera_label.image = im_tk

    # 10ms後に再度フレームを更新
    root.after(10, update_camera_frame)

# 最初のフレーム更新
update_camera_frame()

# Tkinterのメインループ
root.mainloop()

# カメラとウィンドウを停止
picam2.stop()
cv2.destroyAllWindows()
