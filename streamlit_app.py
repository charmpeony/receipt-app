import hashlib
from io import BytesIO

import pytesseract
import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError
from receipt_processing import crop_receipt, prepare_receipt, recognize

st.set_page_config(page_title='レシート家計簿', page_icon='🧾')
st.title('🧾 レシート家計簿')
st.write('スマートフォンで撮影したレシートの写真を選んでください。')
st.caption('JPEG・PNG対応。レシートは1枚ずつ撮影してください。HEICはJPEGに変換してください。')
receipt = st.file_uploader('レシート画像', type=['jpg', 'jpeg', 'png'])
if receipt is None:
    for key in ('receipt_id', 'ocr_text', 'ocr_complete', 'ocr_image'):
        st.session_state.pop(key, None)
    st.stop()

image_bytes = receipt.getvalue()
receipt_id = hashlib.sha256(image_bytes).hexdigest()
if st.session_state.get('receipt_id') != receipt_id:
    st.session_state.update(receipt_id=receipt_id, ocr_text='', ocr_complete=False)
    st.session_state.pop('ocr_image', None)
try:
    with Image.open(BytesIO(image_bytes)) as source:
        image = ImageOps.exif_transpose(source).convert('RGB')
        # Bound large phone photographs before contour detection.
        image.thumbnail((4500, 4500))
except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
    st.error('画像を開けませんでした。JPEGまたはPNGを選び直してください。')
    st.stop()
st.image(image, caption='読み込んだ写真', width='stretch')
mode = st.radio('レシートの切り抜き', ['自動', '手動で範囲を調整', '切り抜かない'])
rotation = st.selectbox('写真の向き', [0, 90, 180, 270], format_func=lambda n: f'{n}度回転')
if rotation:
    image = image.rotate(rotation, expand=True)
if mode == '自動':
    cropped, found = crop_receipt(image)
    if found:
        st.caption('レシート部分を検出し、斜めの形を補正しました。文字が欠けていないか確認してください。')
    else:
        st.info('レシートの輪郭を検出できなかったため、写真全体を使います。必要なら手動で範囲を調整してください。')
elif mode == '手動で範囲を調整':
    left, right = st.slider('横の範囲（％）', 0, 100, (0, 100), key=f'x_{receipt_id}')
    top, bottom = st.slider('縦の範囲（％）', 0, 100, (0, 100), key=f'y_{receipt_id}')
    if left == right or top == bottom:
        st.warning('範囲に幅と高さを持たせてください。')
        st.stop()
    w, h = image.size
    cropped = image.crop((int(w*left/100), int(h*top/100), int(w*right/100), int(h*bottom/100)))
else:
    cropped = image
st.image(cropped, caption='読み取る範囲', width='stretch')
with st.expander('白黒補正のプレビュー'):
    _, binary = prepare_receipt(cropped)
    st.image(binary, caption='照明むら・コントラストを補正して拡大', width='stretch')
st.caption('無料のTesseractで読み取ります。補正画像を外部OCR APIへ送信しません。')
if st.button('文字を読み取る', type='primary'):
    try:
        with st.spinner('画像を補正して文字を読み取っています…'):
            text, selected = recognize(cropped, pytesseract)
        st.session_state.update(ocr_text=text, ocr_complete=True, ocr_image=selected)
        if not text.strip():
            st.warning('文字が見つかりませんでした。撮り直すか、手入力してください。')
    except pytesseract.TesseractNotFoundError:
        st.error('Tesseractが見つかりません。packages.txtの設定を確認してください。')
    except pytesseract.TesseractError:
        st.error('読み取りに失敗しました。日本語・英語の言語データと画像を確認してください。')
    except RuntimeError:
        st.error('読み取りがタイムアウトしました。レシート1枚の範囲に絞って再度お試しください。')
st.text_area('読み取り結果（編集できます）', key='ocr_text', height=300,
    help='再度読み取ると編集内容が置き換わります。')
if st.session_state.get('ocr_complete'):
    st.caption('日付・金額を確認して修正してください。結果は現在の画面内に保持され、データベースには保存されません。')
    with st.expander('前回の読み取りに使った補正画像'):
        st.image(st.session_state['ocr_image'], width='stretch')
