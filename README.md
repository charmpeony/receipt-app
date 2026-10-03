# レシート家計簿

Streamlit app for uploading smartphone receipt photos, previewing them, and
reading Japanese and English text using free, local Tesseract OCR. No OpenAI
API, paid API, or API key is required.

## Use

1. Open the app on your smartphone or computer and upload a JPEG or PNG photo.
   Convert HEIC photos to JPEG first. Smartphone photo orientation is applied
   automatically.
2. Check the preview and select **文字を読み取る** to run OCR.
3. Review and edit the text in **読み取り結果（編集できます）**.
   Edits stay in the current Streamlit session. Running OCR again replaces them;
   uploading a different receipt clears them. Text is not saved to a database.

For best results, photograph a single receipt straight on in good light. OCR
can misread dates and amounts, so check the result before using it.

## Streamlit Community Cloud

Deploy this repository with `streamlit_app.py` as the entry point. Keep
`requirements.txt` and `packages.txt` in the repository root. Community Cloud
installs the Python dependencies and the Tesseract engine with Japanese and
English language packs from these files. No secrets are needed.

## Run locally (Debian/Ubuntu)

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-jpn tesseract-ocr-eng
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

On other operating systems, install Tesseract and its `jpn` and `eng` language
data with your package manager and ensure `tesseract` is on your PATH.
