import streamlit as st
import streamlit.components.v1 as components

# --- Data Parser ---
def parse_dict_to_tree(data_dict, parent_id=""):
    tree = []
    for key, value in data_dict.items():
        current_id = f"{parent_id}/{key}" if parent_id else key
        node = {"id": current_id, "label": str(key)}

        if isinstance(value, dict):
            node["children"] = parse_dict_to_tree(value, current_id)
        elif isinstance(value, list):
            node["children"] = [{"id": f"{current_id}/{item}", "label": str(item)} for item in value]
        else:
            node["children"] = [{"id": f"{current_id}/{value}", "label": str(value)}]
        
        tree.append(node)
    return tree

# --- Component Declaration ---
_component_func = components.declare_component("excel_filter", path="./excel_filter")

def excel_filter(data, key=None):
    tree_data = parse_dict_to_tree(data)
    # Default return empty list
    return _component_func(data=tree_data, key=key, default=[])

# --- Streamlit App ---
st.set_page_config(page_title="Advanced Filter", layout="centered")

# CSS to make the rest of the app look good with the component
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    h1 { color: #31333F; font-family: 'Source Sans Pro'; }
    .stMarkdown { font-family: 'Source Sans Pro'; }
    </style>
""", unsafe_allow_html=True)

st.title("Hierarchical Data Filter")
st.markdown("Use the dropdown below to search and select nested data points.")

# Mock Data
data = {
    "North America": {
        "USA": {
            "California": ["San Francisco", "Los Angeles", "San Diego"],
            "New York": ["NYC", "Buffalo", "Albany"]
        },
        "Canada": ["Toronto", "Vancouver", "Montreal"]
    },
    "Europe": {
        "UK": ["London", "Manchester"],
        "Germany": ["Berlin", "Munich", "Frankfurt"]
    },
    "Asia": {
        "Japan": ["Tokyo", "Osaka"],
        "India": ["Mumbai", "Delhi", "Bangalore"]
    }
}

# 1. Render the Component
selected_items = excel_filter(data, key="geo_filter")

# 2. Display Results
st.write("---")
if selected_items:
    # Filter to get only fully checked leaf nodes for cleaner output
    leaf_nodes = [
        item['id'].split('/')[-1] 
        for item in selected_items 
        if item['status'] == 'checked' and not any(
            child['id'].startswith(item['id'] + "/") for child in selected_items
        )
    ]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Selected", len(selected_items))
    with col2:
        st.metric("Leaf Nodes", len(leaf_nodes))
        
    st.info(f"**Selected Regions:** {', '.join(leaf_nodes)}")
    
    with st.expander("View Full JSON State"):
        st.json(selected_items)
else:
    st.warning("No items selected.")