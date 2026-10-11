import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from vision import extract_books_from_spines
from isbn_lookup import lookup_isbn

st.set_page_config(page_title="Library Catalog", page_icon="📚", layout="centered")

# Establish Google Sheets connection
conn = st.connection("gsheets", type=GSheetsConnection)


def load_catalog() -> pd.DataFrame:
    # Read the first worksheet, ttl=0 ensures always fresh data
    df = conn.read(ttl=0)
    return df if df is not None and not df.empty else pd.DataFrame(columns=[
        "title", "author", "publisher", "isbn", "location", "status", "added_at"
    ])


def append_books_to_sheet(new_books_df: pd.DataFrame, location: str):
    existing_df = load_catalog()

    records = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    for _, row in new_books_df.iterrows():
        title = str(row.get("title", "")).strip()
        if not title:
            continue
        records.append({
            "title": title,
            "author": str(row.get("author", "")).strip() if pd.notna(row.get("author")) else "",
            "publisher": str(row.get("publisher", "")).strip() if pd.notna(row.get("publisher")) else "",
            "isbn": str(row.get("isbn", "")).strip() if pd.notna(row.get("isbn")) else "",
            "location": location,
            "status": "unread",
            "added_at": now_str
        })

    if records:
        df_to_add = pd.DataFrame(records)
        combined_df = pd.concat([existing_df, df_to_add], ignore_index=True)
        conn.update(data=combined_df)


# UI Tabs
st.title("📚 Library Catalog")

tab_spines, tab_isbn, tab_manual, tab_view = st.tabs([
    "📸 Shelf Spines",
    "🔍 Scan ISBN",
    "✍️ Manual",
    "📖 View Sheet"
])

# 1. BATCH SPINES TAB
with tab_spines:
    st.subheader("Snap a Shelf Row")
    st.caption("Point at 8–15 book spines and snap a picture.")
    shelf_tag = st.text_input("Shelf / Room tag", value="Sala - Prateleira 1", key="spine_loc")

    photo = st.camera_input("Take photo of spines", key="spine_cam")
    if photo:
        with st.spinner("Gemini is reading book spines..."):
            detected = extract_books_from_spines(photo.getvalue())

        if detected:
            st.success(f"Found {len(detected)} books! Review & adjust if needed:")
            df_detected = pd.DataFrame(detected)
            edited_df = st.data_editor(df_detected, num_rows="dynamic", use_container_width=True)

            if st.button("💾 Save All to Google Sheet", type="primary"):
                with st.spinner("Writing to Google Sheet..."):
                    append_books_to_sheet(edited_df, shelf_tag)
                st.balloons()
                st.success("Saved directly to her Google Sheet!")
        else:
            st.warning("Could not clearly read the spines. Try adjusting angle or lighting.")

# 2. ISBN LOOKUP TAB
with tab_isbn:
    st.subheader("Single ISBN Lookup")
    isbn_val = st.text_input("ISBN:")
    loc_val = st.text_input("Shelf / Room tag", value="Sala - Prateleira 1", key="isbn_loc")

    if st.button("Search ISBN"):
        found = lookup_isbn(isbn_val)
        if found.get("title"):
            st.success("Book identified!")
            df_s = pd.DataFrame([found])
            edited_s = st.data_editor(df_s, num_rows="dynamic", use_container_width=True)
            if st.button("Save to Google Sheet", key="save_isbn_confirm"):
                append_books_to_sheet(edited_s, loc_val)
                st.success("Saved to Google Sheet!")
        else:
            st.warning("ISBN not found. Use the manual tab to add it quickly.")

# 3. MANUAL TAB
with tab_manual:
    st.subheader("Manual Entry")
    with st.form("manual_entry", clear_on_submit=True):
        m_title = st.text_input("Title *")
        m_author = st.text_input("Author")
        m_publisher = st.text_input("Publisher")
        m_loc = st.text_input("Shelf / Room", value="Sala - Prateleira 1")
        if st.form_submit_button("Add Book"):
            if m_title:
                df_manual = pd.DataFrame([{"title": m_title, "author": m_author, "publisher": m_publisher}])
                append_books_to_sheet(df_manual, m_loc)
                st.success(f"Added '{m_title}' to Google Sheet!")

# 4. VIEW CATALOG TAB
with tab_view:
    st.subheader("Live Google Sheet Data")
    current_catalog = load_catalog()
    if not current_catalog.empty:
        st.metric("Total Books", len(current_catalog))
        st.dataframe(current_catalog, use_container_width=True)
    else:
        st.info("The sheet is currently empty. Start snapping spines!")