import streamlit as st

st.set_page_config(
    page_title="レシート家計簿",
    page_icon="🧾"
)

st.title("🧾 レシート家計簿")

st.write("レシートを撮影するか、写真を選んでください。")

receipt = st.file_uploader(
    "レシート画像",
    type=["jpg", "jpeg", "png"]
)

if receipt is not None:
    st.image(
        receipt,
        caption="読み込んだレシート",
        use_container_width=True
    )
    st.success("レシートを読み込めました！")
