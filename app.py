import streamlit as st
import pandas as pd
import csv
import os
import io
import xlsxwriter

# Page setup
st.set_page_config(page_title="📬 Email Parser Viewer", layout="wide")
st.title("📬 Parsed Email Viewer")
st.markdown("Upload and explore parsed emails, grouped by thread (subject). Select threads to export them as CSV, Excel, or Notepad.")

# Load CSV
uploaded_file = st.file_uploader("📥 Upload a parsed CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("Uploaded file loaded successfully.")
elif os.path.exists("output.csv"):
    df = pd.read_csv("output.csv")
    st.info("Loaded `output.csv` from local folder.")
else:
    st.warning("No file uploaded and `output.csv` not found.")
    st.stop()

# Preprocess
df["__order"] = range(len(df))  # Preserve original order
df["Subject"] = df.get("Subject", "No Subject").fillna("No Subject")

# Group by thread
grouped = df.groupby("Subject", sort=False)

# --- 📤 Export Section (Top of Page) ---
st.subheader("📤 Export Options")

export_format = st.radio(
    "Choose export format:",
    ["CSV", "Excel (.xlsx)", "Notepad (.txt)"],
    horizontal=True
)

export_now = st.button("📤 Export Selected Threads")

# Placeholder for download button
download_placeholder = st.empty()

# Collect selected groups whether or not export is pressed
selected_groups = []
for i, (subject, group) in enumerate(grouped, start=1):
    if st.session_state.get(f"select_{i}", False):
        selected_groups.append(group)

# Prepare result_df only if exporting
result_df = None
if export_now:
    if not selected_groups:
        st.error("Please select at least one thread to export.")
    else:
        result_df = pd.concat(selected_groups).drop(columns=["__order"], errors="ignore")
        st.success(f"✅ Exported {len(result_df)} replies from {len(selected_groups)} threads.")

# --- 📎 Download Button ---
if result_df is not None:
    if export_format == "CSV":
        csv_data = result_df.to_csv(index=False, quoting=csv.QUOTE_ALL)
        download_placeholder.download_button("⬇️ Download CSV", data=csv_data,
                                             file_name="filtered_output.csv", mime="text/csv")

    elif export_format == "Excel (.xlsx)":
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            result_df.to_excel(writer, index=False, sheet_name='Emails')
        excel_buffer.seek(0)
        download_placeholder.download_button("⬇️ Download Excel File", data=excel_buffer.getvalue(),
                                             file_name="filtered_output.xlsx",
                                             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    elif export_format == "Notepad (.txt)":
        txt_output = ""
        for _, row in result_df.iterrows():
            txt_output += f"Name: {row.get('Name', '')}\n"
            txt_output += f"Email: {row.get('Email', '')}\n"
            txt_output += f"Sender: {row.get('Sender', '')}\n"
            txt_output += f"Subject: {row.get('Subject', '')}\n"
            txt_output += f"Reply:\n{row.get('Reply', '').strip()}\n"
            txt_output += "-" * 40 + "\n"
        download_placeholder.download_button("⬇️ Download Notepad File", data=txt_output,
                                             file_name="filtered_output.txt", mime="text/plain")
else:
    download_placeholder.empty()

# --- 🔍 Search Section ---
st.subheader("🔍 Search Threads")
search_query = st.text_input("Search by subject or name:", "").strip().lower()

# --- 📑 Email Threads Section ---
st.subheader("📑 Email Threads")
for i, (subject, group) in enumerate(grouped, start=1):
    group = group.sort_values("__order")
    first_name = group.iloc[0].get("Name", "Unknown")
    
    # Filter based on search query
    searchable_text = f"{first_name} {subject}".lower()
    if search_query and search_query not in searchable_text:
        continue

    expander_title = f"{i}. {first_name} | {subject} ({len(group)} replies)"

    col1, col2 = st.columns([0.05, 0.95])
    with col1:
        st.checkbox("✔", key=f"select_{i}", label_visibility="collapsed")
    with col2:
        with st.expander(expander_title, expanded=False):
            for _, row in group.iterrows():
                st.markdown(f"""
**Name**: {row.get("Name", "")}  
**Email**: {row.get("Email", "")}  
**Sender**: {row.get("Sender", "")}  
**Reply:**  
```text
{row.get("Reply", "").strip()}
```""", unsafe_allow_html=True)
