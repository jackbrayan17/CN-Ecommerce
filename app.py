import streamlit as st
from supabase import create_client, Client
import pandas as pd
import uuid
from datetime import datetime
import mimetypes

st.set_page_config(page_title="Product Management App", page_icon=":moon:", layout="centered")
# Supabase config
url = "https://xfbfygphfxonsicyvadw.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhmYmZ5Z3BoZnhvbnNpY3l2YWR3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwOTMyNDEsImV4cCI6MjA2MzY2OTI0MX0.iMYPQ3zZOl1WLLDugTV24IAKFOE5XLI_JkMQp68tBKU"
supabase: Client = create_client(url, key)

# Dropdown Options
colors = ["Blue", "Green", "Red", "Orange", "Violet", "Brown", "Black", "White", "Pink", "Purple", "Yellow", "Grey"]
categories = ["Women Clothing", "Kid Clothing", "Men Clothing", "Accessories", "Shoes"]
clothing_sizes = ["XS", "S", "M", "L", "XL", "XXL"]
shoe_sizes = [str(size) for size in range(33, 47)]

# Tabs
tab1, tab2, tab3 = st.tabs(["➕ Add Product", "📝 Modify Product", "📖 View Products"])

# Upload image to Supabase Storage
def upload_image_to_supabase(image_file, folder="products"):
    try:
        file_bytes = image_file.read()
        file_id = str(uuid.uuid4())
        extension = image_file.name.split('.')[-1].lower()

        if extension not in ['png', 'jpg', 'jpeg']:
            return {"error": f"Unsupported file type for {image_file.name}. Skipping."}

        file_path = f"{folder}/{file_id}_{image_file.name}"
        mime_type = mimetypes.guess_type(image_file.name)[0] or 'application/octet-stream'

        upload_res = supabase.storage.from_("product-image").upload(file_path, file_bytes, {"content-type": mime_type})

        if upload_res.status_code != 200:
            return {"error": f"Upload failed with status {upload_res.status_code}."}

        public_url = supabase.storage.from_("product-image").get_public_url(file_path)
        return {"url": public_url, "path": file_path}

    except Exception as e:
        return {"error": f"Failed to upload image: {e}"}


# 📦 Add Product Tab
with tab1:
    st.header("Add a New Product")

    with st.form("product_form"):
        product_name = st.text_input("Product Name")
        description = st.text_area("Product Description")
        unit_price = st.number_input("Unit Price", min_value=0.0)
        selling_price = st.number_input("Selling Price", min_value=0.0)
        color = st.selectbox("Color", colors)
        category = st.selectbox("Category", categories)

        if category in ["Women Clothing", "Kid Clothing", "Men Clothing"]:
            size = st.selectbox("Size", clothing_sizes)
        elif category == "Shoes":
            size = st.selectbox("Size", shoe_sizes)
        else:
            size = "N/A"

        images = st.file_uploader("Upload up to 5 images", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

        submitted = st.form_submit_button("Save Product")

        if submitted:
            now = datetime.utcnow().isoformat()

            product_data = {
                "product_name": product_name,
                "description": description,
                "unit_price": unit_price,
                "selling_price": selling_price,
                "color": color,
                "category": category,
                "size": size,
                "created_at": now,
                "updated_at": now
            }

            response = supabase.table("products").insert(product_data).execute()

            if response.data:
                product_id = response.data[0]['id']
                st.success("✅ Product added successfully!")

                for image in images[:5]:
                    upload_result = upload_image_to_supabase(image)

                    if "error" in upload_result:
                        st.error(upload_result["error"])
                        continue

                    image_data = {
                        "product_id": product_id,
                        "image_url": upload_result["url"],
                        "storage_path": upload_result["path"]
                    }

                    supabase.table("productimage").insert(image_data).execute()

                st.success("📸 Images uploaded and linked successfully!")

            else:
                st.error("❌ Failed to add product.")

# 📝 Modify Product Tab
with tab2:
    st.header("Modify an Existing Product")

    try:
        products = supabase.table("products").select("*").execute().data
    except Exception as e:
        st.error(f"Failed to fetch products: {e}")
        products = []

    if products:
        product_df = pd.DataFrame(products)
        selected_product = st.selectbox("Select Product to Modify", product_df['product_name'])

        product_row = product_df[product_df['product_name'] == selected_product].iloc[0]

        with st.form("modify_form"):
            new_name = st.text_input("Product Name", value=product_row['product_name'])
            new_description = st.text_area("Product Description", value=product_row.get('description', ''))
            new_unit_price = st.number_input("Unit Price", min_value=0.0, value=product_row['unit_price'])
            new_selling_price = st.number_input("Selling Price", min_value=0.0, value=product_row['selling_price'])
            new_color = st.selectbox("Color", colors, index=colors.index(product_row['color']))
            new_category = st.selectbox("Category", categories, index=categories.index(product_row['category']))

            if new_category in ["Women Clothing", "Kid Clothing", "Men Clothing"]:
                new_size = st.selectbox("Size", clothing_sizes, index=clothing_sizes.index(product_row['size']))
            elif new_category == "Shoes":
                new_size = st.selectbox("Size", shoe_sizes, index=shoe_sizes.index(product_row['size']))
            else:
                new_size = "N/A"

            updated = st.form_submit_button("Update Product")

            if updated:
                updated_data = {
                    "product_name": new_name,
                    "description": new_description,
                    "unit_price": new_unit_price,
                    "selling_price": new_selling_price,
                    "color": new_color,
                    "category": new_category,
                    "size": new_size,
                    "updated_at": datetime.utcnow().isoformat()
                }

                supabase.table("products").update(updated_data).eq("id", product_row['id']).execute()
                st.success("✅ Product updated successfully!")

    else:
        st.warning("No products found in database.")

# 📖 View Products Tab
with tab3:
    st.header("All Products")

    try:
        products = supabase.table("products").select("*").execute().data
    except Exception as e:
        st.error(f"Failed to fetch products: {e}")
        products = []

    if products:
        product_df = pd.DataFrame(products)
        st.dataframe(product_df)
    else:
        st.write("No products found.")
