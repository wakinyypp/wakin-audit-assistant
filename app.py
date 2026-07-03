import streamlit as st
import pytesseract
import fitz  # PyMuPDF
import re
import io
from PIL import Image

# ========== 页面 ==========
st.set_page_config(page_title="企业级AI审票系统", layout="wide")
st.title("📑 企业级AI审票系统（稳定修复版 v1.1）")

st.write("支持：发票 / 比价单 / 申请单 / 签收单 自动审计比对")


# ========== OCR ==========
def ocr_image(img):
    return pytesseract.image_to_string(img, lang="chi_sim+eng")


# ========== PDF解析 ==========
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    full_text = ""

    for page in doc:
        text = page.get_text()
        full_text += text

        # 扫描件兜底OCR
        if len(text.strip()) < 20:
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            full_text += ocr_image(img)

    return full_text


# ========== 金额提取 ==========
def extract_amounts(text):
    amounts = re.findall(r"\d+\.\d{2}", text)
    cleaned = []

    for a in amounts:
        try:
            val = float(a)

            # ❗ 核心修复：过滤无效报价
            if val > 0:
                cleaned.append(val)

        except:
            continue

    return cleaned


def extract_max_amount(text):
    amounts = extract_amounts(text)
    return max(amounts) if amounts else None


# ========== 文档分类 ==========
def classify_doc(text, filename):
    if "发票" in filename or "发票" in text:
        return "invoice"
    if "比价" in filename:
        return "quote"
    if "申请" in filename:
        return "request"
    if "签收" in filename:
        return "delivery"
    return "unknown"


# ========== 处理 ==========
def process(files):
    data = {
        "invoice": [],
        "quote": [],
        "request": [],
        "delivery": []
    }

    for file in files:
        text = extract_text_from_pdf(file)
        doc_type = classify_doc(text, file.name)
        amount = extract_max_amount(text)

        data[doc_type].append({
            "name": file.name,
            "text": text,
            "amount": amount
        })

    return data


# ========== 审核逻辑 ==========
def audit(data):
    result = []

    invoice_amounts = [x["amount"] for x in data["invoice"] if x["amount"]]
    quote_amounts = [x["amount"] for x in data["quote"] if x["amount"]]

    # ❗ 核心修复：过滤 0 / None 后再计算最低价
    valid_quotes = [q for q in quote_amounts if q and q > 0]

    # =========================
    # 1️⃣ 发票 vs 比价单最低价（修复版）
    # =========================
    if invoice_amounts and valid_quotes:

        min_quote = min(valid_quotes)
        max_invoice = max(invoice_amounts)

        if abs(max_invoice - min_quote) < 0.01:
            result.append("✅ 发票金额 = 比价单最低有效报价（正常）")
        else:
            result.append("❌ 发票金额 ≠ 比价单最低有效报价（异常）")

        result.append(f"📊 有效最低比价: {min_quote}")
        result.append(f"📊 发票最高金额: {max_invoice}")

    # =========================
    # 2️⃣ 签收单逻辑（预留）
    # =========================
    if data["delivery"]:
        result.append("📦 已检测签收单（数量比对模块待升级）")

    # =========================
    # 3️⃣ 申请单
    # =========================
    if not data["request"]:
        result.append("ℹ️ 未检测到申请单金额字段（正常跳过）")

    return result


# ========== UI ==========
uploaded_files = st.file_uploader(
    "上传单据（发票 / 比价 / 申请 / 签收）",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    st.info("正在解析单据...")
    data = process(uploaded_files)

    st.success("解析完成")

    st.subheader("📊 审核结果")

    results = audit(data)
    for r in results:
        st.write(r)

    with st.expander("📦 原始识别数据"):
        st.json({
            k: [
                {"name": x["name"], "amount": x["amount"]}
                for x in v
            ]
            for k, v in data.items()
        })
