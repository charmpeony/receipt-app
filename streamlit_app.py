import hashlib
from io import BytesIO

import pytesseract
import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

st.set_page_config(
    page_title="レシート家計簿",
    page_icon="🧾"
)

st.title("🧾 レシート家計簿")

st.write("スマートフォンで撮影したレシートの写真を選んでください。")
st.caption("JPEG・PNG形式に対応しています。HEIC形式の写真はJPEGに変換してください。")

receipt = st.file_uploader(
    "レシート画像",
    type=["jpg", "jpeg", "png"]
)

if receipt is not None:
    image_bytes = receipt.getvalue()
    receipt_id = hashlib.sha256(image_bytes).hexdigest()
    if st.session_state.get("receipt_id") != receipt_id:
        st.session_state["receipt_id"] = receipt_id
        st.session_state["ocr_text"] = ""
        st.session_state["ocr_complete"] = False

    try:
        # Apply smartphone EXIF orientation before previewing and reading text.
        with Image.open(BytesIO(image_bytes)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        st.error("画像を開けませんでした。JPEGまたはPNG画像を選び直してください。")
        st.stop()

    st.image(image, caption="読み込んだレシート", width="stretch")
    st.caption("無料のTesseract OCRで日本語と英語を読み取ります。画像を外部APIへ送信しません。")

    if st.button("文字を読み取る", type="primary"):
        try:
            with st.spinner("日本語・英語の文字を読み取っています…"):
                # Grayscale and automatic contrast help with receipt photographs.
                ocr_image = ImageOps.autocontrast(ImageOps.grayscale(image))
                text = pytesseract.image_to_string(
                    ocr_image, lang="jpn+eng", config="--psm 6", timeout=60
                )
            st.session_state["ocr_text"] = text.strip()
            st.session_state["ocr_complete"] = True
            if not text.strip():
                st.warning("文字が見つかりませんでした。明るく鮮明な写真で再度お試しください。手入力もできます。")
        except pytesseract.TesseractNotFoundError:
            st.error("Tesseractが見つかりません。packages.txtの設定を確認してください。")
        except pytesseract.TesseractError:
            st.error("文字の読み取りに失敗しました。日本語・英語の言語データと画像を確認してください。")
        except RuntimeError:
            st.error("読み取りがタイムアウトしました。小さな画像で再度お試しください。")

    st.text_area(
        "読み取り結果（編集できます）",
        key="ocr_text",
        height=300,
        help="読み取った文字を確認して修正してください。再度読み取りを実行すると編集内容が置き換わります。",
    )
    if st.session_state["ocr_complete"]:
        st.caption("読み取りが完了しました。金額・日付などを確認して修正してください。")
else:
    # Removing an upload must not restore an old receipt's edited text later.
    for key in ("receipt_id", "ocr_text", "ocr_complete"):
        st.session_state.pop(key, None)
