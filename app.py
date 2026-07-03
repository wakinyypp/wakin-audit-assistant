import streamlit as st
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
import re

# =========================
# 1. OCR路径（Windows本地必须）
# =========================
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# =========================
# 2. 页面设置
# =========================
st.set_page_config(page_title="wakin的审票小助手", layout="wide")

st.title("📄 wakin的审票小助手")
st.write("上传采购单（发票 / 申请单 / 比价单 / 签收单）自动检查是否有异常")

# =========================
# 3. 文件上传
# =========================
uploaded_file = st.file_uploader("上传PDF文件", type=["pdf"])

# =========================
# 4. 提取PDF文本（优先文本，否则OCR）
# =========================
def extract_text(pdf_bytes):
    text = ""

    # ① 先尝试 pdfplumber（电子PDF）
    try:
        with pdfplumber.open(pdf_bytes) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except:
        pass

    # ② 如果没有文字 -> OCR扫描件
    if not text.strip():
        images = convert_from_bytes(pdf_bytes.read())
        for img in images:
            text += pytesseract.image_to_string(img, lang="chi_sim+eng")

    return text

# =========================
# 5. 简单规则检查（可扩展）
# =========================
def check_invoice(text):
    issues = []

    if "USD" not in text and "CNY" not in text and "EUR" not in text:
        issues.append("⚠ 未发现币种信息")

    if not re.search(r"\d{5,}", text):
        issues.append("⚠ 可能缺少订单号/编号")

    if len(text) < 50:
        issues.append("⚠ 文本识别过少，可能OCR失败")

    return issues

# =========================
# 6. 主流程
# =========================
if uploaded_file:

    st.info("正在识别中，请稍等...")

    file_bytes = uploaded_file.read()
    text = extract_text(uploaded_file)

    st.subheader("📌 识别结果")
    st.text_area("文本内容", text, height=300)

    st.subheader("🧠 审核结果")

    issues = check_invoice(text)

    if issues:
        for i in issues:
            st.warning(i)
        st.error("❌ 审核未通过，请检查单据")
    else:
        st.success("✅ 审核通过")
