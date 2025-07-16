import streamlit as st
import pandas as pd
import csv
import os

# Page setup
st.set_page_config(page_title="📬 Email Parser Viewer", layout="wide")
st.title("📬 Parsed Email Viewer")
st.markdown("Upload and explore parsed emails, grouped by thread (subject). Select threads to export them as CSV.")

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
selected_groups = []

st.subheader("📑 Email Threads")

for i, (subject, group) in enumerate(grouped, start=1):
    group = group.sort_values("__order")
    first_name = group.iloc[0].get("Name", "Unknown")
    expander_title = f"{i}. {first_name} | {subject}"

    col1, col2 = st.columns([0.05, 0.95])
    with col1:
        checked = st.checkbox("✔", key=f"select_{i}_{subject}", label_visibility="collapsed")
    with col2:
        with st.expander(expander_title):
            for j, (_, row) in enumerate(group.iterrows()):
                st.markdown(f"""
                **Name**: {row.get("Name", "")}  
                **Email**: {row.get("Email", "")}  
                **Sender**: {row.get("Sender", "")}  
                **Phone**: {row.get("Phone", "")}  
                **Reply:**  
                ```text
{row.get("Reply", "").strip()}
                ```
                """, unsafe_allow_html=True)
    
    if checked:
        selected_groups.append(group)

# Export
st.divider()
st.subheader("📤 Export")

if st.button("Export Selected Threads"):
    if not selected_groups:
        st.error("Please select at least one thread to export.")
    else:
        result_df = pd.concat(selected_groups)
        result_df = result_df.drop(columns=["__order"], errors="ignore")
        csv_data = result_df.to_csv(index=False, quoting=csv.QUOTE_ALL)
        st.download_button("⬇️ Download Exported CSV", data=csv_data, file_name="filtered_output.csv", mime="text/csv")
        st.success(f"Exported {len(result_df)} replies from {len(selected_groups)} threads.")
