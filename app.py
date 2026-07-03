import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import re
import io

# =============================
# ⚙️ 基础配置（云端安全模式）
# =============================
st.set_page_config(page_title="企业级AI审票系统", layout="wide")

st.title("📊 企业级AI审票系统（稳定修复版）")

# ⚠️ 云端兼容：不强依赖本地tesseract路径
# 如果云端有tesseract，会自动用；没有也不会直接崩
try:
    pytesseract.get_tesseract_version()
except:
    st.warning("⚠️ 当前环境可能未安装Tesseract，OCR功能可能受限")


# =============================
# OCR识别（图片）
# =============================
def ocr_image(image: Image.Image):
    try:
        text = pytesseract.image_to_string(image, lang="eng")
        return text
    except Exception as e:
        return f"[OCR失败] {str(e)}"


# =============================
# PDF解析（核心稳定方案）
# =============================
def extract_pdf(file):
    text = ""

    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")

        for page in doc:
            page_text = page.get_text()

            # 如果PDF是扫描件（无文本）
            if len(page_text.strip()) < 20:
                pix = page.get_pixmap()
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                page_text = ocr_image(img)

            text += page_text + "\n"

    except Exception as e:
        return f"[PDF解析失败] {str(e)}"

    return text


# =============================
# 数字提取（金额/数量）
# =============================
def extract_numbers(text):
    nums = re.findall(r"\d+\.?\d*", text)
    return [float(n) for n in nums if len(n) < 10]


# =============================
# 单据解析
# =============================
def analyze_documents(files):
    results = {}

    for file in files:
        name = file.name

        if name.lower().endswith(".pdf"):
            text = extract_pdf(file)
        else:
            image = Image.open(file)
            text = ocr_image(image)

        numbers = extract_numbers(text)

        results[name] = {
            "text": text,
            "numbers": numbers,
            "max": max(numbers) if numbers else 0,
            "count": len(numbers)
        }

    return results


# =============================
# 企业级审票逻辑（稳定版）
# =============================
def audit(results):

    invoice = None
    request = None
    quote = None
    sign = None

    for name, data in results.items():
        if "发票" in name:
            invoice = data
        elif "申请" in name:
            request = data
        elif "比价" in name:
            quote = data
        elif "签收" in name:
            sign = data

    report = []

    # -------------------------
    # 1. 发票 vs 申请单
    # -------------------------
    if invoice and request:
        if invoice["max"] == request["max"]:
            report.append("✅ 发票金额 = 申请单金额")
        else:
            report.append("❌ 发票金额 ≠ 申请单金额")

    # -------------------------
    # 2. 发票 vs 比价单
    # -------------------------
    if invoice and quote:
        if invoice["max"] <= quote["max"]:
            report.append("✅ 发票金额在比价范围内")
        else:
            report.append("⚠ 发票金额高于比价最低价（异常）")

    # -------------------------
    # 3. 签收单校验（你新增需求）
    # -------------------------
    if invoice and sign:
        if invoice["count"] == sign["count"]:
            report.append("✅ 签收数量与发票一致")
        else:
            report.append("❌ 签收数量与发票不一致（可能短收/漏收）")

    # -------------------------
    # 4. 默认兜底
    # -------------------------
    if not report:
        report.append("⚠ 未识别到完整单据，请检查文件命名（发票/申请/比价/签收）")

    return report


# =============================
# UI
# =============================
uploaded_files = st.file_uploader(
    "上传单据（发票 / 申请单 / 比价单 / 签收单）",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:

    st.info("📄 正在解析单据，请稍候...")

    results = analyze_documents(uploaded_files)

    st.success("✔ 解析完成")

    st.subheader("📊 审核结果")

    report = audit(results)

    for r in report:
        st.write(r)

    st.subheader("🔍 识别详情")

    for name, data in results.items():
        with st.expander(name):
            st.write("📌 数字识别：", data["numbers"])
            st.text(data["text"][:1500])
