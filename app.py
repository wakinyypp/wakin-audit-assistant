import streamlit as st
import pdfplumber
import pytesseract
from PIL import Image
import io
import re

# =========================
# 1. OCR路径（本地Windows用）
# 云端会自动忽略，不影响运行
# =========================
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# =========================
# 2. 页面设置
# =========================
st.set_page_config(page_title="wakin的审票小助手", layout="wide")

st.title("📄 wakin的审票小助手（云端稳定版）")
st.write("上传PDF（发票 / 申请单 / 比价单 / 签收单）自动检查")

# =========================
# 3. 上传文件
# =========================
uploaded_file = st.file_uploader("上传PDF文件", type=["pdf"])

# =========================
# 4. 稳定PDF解析（核心优化）
# 👉 不使用 pdf2image！
# =========================
def extract_text(pdf_file):
    text = ""

    # ① 先尝试文本型PDF
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        st.warning(f"PDF解析异常: {e}")

    return text


# =========================
# 5. OCR备用（仅对“单页图片PDF”兜底）
# =========================
def simple_ocr_fallback(uploaded_file):
    try:
        images = Image.open(uploaded_file)
        text = pytesseract.image_to_string(images, lang="chi_sim+eng")
        return text
    except:
        return ""


# =========================
# 6. 审核逻辑（可扩展）
# =========================
def check_invoice(text):
    issues = []

    if "USD" not in text and "CNY" not in text and "EUR" not in text:
        issues.append("⚠ 未发现币种信息")

    if not re.search(r"\d{5,}", text):
        issues.append("⚠ 可能缺少订单/编号")

    if len(text.strip()) < 30:
        issues.append("⚠ 文本识别过少（可能是扫描件）")

    return issues


# =========================
# 7. 主流程
# =========================
if uploaded_file:

    st.info("正在解析中，请稍等...")

    # 读取文件（关键：只读一次）
    file_bytes = uploaded_file.read()

    # PDF文本提取
    text = extract_text(io.BytesIO(file_bytes))

    # 如果文本为空 → OCR兜底
    if not text.strip():
        st.warning("检测为扫描件，启用OCR识别...")
        text = simple_ocr_fallback(io.BytesIO(file_bytes))

    # =========================
    # 8. 展示结果
    # =========================
    st.subheader("📌 识别结果")
    st.text_area("文本内容", text, height=300)

    st.subheader("🧠 审核结果")

    issues = check_invoice(text)

    if issues:
        for i in issues:
            st.warning(i)
        st.error("❌ 审核未通过")
    else:
        st.success("✅ 审核通过")
