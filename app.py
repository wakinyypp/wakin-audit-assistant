import streamlit as st
import pdfplumber
import re

# 页面标题
st.set_page_config(page_title="wakin的审票小助手")

st.title("🧠 wakin的审票小助手")
st.write("上传采购单据（发票 / 申请单 / 比价单 / 签收单）进行自动审票")

# 上传文件
uploaded_file = st.file_uploader("📤 上传PDF文件", type=["pdf"])

# 提取PDF文本
def extract_text(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# 风控分析逻辑（简化版）
def analyze(text):
    issues = []
    risk = "low"

    # 是否缺币种
    if not any(currency in text for currency in ["USD", "CNY", "EUR", "HKD"]):
        issues.append("❌ 发票可能缺少币种信息")
        risk = "medium"

    # 是否缺型号（简单识别）
    if not re.search(r"[A-Z]{2,}-?\d+", text):
        issues.append("❌ 可能缺少标准型号信息")
        risk = "medium"

    # 是否像发票
    if "invoice" not in text.lower() and "发票" not in text:
        issues.append("⚠️ 未识别到明显发票字段")

    status = "pass" if len(issues) == 0 else "review"

    return status, risk, issues


# 主流程
if uploaded_file:

    st.subheader("📄 识别中...")

    text = extract_text(uploaded_file)

    st.text_area("📄 文本内容", text, height=250)

    if st.button("🧠 开始审票"):

        status, risk, issues = analyze(text)

        st.subheader("📊 审核结果")

        if status == "pass":
            st.success("✔ 审核通过")
        else:
            st.error("❌ 需要人工复核")

        st.write("⚠️ 风险等级：", risk)

        if issues:
            st.write("### 问题列表：")
            for i in issues:
                st.write(i)
