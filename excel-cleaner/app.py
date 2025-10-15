import io
import pandas as pd
import streamlit as st
from unidecode import unidecode

st.set_page_config(page_title="Excel Keyword Cleaner", page_icon="🧹", layout="centered")
st.title("🧹 Excel Keyword Cleaner")

st.write("Upload an Excel file where **column A** contains your keywords (with a header). "
         "This will create a cleaned version in **column B** called **Cleaned**.")

uploaded = st.file_uploader("Upload .xlsx", type=["xlsx"])

def clean_text_series(s: pd.Series) -> pd.Series:
    out = s.astype(str)
    out = out.map(unidecode)                                  # é → e, ç → c, etc.
    out = out.str.replace("'", "", regex=False)               # remove apostrophes to avoid SQL issues
    out = out.str.replace(r"[^A-Za-z0-9 ]+", "", regex=True)  # keep letters, digits, spaces only
    out = out.str.replace(r"\s+", " ", regex=True).str.strip()
    return out

if uploaded:
    try:
        df = pd.read_excel(uploaded, engine="openpyxl")
    except Exception as e:
        st.error(f"Could not read Excel file: {e}")
        st.stop()

    if df.shape[1] == 0:
        st.error("No columns found in the sheet.")
        st.stop()

    first_col_name = df.columns[0]
    cleaned = clean_text_series(df[first_col_name])

    # Insert as second column (column B)
    out_df = df.copy()
    if "Cleaned" in out_df.columns:
        out_df.drop(columns=["Cleaned"], inplace=True)
    out_df.insert(1, "Cleaned", cleaned)

    st.subheader("Preview (first 20 rows)")
    st.dataframe(out_df.head(20), use_container_width=True)

    # Prepare downloads
    # Excel
    xlsx_buf = io.BytesIO()
    with pd.ExcelWriter(xlsx_buf, engine="openpyxl") as writer:
        out_df.to_excel(writer, index=False, sheet_name="cleaned")
    xlsx_buf.seek(0)

    # CSV
    csv_bytes = out_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download cleaned Excel (.xlsx)",
        data=xlsx_buf,
        file_name="cleaned.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.download_button(
        "⬇️ Download cleaned CSV (.csv)",
        data=csv_bytes,
        file_name="cleaned.csv",
        mime="text/csv",
    )

    st.caption("Rule set: accents → ASCII, apostrophes removed, non-alphanumerics removed, spaces kept and normalised.")
else:
    st.info("Choose an .xlsx file to start.")
