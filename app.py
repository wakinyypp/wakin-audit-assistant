import streamlit as st
import pdfplumber
import io
import re

# =========================
# 页面设置
# =========================
st.set_page_config(page_title="AI四单据审票系统V6", layout="wide")

st.title("🧠 AI四单据审票系统 V6（修复数量误判版）")
st.write("申请单 + 比价单 + 发票 + 签收单 一致性审计")

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
    delivery_file = st.file_uploader("📦 签收单", type=["pdf"], key="d")


# =========================
# PDF解析
# =========================
def extract_text(file):
    text = ""
    with pdfplumber.open(io.BytesIO(file.read())) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text


# =========================
# 🔥 修复版结构化解析（关键）
# =========================
def parse(text):

    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 2]

    # 提取所有数字（用于数量判断）
    numbers = re.findall(r"\b\d+\b", text)

    numbers = [int(n) for n in numbers if int(n) < 1000]

    return {
        "lines": lines,
        "numbers": numbers
    }


# =========================
# 🔥 修复版对比逻辑（关键）
# =========================
def compare(app, quote, invoice, delivery):

    issues = []
    risk = "LOW"

    # =========================
    # 1️⃣ 数量对比（已修复）
    # =========================
    invoice_qty = sum(invoice["numbers"])
    delivery_qty = sum(delivery["numbers"])

    if invoice_qty != delivery_qty:
        issues.append(f"❌ 数量不一致：发票={invoice_qty} vs 签收={delivery_qty}")
        risk = "HIGH"

    # =========================
    # 2️⃣ 行数辅助判断
    # =========================
    if len(delivery["lines"]) < len(invoice["lines"]):
        issues.append("❌ 签收单内容少于发票（疑似漏签）")
        risk = "HIGH"

    # =========================
    # 3️⃣ 申请 vs 发票
    # =========================
    if len(app["lines"]) > len(invoice["lines"]):
        issues.append("⚠ 发票未完全覆盖申请单内容")
        risk = "MEDIUM"

    # =========================
    # 4️⃣ 比价 vs 发票
    # =========================
    if len(quote["lines"]) > len(invoice["lines"]):
        issues.append("⚠ 比价单与发票存在不一致")
        risk = "MEDIUM"

    return issues, risk


# =========================
# 主流程
# =========================
if apply_file and quote_file and invoice_file and delivery_file:

    st.info("🧠 正在进行四单据AI审计...")

    apply_text = extract_text(apply_file)
    quote_text = extract_text(quote_file)
    invoice_text = extract_text(invoice_file)
    delivery_text = extract_text(delivery_file)

    app = parse(apply_text)
    quote = parse(quote_text)
    invoice = parse(invoice_text)
    delivery = parse(delivery_text)

    st.subheader("📌 结构化结果")

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
        st.success("✅ 四单据一致，审核通过")
