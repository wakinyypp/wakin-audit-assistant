import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re

# 页面配置
st.set_page_config(page_title="wakin的审票小助手", layout="wide")

st.title("📄 wakin的审票小助手")
st.write("上传采购单 / 签收单 / 发票进行自动比对")

# 上传文件
invoice_file = st.file_uploader("上传发票", type=["pdf"])
order_file = st.file_uploader("上传申请单/比价单", type=["pdf"])
delivery_file = st.file_uploader("上传签收单", type=["pdf"])


# PDF转图片（稳定版：PyMuPDF）
def pdf_to_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images


# OCR识别
def ocr_image(img):
    text = pytesseract.image_to_string(img, lang="chi_sim+eng")
    return text


# 提取数字（金额/数量）
def extract_numbers(text):
    nums = re.findall(r"\d+\.?\d*", text)
    return [float(n) for n in nums]


# 主逻辑
def process(pdf_file):
    if pdf_file is None:
        return None, None

    images = pdf_to_images(pdf_file.read())

    full_text = ""
    for img in images:
        full_text += ocr_image(img)

    numbers = extract_numbers(full_text)

    return full_text, numbers


if st.button("开始审票"):

    invoice_text, invoice_nums = process(invoice_file)
    order_text, order_nums = process(order_file)
    delivery_text, delivery_nums = process(delivery_file)

    st.subheader("识别结果")

    st.write("发票数字：", invoice_nums)
    st.write("申请单数字：", order_nums)
    st.write("签收单数字：", delivery_nums)

    # 简单对比逻辑
    if invoice_nums and order_nums:
        if max(invoice_nums) == max(order_nums):
            st.success("✔ 发票与申请单金额一致")
        else:
            st.error("❌ 发票与申请单金额不一致")

    # 签收单校验（新增）
    if delivery_nums and order_nums:
        if max(delivery_nums) == max(order_nums):
            st.success("✔ 签收单数量一致")
        else:
            st.warning("⚠ 签收单与申请单可能不一致，请复核")
