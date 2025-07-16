import streamlit as st
import pandas as pd
import csv
import os

st.set_page_config(page_title="Email Reply Review", layout="wide")
st.title("📧 Email Reply Review & Export")

st.markdown("""
This app loads `output1.csv`, shows parsed replies from your exported emails,
and lets you select which ones to keep and export for use elsewhere.
""")

# Step 1: Load file
uploaded_file = st.file_uploader("📥 Upload output1.csv (optional)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
elif os.path.exists("output1.csv"):
    df = pd.read_csv("output1.csv")
    st.info("Auto-loaded local file: `output1.csv`")
else:
    st.warning("No file uploaded and `output1.csv` not found in this folder.")
    st.stop()

# Step 2: Filter out bad rows (like separator lines)
df = df.dropna(subset=['Name', 'Email', 'Reply']).copy()
df = df[~df['Name'].str.contains(r'^[-=]{3,}$', na=False)]

# Step 3: Display with checkboxes
st.subheader("✅ Select replies to export")

selected_rows = []
for i, row in df.iterrows():
    with st.expander(f"{i+1}. {row['Name']} | {row['Email']}", expanded=False):
        st.markdown(f"**🧑 Name:** {row['Name']}")
        st.markdown(f"**📨 Email:** {row['Email']}")
        st.markdown(f"**✉️ Sender:** {row['Sender']}")
        st.markdown("**📝 Reply:**")
        st.code(row['Reply'], language='text')
        if st.checkbox("Include this reply", key=f"row_{i}"):
            selected_rows.append(row)

# Step 4: Export button
if st.button("📤 Export Selected Replies"):
    if not selected_rows:
        st.error("⚠️ You didn't select any replies.")
    else:
        result_df = pd.DataFrame(selected_rows)
        result_df.to_csv("filtered_output1.csv", index=False, quoting=csv.QUOTE_ALL)
        st.success(f"✅ Exported {len(result_df)} rows to `filtered_output1.csv`.")

        st.download_button(
            label="⬇️ Download Filtered File",
            data=result_df.to_csv(index=False),
            file_name="filtered_output1.csv",
            mime="text/csv"
        )
