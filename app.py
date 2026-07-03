import streamlit as st
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
import io
import re

# =========================
# 如果你本地有tesseract，需要写路径（Streamlit云端不用）
# =========================
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

st.set_page_config(page_title="AI四单据审票系统V7", layout="wide")

st.title("🧠 AI四单据审票系统 V7（OCR增强版）")
st.write("支持扫描件 + PDF文字 + 自动识别签收单")

# =========================
# 上传文件
# =========================
col1, col2, col3, col4 = st.columns(4)

with col1:
    apply_file = st.file_uploader("📄 申请单", type=["pdf"], key="a")

with col2:
    quote_file = st.file_uploader("📄 比价单", type=["pdf"], key="b")

with col3:
    invoice_file = st.file_uploader("📄 发票", type=["pdf"], key="c")

with col4:
    delivery_file = st.file_uploader("📦 签收单(扫描件支持)", type=["pdf"], key="d")


# =========================
# 1️⃣ 文字PDF提取
# =========================
def extract_text_pdf(file):
    text = ""
    with pdfplumber.open(io.BytesIO(file.read())) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text


# =========================
# 2️⃣ OCR识别（扫描件）
# =========================
def extract_text_ocr(file):
    images = convert_from_bytes(file.read())
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img, lang="eng+chi_sim") + "\n"
    return text


# =========================
# 3️⃣ 智能提取（核心）
# =========================
def extract_text(file):
    text = extract_text_pdf(file)

    # 如果PDF没有文字 → OCR
    if len(text.strip()) < 10:
        st.info("🔍 检测到扫描件，启用OCR识别...")
        file.seek(0)
        text = extract_text_ocr(file)

    return text


# =========================
# 4️⃣ 解析
# =========================
def parse(text):

    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 2]

    numbers = re.findall(r"\b\d+\b", text)
    numbers = [int(n) for n in numbers if int(n) < 1000]

    return {
        "lines": lines,
        "numbers": numbers
    }


# =========================
# 5️⃣ 对比逻辑
# =========================
def compare(app, quote, invoice, delivery):

    issues = []
    risk = "LOW"

    invoice_qty = sum(invoice["numbers"])
    delivery_qty = sum(delivery["numbers"])

    if invoice_qty != delivery_qty:
        issues.append(f"❌ 数量不一致：发票={invoice_qty} vs 签收={delivery_qty}")
        risk = "HIGH"

    if len(delivery["lines"]) < len(invoice["lines"]):
        issues.append("❌ 签收单缺失内容（可能漏签）")
        risk = "HIGH"

    return issues, risk


# =========================
# 主流程
# =========================
if apply_file and quote_file and invoice_file and delivery_file:

    st.info("🧠 正在进行AI四单据审计（含OCR）...")

    apply_text = extract_text(apply_file)
    quote_text = extract_text(quote_file)
    invoice_text = extract_text(invoice_file)
    delivery_text = extract_text(delivery_file)

    app = parse(apply_text)
    quote = parse(quote_text)
    invoice = parse(invoice_text)
    delivery = parse(delivery_text)

    st.subheader("📌 OCR/解析结果")

    st.json({
        "申请单": app,
        "比价单": quote,
        "发票": invoice,
        "签收单": delivery
    })

    st.subheader("🧠 审计结果")

    issues, risk = compare(app, quote, invoice, delivery)

    st.write("### 🚨 风险等级：", risk)

    if issues:
        for i in issues:
            st.warning(i)
        st.error("❌ 建议人工复核")
    else:
        st.success("✅ 审核通过")
