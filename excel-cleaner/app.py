import io
import pandas as pd
import streamlit as st
from unidecode import unidecode

st.set_page_config(page_title="Excel Keyword Cleaner", page_icon="🧹", layout="centered")
st.title("🧹 Excel Keyword Cleaner")

st.markdown("""
**How it works**
1. Put your keywords in **column A**, with a **header in the first row**.
2. Upload the file. We will add a cleaned version in **column B** called **Cleaned**.
3. Download the cleaned Excel or CSV.

If in doubt, use the template below.
""")

# --- Template download ---
with st.expander("Download a template"):
    st.write("Template format: column A header is **Keywords**. Enter your keywords from row 2 down.")
    template_df = pd.DataFrame({"Keywords": ["qu'est-ce qu'une souris ergonomique", "souris ergonomique réglable à main"]})
    xlsx_buf = io.BytesIO()
    with pd.ExcelWriter(xlsx_buf, engine="openpyxl") as writer:
        template_df.to_excel(writer, index=False, sheet_name="template")
    xlsx_buf.seek(0)
    st.download_button(
        "⬇️ Download Excel template (.xlsx)",
        data=xlsx_buf,
        file_name="keyword_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

uploaded = st.file_uploader("Upload your file (.xlsx or .csv)", type=["xlsx", "csv"])

def clean_text_series(s: pd.Series) -> pd.Series:
    out = s.astype(str)
    out = out.map(unidecode)                                  # é -> e
    out = out.str.replace("'", "", regex=False)               # remove apostrophes
    out = out.str.replace(r"[^A-Za-z0-9 ]+", "", regex=True)  # keep letters, digits, spaces
    out = out.str.replace(r"\s+", " ", regex=True).str.strip()
    return out

def read_any(upload):
    name = upload.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(upload)
    return pd.read_excel(upload, engine="openpyxl")

if not uploaded:
    st.info("Upload a file to begin.")
    st.stop()

# Read
try:
    df = read_any(uploaded)
except Exception as e:
    st.error("Could not read your file.")
    with st.expander("Technical details"):
        st.write(str(e))
    st.stop()

# Validate first column exists and has a header
if df.shape[1] == 0:
    st.error("No columns found. Ensure your data is in column A with a header.")
    st.stop()

first_col = df.columns[0]
if str(first_col).startswith("Unnamed") or str(first_col).strip() == "":
    st.error("Column A is missing a header. Put a header in cell A1 and try again. Use the template if needed.")
    st.stop()

st.success(f"Detected column A header: **{first_col}**")

# Clean and output
try:
    cleaned = clean_text_series(df[first_col])
except Exception as e:
    st.error("Failed while cleaning the first column.")
    with st.expander("Technical details"):
        st.write(str(e))
    st.stop()

out_df = df.copy()
if "Cleaned" in out_df.columns:
    out_df.drop(columns=["Cleaned"], inplace=True)
out_df.insert(1, "Cleaned", cleaned)

st.subheader("Preview (first 20 rows)")
st.dataframe(out_df.head(20), use_container_width=True)

# Downloads
xlsx_out = io.BytesIO()
with pd.ExcelWriter(xlsx_out, engine="openpyxl") as writer:
    out_df.to_excel(writer, index=False, sheet_name="cleaned")
xlsx_out.seek(0)

st.download_button(
    "⬇️ Download cleaned Excel (.xlsx)",
    data=xlsx_out,
    file_name="cleaned.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

csv_out = out_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download cleaned CSV (.csv)",
    data=csv_out,
    file_name="cleaned.csv",
    mime="text/csv",
)

st.caption("Rules: accents to ASCII, apostrophes removed, non-alphanumerics removed, spaces normalised.")
