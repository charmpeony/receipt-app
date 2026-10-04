# レシート家計簿・画像補正版

無料のTesseract OCRを使用します。OpenAI API・有料API・APIキーは不要です。

## 差し替え方法

ZIPを解凍し、次の5ファイルをGitHubの既存リポジトリの一番上の階層にアップロードして上書きします。

- streamlit_app.py
- receipt_processing.py（新規）
- requirements.txt
- packages.txt
- README.md

Streamlitの起動ファイルは従来どおり `streamlit_app.py` です。

## 使い方

1. レシート1枚を撮影し、JPEG・PNGをアップロード。
2. 自動で切り抜いた「読み取る範囲」を確認。
3. 欠けている場合は「手動で範囲を調整」。横・縦の範囲をスライダーで調整。
4. 横向き・逆さまなら「写真の向き」を変更。
5. 「文字を読み取る」を押し、結果の日付・金額を確認して修正。

白い紙の輪郭を検出し、遠近のゆがみを補正します。検出できなければ全体を使います。
照明むらの補正、コントラスト調整、拡大、白黒化を行い、グレー画像と白黒画像の
OCR結果を文字の信頼度で比較して採用します。信頼度は正しさを保証しません。
2枚写っている場合は大きい方だけを選ぶ可能性があります。1枚ずつ読み取ってください。
元の写真は変更しません。補正画像を外部OCR APIへ送信しません。
結果は現在のStreamlitセッションに保持され、データベースには保存されません。
新しい写真を選ぶと結果をクリアし、再読み取りは編集結果を上書きします。

## ローカル実行（Debian/Ubuntu）

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-jpn tesseract-ocr-eng
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```
