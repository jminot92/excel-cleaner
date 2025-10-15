import io
import pandas as pd
import streamlit as st
from unidecode import unidecode

# --- Page setup ---
st.set_page_config(
    page_title="Foreign Text Normaliser – ASCII Converter",
    page_icon="🧩",
    layout="centered"
)

st.title("🧩 Foreign Text Normaliser – ASCII Converter")

st.markdown("""
**Purpose:**  
This tool converts foreign-language or accented characters into plain ASCII text suitable for SQL, URLs, and systems that only accept basic characters.

**How it works:**
1. Place your text or keywords in **column A**, with a **header in row 1**.  
2. Upload your Excel or CSV file.  
3. The tool adds a cleaned version in **column B** called **Cleaned**.  
4. Download your cleaned file in Excel or CSV format.

If unsure, start with the template below.
""")

# --- Template download ---
with st.expander("📄 Download an Excel template"):
    st.write("Template format: column A header is **Keywords**. Enter your text from row 2 down.")
    template_df = pd.DataFrame({
        "Keywords": [
            "qu'est-ce qu'une souris ergonomique",
            "souris ergonomique réglable à main",
            "façade naïve déjà vu café",
            "über schön groß Straße"
        ]
    })
    xlsx_buf = io.BytesIO()
    with pd.ExcelWriter(xlsx_buf, engine="openpyxl") as writer:
        template_df.to_excel(writer, index=False, sheet_name="template")
    xlsx_buf.seek(0)
    st.download_button(
        "⬇️ Download Excel template (.xlsx)",
        data=xlsx_buf,
        file_name="text_normaliser_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

uploaded = st.file_uploader("Upload your file (.xlsx or .csv)", type=["xlsx", "csv"])

# --- Core cleaning logic ---
def clean_text_series(s: pd.Series) -> pd.Series:
    out = s.astype(str)
    out = out.map(unidecode)                                  # Convert é -> e, ç -> c, etc.
    out = out.str.replace("'", "", regex=False)               # Remove apostrophes (SQL safety)
    out = out.str.replace(r"[^A-Za-z0-9 ]+", "", regex=True)  # Keep letters, digits, spaces
    out = out.str.replace(r"\s+", " ", regex=True).str.strip()
    return out

def read_any(upload):
    name = upload.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(upload)
    return pd.read_excel(upload, engine="openpyxl")

# --- Upload validation ---
if not uploaded:
    st.info("Upload a file to begin.")
    st.stop()

try:
    df = read_any(uploaded)
except Exception as e:
    st.error("Could not read your file.")
    with st.expander("Technical details"):
        st.write(str(e))
    st.stop()

if df.shape[1] == 0:
    st.error("No columns found. Ensure your data is in column A with a header.")
    st.stop()

first_col = df.columns[0]
if str(first_col).startswith("Unnamed") or str(first_col).strip() == "":
    st.error("Column A is missing a header. Add one in cell A1 and try again. Use the template if needed.")
    st.stop()

st.success(f"Detected column A header: **{first_col}**")

# --- Processing ---
try:
    cleaned = clean_text_series(df[first_col])
except Exception as e:
    st.error("Failed while cleaning text.")
    with st.expander("Technical details"):
        st.write(str(e))
    st.stop()

out_df = df.copy()
if "Cleaned" in out_df.columns:
    out_df.drop(columns=["Cleaned"], inplace=True)
out_df.insert(1, "Cleaned", cleaned)

# --- Display preview ---
st.subheader("Preview (first 20 rows)")
st.dataframe(out_df.head(20), use_container_width=True)

# --- Download options ---
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

st.caption("Rules: accents → ASCII, apostrophes removed, non-alphanumerics removed, spaces normalised.")
