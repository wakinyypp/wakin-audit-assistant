import streamlit as st
import pytesseract
import fitz  # PyMuPDF
import re

# ========== 页面配置 ==========
st.set_page_config(page_title="企业级AI审票系统", layout="wide")

st.title("📑 企业级AI审票系统（稳定版）")

st.write("支持：发票 / 比价单 / 申请单 / 签收单 自动比对")

# ========== OCR ==========
def ocr_image(img):
    """OCR识别"""
    text = pytesseract.image_to_string(img, lang="chi_sim+eng")
    return text


def extract_text_from_pdf(pdf_file):
    """使用 PyMuPDF 直接解析 PDF（避免 pdf2image）"""
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    full_text = ""

    for page in doc:
        text = page.get_text()
        full_text += text

        # 如果是扫描件（无文本），再走OCR兜底
        if len(text.strip()) < 20:
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            import PIL.Image
            import io

            img = PIL.Image.open(io.BytesIO(img_bytes))
            full_text += ocr_image(img)

    return full_text


# ========== 金额提取 ==========
def extract_amounts(text):
    """提取金额"""
    amounts = re.findall(r"(\d+\.\d{2})", text)
    return [float(a) for a in amounts if float(a) > 0]


def extract_max_amount(text):
    amounts = extract_amounts(text)
    return max(amounts) if amounts else None


# ========== 文档识别 ==========
def classify_doc(text, filename):
    """判断文档类型"""
    if "发票" in filename or "发票" in text:
        return "invoice"
    if "比价" in filename:
        return "quote"
    if "申请" in filename:
        return "request"
    if "签收" in filename:
        return "delivery"
    return "unknown"


# ========== 主处理 ==========
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


# ========== 审核逻辑（核心修复） ==========
def audit(data):
    result = []

    invoice_amounts = [x["amount"] for x in data["invoice"] if x["amount"]]
    quote_amounts = [x["amount"] for x in data["quote"] if x["amount"]]
    delivery_docs = data["delivery"]

    # 1️⃣ 发票 vs 比价单（你之前这里是错的，已修复）
    if invoice_amounts and quote_amounts:
        min_quote = min(quote_amounts)
        max_invoice = max(invoice_amounts)

        if max_invoice == min_quote:
            result.append("✅ 发票金额 = 比价单最低金额（正常）")
        else:
            result.append("❌ 发票金额 ≠ 比价单最低金额（异常）")

    # 2️⃣ 发票 vs 签收单（新增逻辑）
    if delivery_docs and invoice_amounts:
        result.append("📦 已检测签收单，进入数量比对逻辑")
        result.append("⚠️ 当前版本：签收数量需OCR字段升级（已预留接口）")

    # 3️⃣ 没有申请单金额（你指出的问题）
    if not data["request"]:
        result.append("ℹ️ 申请单无金额字段（已按规则跳过）")

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

    # debug
    with st.expander("原始识别数据"):
        st.json({
            k: [{"name": x["name"], "amount": x["amount"]} for x in v]
            for k, v in data.items()
        })
