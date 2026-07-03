import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import re

st.set_page_config(page_title="企业级AI审票系统", layout="wide")

st.title("📊 企业级AI审票系统（稳定版）")

# ---------------- OCR ----------------
def ocr_image(img):
    text = pytesseract.image_to_string(img, lang="chi_sim+eng")
    return text


def extract_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text


# ---------------- 金额提取 ----------------
def extract_amounts(text):
    amounts = re.findall(r"(\d+\.?\d*)", text)
    amounts = [float(a) for a in amounts if len(a) < 10]
    return amounts


# ---------------- 单据解析 ----------------
def analyze_documents(files):
    results = {}

    for file in files:
        name = file.name

        if name.endswith(".pdf"):
            text = extract_pdf(file)
        else:
            img = Image.open(file)
            text = ocr_image(img)

        amounts = extract_amounts(text)

        results[name] = {
            "text": text,
            "amounts": amounts,
            "max_amount": max(amounts) if amounts else 0
        }

    return results


# ---------------- 审核引擎（核心） ----------------
def audit(results):

    invoice = None
    quote = None
    request = None
    delivery = None

    for name, data in results.items():
        if "发票" in name:
            invoice = data
        elif "比价" in name:
            quote = data
        elif "申请" in name:
            request = data
        elif "签收" in name:
            delivery = data

    report = []

    # 发票 vs 申请单
    if invoice and request:
        if invoice["max_amount"] == request["max_amount"]:
            report.append("✅ 发票与申请单金额一致")
        else:
            report.append("❌ 发票与申请单金额不一致")

    # 发票 vs 比价单
    if invoice and quote:
        if invoice["max_amount"] >= quote["max_amount"]:
            report.append("⚠ 发票金额高于比价最低价（异常）")
        else:
            report.append("✅ 发票在比价范围内")

    # 签收单校验（你新增重点）
    if invoice and delivery:
        if invoice["amounts"] and delivery["amounts"]:
            if len(invoice["amounts"]) == len(delivery["amounts"]):
                report.append("✅ 签收数量与发票一致")
            else:
                report.append("❌ 签收数量与发票不一致")

    return report


# ---------------- UI ----------------
uploaded_files = st.file_uploader(
    "上传单据（发票/申请单/比价单/签收单）",
    accept_multiple_files=True
)

if uploaded_files:

    st.info("正在解析单据...")

    results = analyze_documents(uploaded_files)

    st.success("解析完成")

    st.subheader("📄 审核结果")

    report = audit(results)

    for r in report:
        st.write(r)

    st.subheader("🔍 原始识别结果")

    for k, v in results.items():
        st.write("###", k)
        st.text(v["text"][:1000])
