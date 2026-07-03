import streamlit as st
from pdf2image import convert_from_bytes
from paddleocr import PaddleOCR
import re
from PIL import Image
import numpy as np

st.set_page_config(page_title="审票助手V2", layout="wide")

st.title("📄 wakin AI审票助手（云端稳定版）")

invoice = st.file_uploader("发票", type=["pdf"])
order = st.file_uploader("申请单", type=["pdf"])
delivery = st.file_uploader("签收单", type=["pdf"])

ocr = PaddleOCR(use_angle_cls=True, lang="ch")


def pdf_to_text(file):
    if file is None:
        return ""

    images = convert_from_bytes(file.read(), dpi=200)

    text_all = ""

    for img in images:
        img = np.array(img)
        result = ocr.ocr(img, cls=True)

        for line in result[0]:
            text_all += line[1][0] + "\n"

    return text_all


def extract_numbers(text):
    return re.findall(r"\d+\.?\d*", text)


if st.button("开始审票"):

    inv_text = pdf_to_text(invoice)
    ord_text = pdf_to_text(order)
    del_text = pdf_to_text(delivery)

    inv_num = extract_numbers(inv_text)
    ord_num = extract_numbers(ord_text)
    del_num = extract_numbers(del_text)

    st.subheader("识别结果")

    st.write("发票：", inv_num)
    st.write("申请单：", ord_num)
    st.write("签收单：", del_num)

    if inv_num and ord_num:
        if max(inv_num) == max(ord_num):
            st.success("✔ 发票一致")
        else:
            st.error("❌ 发票不一致")

    if del_num and ord_num:
        if max(del_num) == max(ord_num):
            st.success("✔ 签收单一致")
        else:
            st.warning("⚠ 签收单不一致")
