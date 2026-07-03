import streamlit as st
import fitz  # PyMuPDF
import re

st.set_page_config(page_title="审票系统（稳定版）", layout="wide")

st.title("📄 wakin审票系统（云端稳定版）")

invoice = st.file_uploader("发票PDF", type=["pdf"])
order = st.file_uploader("申请单PDF", type=["pdf"])
delivery = st.file_uploader("签收单PDF", type=["pdf"])


# ✅ 只提取PDF文字（不做OCR）
def extract_text(pdf_file):
    if pdf_file is None:
        return ""

    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

    text = ""
    for page in doc:
        text += page.get_text()

    return text


# 提取数字
def extract_numbers(text):
    return re.findall(r"\d+\.?\d*", text)


if st.button("开始审票"):

    inv_text = extract_text(invoice)
    ord_text = extract_text(order)
    del_text = extract_text(delivery)

    inv_num = extract_numbers(inv_text)
    ord_num = extract_numbers(ord_text)
    del_num = extract_numbers(del_text)

    st.subheader("识别结果")

    st.write("发票数字：", inv_num)
    st.write("申请单数字：", ord_num)
    st.write("签收单数字：", del_num)

    # 发票 vs 申请单
    if inv_num and ord_num:
        if max(inv_num) == max(ord_num):
            st.success("✔ 发票金额一致")
        else:
            st.error("❌ 发票金额不一致")

    # 签收单 vs 申请单
    if del_num and ord_num:
        if max(del_num) == max(ord_num):
            st.success("✔ 签收单数量一致")
        else:
            st.warning("⚠ 签收单不一致")
