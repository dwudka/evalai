import streamlit as st
from campwatcher import api
from ranking import difficulty_score
from campground_data import CAMPGROUND_ATTRIBUTES

st.set_page_config(page_title="Campsite Finder", page_icon="\U0001F3D5")
st.title("Campsite Finder")

query = st.text_input("Search")
col1, col2 = st.columns(2)
with col1:
    latitude = st.text_input("Latitude", placeholder="Optional")
with col2:
    longitude = st.text_input("Longitude", placeholder="Optional")

filters = st.sidebar
filters.header("Filters")
tent_only = filters.checkbox("Tent only")
no_rv = filters.checkbox("No RV")

if st.button("Search"):
    if not query:
        st.warning("Enter a search term.")
    else:
        results = api.fetch_campgrounds(query, latitude or None, longitude or None)
        display = []
        for camp in results:
            cid = str(camp.get("FacilityID"))
            attrs = CAMPGROUND_ATTRIBUTES.get(cid, {})
            if tent_only and not attrs.get("tent_only"):
                continue
            if no_rv and not attrs.get("no_rv"):
                continue
            score = difficulty_score(cid)
            display.append({
                "Name": camp.get("FacilityName"),
                "ID": cid,
                "Difficulty": f"{score:.2f}",
            })
        if display:
            st.dataframe(display)
        else:
            st.info("No results found.")
