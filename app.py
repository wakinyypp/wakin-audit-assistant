import streamlit as st
import pytesseract
import fitz  # PyMuPDF
import io
import re
from PIL import Image

st.set_page_config(page_title="AI审票稳定版V8", layout="wide")

st.title("🧠 AI四单据审票系统 V8（云端稳定版）")


# =========================
# 上传
# =========================
col1, col2, col3, col4 = st.columns(4)

with col1:
    apply_file = st.file_uploader("📄 申请单", type=["pdf"])

with col2:
    quote_file = st.file_uploader("📄 比价单", type=["pdf"])

with col3:
    invoice_file = st.file_uploader("📄 发票", type=["pdf"])

with col4:
    delivery_file = st.file_uploader("📦 签收单", type=["pdf"])


# =========================
# PDF提取文字（优先）
# =========================
def extract_text_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text


# =========================
# OCR（稳定版，无poppler）
# =========================
def extract_text_ocr(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""

    for page in doc:
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        text += pytesseract.image_to_string(img, lang="eng+chi_sim") + "\n"

    return text


# =========================
# 智能识别
# =========================
def extract_text(file):
    text = extract_text_pdf(file)

    if len(text.strip()) < 10:
        st.info("🔍 使用OCR识别扫描件...")
        file.seek(0)
        text = extract_text_ocr(file)

    return text


# =========================
# 解析
# =========================
def parse(text):
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 2]
    numbers = re.findall(r"\b\d+\b", text)
    numbers = [int(n) for n in numbers if int(n) < 1000]

    return {"lines": lines, "numbers": numbers}


# =========================
# 对比
# =========================
def compare(invoice, delivery):
    issues = []
    risk = "LOW"

    inv_qty = sum(invoice["numbers"])
    del_qty = sum(delivery["numbers"])

    if inv_qty != del_qty:
        issues.append(f"❌ 数量不一致：发票={inv_qty} vs 签收={del_qty}")
        risk = "HIGH"

    return issues, risk


# =========================
# 主流程
# =========================
if apply_file and quote_file and invoice_file and delivery_file:

    st.info("🧠 正在处理四单据...")

    invoice_text = extract_text(invoice_file)
    delivery_text = extract_text(delivery_file)

    invoice = parse(invoice_text)
    delivery = parse(delivery_text)

    st.json({
        "发票": invoice,
        "签收单": delivery
    })

    issues, risk = compare(invoice, delivery)

    st.write("### 风险：", risk)

    if issues:
        for i in issues:
            st.warning(i)
    else:
        st.success("通过")
