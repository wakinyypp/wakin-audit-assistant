import streamlit as st
import fitz
import re

st.set_page_config(page_title="AI审票系统V3", layout="wide")

st.title("📊 wakin AI三单审计系统")

invoice = st.file_uploader("发票PDF", type=["pdf"])
price_order = st.file_uploader("比价/申请单PDF", type=["pdf"])
delivery = st.file_uploader("签收单PDF", type=["pdf"])


def extract_text(file):
    if file is None:
        return ""

    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""

    for page in doc:
        text += page.get_text()

    return text


def extract_numbers(text):
    return [float(x) for x in re.findall(r"\d+\.?\d*", text)]


def get_max(nums):
    return max(nums) if nums else None


if st.button("开始审票"):

    inv_text = extract_text(invoice)
    po_text = extract_text(price_order)
    del_text = extract_text(delivery)

    inv_nums = extract_numbers(inv_text)
    po_nums = extract_numbers(po_text)
    del_nums = extract_numbers(del_text)

    inv_max = get_max(inv_nums)
    po_max = get_max(po_nums)
    del_max = get_max(del_nums)

    st.subheader("📌 审计结果")

    st.write("发票最大金额:", inv_max)
    st.write("比价/申请单最大金额:", po_max)
    st.write("签收单最大数量:", del_max)

    st.divider()

    # 🔥 审计逻辑1：发票 vs 比价单
    if inv_max and po_max:
        if inv_max <= po_max:
            st.success("✔ 发票未超预算（发票 ≤ 比价单）")
        else:
            st.error("❌ 发票超预算（存在风险）")

    # 🔥 审计逻辑2：签收 vs 申请单
    if del_max and po_max:
        if del_max == po_max:
            st.success("✔ 签收数量一致")
        else:
            st.warning("⚠ 签收数量不一致（可能少货/多货）")

    # 🔥 审计逻辑3：三单一致性检查
    st.divider()

    if inv_max and po_max and del_max:
        if inv_max <= po_max and del_max == po_max:
            st.success("🎉 三单一致，审计通过")
        else:
            st.error("🚨 三单存在不一致，需要复核")
