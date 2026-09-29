import os
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st
import psycopg2
from dotenv import load_dotenv


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Cosmetics Retail Intelligence",
    page_icon="💄",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


# ============================================================
# DATABASE CONNECTION
# ============================================================

@st.cache_resource
def get_connection():

    if not DATABASE_URL:
        st.error("DATABASE_URL is missing from your .env file.")
        st.stop()

    try:
        connection = psycopg2.connect(
            DATABASE_URL,
            sslmode="require"
        )

        return connection

    except Exception as e:

        st.error("Could not connect to Supabase PostgreSQL.")
        st.code(str(e))
        st.stop()


# ============================================================
# SQL FUNCTION
# ============================================================

def run_query(query, params=None):

    connection = get_connection()

    try:

        return pd.read_sql_query(
            query,
            connection,
            params=params
        )

    except Exception as e:

        st.error("SQL query failed.")
        st.code(str(e))

        return pd.DataFrame()


# ============================================================
# HEADER
# ============================================================

st.title("💄 Cosmetics Retail Intelligence")

st.markdown(
    """
    **Distribution & Retail Analytics Dashboard**

    Monitor sales, products, inventory, suppliers, stores,
    customers and own-brand performance using data stored
    in Supabase PostgreSQL.
    """
)


# ============================================================
# SIDEBAR - NAVIGATION ONLY
# ============================================================

st.sidebar.title("📊 Dashboard")

page = st.sidebar.radio(
    "Select Page",
    [
        "Executive Dashboard",
        "Product Management",
        "Sales Analytics",
        "Inventory Management",
        "Distribution & Suppliers",
        "Own Brand Analytics",
        "Customer Analytics",
        "SQL Explorer",
        "Database Tables"
    ]
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

@st.cache_data(ttl=300)
def get_brands():

    return run_query(
        """
        SELECT brand_id, brand_name, brand_type
        FROM brands
        ORDER BY brand_name;
        """
    )


@st.cache_data(ttl=300)
def get_categories():

    return run_query(
        """
        SELECT category_id, category_name
        FROM categories
        ORDER BY category_name;
        """
    )


@st.cache_data(ttl=300)
def get_stores():

    return run_query(
        """
        SELECT store_id, store_name
        FROM stores
        ORDER BY store_name;
        """
    )


@st.cache_data(ttl=300)
def get_warehouses():

    return run_query(
        """
        SELECT warehouse_id, warehouse_name
        FROM warehouses
        ORDER BY warehouse_name;
        """
    )


@st.cache_data(ttl=300)
def get_suppliers():

    return run_query(
        """
        SELECT supplier_id, supplier_name
        FROM suppliers
        ORDER BY supplier_name;
        """
    )


@st.cache_data(ttl=300)
def get_product_types():

    return run_query(
        """
        SELECT DISTINCT product_type
        FROM products
        WHERE product_type IS NOT NULL
        ORDER BY product_type;
        """
    )


@st.cache_data(ttl=300)
def get_date_range():

    return run_query(
        """
        SELECT
            MIN(sale_date)::date AS min_date,
            MAX(sale_date)::date AS max_date
        FROM sales;
        """
    )


brands_df = get_brands()
categories_df = get_categories()
stores_df = get_stores()
warehouses_df = get_warehouses()
suppliers_df = get_suppliers()
product_types_df = get_product_types()
date_range_df = get_date_range()


# ============================================================
# COMMON VALUES
# ============================================================

brand_names = brands_df["brand_name"].tolist()
brand_types = brands_df["brand_type"].dropna().unique().tolist()

category_names = categories_df["category_name"].tolist()

store_names = stores_df["store_name"].tolist()

warehouse_names = warehouses_df["warehouse_name"].tolist()

supplier_names = suppliers_df["supplier_name"].tolist()

product_types = product_types_df["product_type"].tolist()


if not date_range_df.empty:

    MIN_DATE = pd.to_datetime(
        date_range_df.iloc[0]["min_date"]
    ).date()

    MAX_DATE = pd.to_datetime(
        date_range_df.iloc[0]["max_date"]
    ).date()

else:

    MIN_DATE = date(2024, 1, 1)
    MAX_DATE = date.today()


# ============================================================
# 1. EXECUTIVE DASHBOARD
# ============================================================

if page == "Executive Dashboard":

    st.header("📊 Executive Dashboard")

    st.subheader("🔎 Executive Dashboard Filters")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        executive_dates = st.date_input(
            "Sale Date",
            value=(MIN_DATE, MAX_DATE),
            min_value=MIN_DATE,
            max_value=MAX_DATE,
            key="executive_dates"
        )

    with col2:

        executive_store = st.multiselect(
            "Store",
            store_names,
            default=store_names,
            key="executive_store"
        )

    with col3:

        executive_product_type = st.multiselect(
            "Product Type",
            product_types,
            default=product_types,
            key="executive_product_type"
        )

    with col4:

        executive_brand_type = st.multiselect(
            "Brand Type",
            brand_types,
            default=brand_types,
            key="executive_brand_type"
        )


    col5, col6 = st.columns(2)

    with col5:

        executive_channel = st.multiselect(
            "Sales Channel",
            ["Store", "Online"],
            default=["Store", "Online"],
            key="executive_channel"
        )

    with col6:

        executive_category = st.multiselect(
            "Category",
            category_names,
            default=category_names,
            key="executive_category"
        )


    if isinstance(executive_dates, tuple):

        executive_start = executive_dates[0]
        executive_end = executive_dates[1]

    else:

        executive_start = MIN_DATE
        executive_end = MAX_DATE


    conditions = [
        "s.sale_date::date BETWEEN %s AND %s"
    ]

    params = [
        executive_start,
        executive_end
    ]


    if executive_store:

        placeholders = ",".join(
            ["%s"] * len(executive_store)
        )

        conditions.append(
            f"st.store_name IN ({placeholders})"
        )

        params.extend(executive_store)


    if executive_product_type:

        placeholders = ",".join(
            ["%s"] * len(executive_product_type)
        )

        conditions.append(
            f"p.product_type IN ({placeholders})"
        )

        params.extend(executive_product_type)


    if executive_brand_type:

        placeholders = ",".join(
            ["%s"] * len(executive_brand_type)
        )

        conditions.append(
            f"b.brand_type IN ({placeholders})"
        )

        params.extend(executive_brand_type)


    if executive_channel:

        placeholders = ",".join(
            ["%s"] * len(executive_channel)
        )

        conditions.append(
            f"s.sales_channel IN ({placeholders})"
        )

        params.extend(executive_channel)


    if executive_category:

        placeholders = ",".join(
            ["%s"] * len(executive_category)
        )

        conditions.append(
            f"c.category_name IN ({placeholders})"
        )

        params.extend(executive_category)


    where_clause = " AND ".join(conditions)


    # --------------------------------------------------------
    # KPI QUERY
    # --------------------------------------------------------

    kpi_query = f"""

    SELECT

        COALESCE(
            SUM(si.total_amount),
            0
        ) AS revenue,

        COUNT(
            DISTINCT s.sale_id
        ) AS orders,

        COALESCE(
            SUM(si.quantity),
            0
        ) AS units_sold,

        COALESCE(
            SUM(
                si.total_amount
                -
                (si.quantity * p.unit_cost)
            ),
            0
        ) AS gross_profit

    FROM sales s

    JOIN sale_items si
        ON s.sale_id = si.sale_id

    JOIN products p
        ON si.product_id = p.product_id

    JOIN brands b
        ON p.brand_id = b.brand_id

    JOIN categories c
        ON p.category_id = c.category_id

    JOIN stores st
        ON s.store_id = st.store_id

    WHERE {where_clause};

    """

    kpi_df = run_query(
        kpi_query,
        params
    )


    revenue = float(kpi_df.iloc[0]["revenue"] or 0)
    orders = int(kpi_df.iloc[0]["orders"] or 0)
    units = int(kpi_df.iloc[0]["units_sold"] or 0)
    profit = float(kpi_df.iloc[0]["gross_profit"] or 0)


    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Revenue",
        f"₹{revenue:,.2f}"
    )

    c2.metric(
        "Orders",
        f"{orders:,}"
    )

    c3.metric(
        "Units Sold",
        f"{units:,}"
    )

    c4.metric(
        "Gross Profit",
        f"₹{profit:,.2f}"
    )


    # --------------------------------------------------------
    # STORE PERFORMANCE
    # --------------------------------------------------------

    store_query = f"""

    SELECT

        st.store_name,

        SUM(si.total_amount) AS revenue,

        SUM(si.quantity) AS units_sold,

        COUNT(
            DISTINCT s.sale_id
        ) AS orders

    FROM sales s

    JOIN sale_items si
        ON s.sale_id = si.sale_id

    JOIN products p
        ON si.product_id = p.product_id

    JOIN brands b
        ON p.brand_id = b.brand_id

    JOIN categories c
        ON p.category_id = c.category_id

    JOIN stores st
        ON s.store_id = st.store_id

    WHERE {where_clause}

    GROUP BY
        st.store_id,
        st.store_name

    ORDER BY revenue DESC;

    """

    store_df = run_query(
        store_query,
        params
    )


    if not store_df.empty:

        st.subheader("🏪 Store Performance")

        st.dataframe(
            store_df,
            use_container_width=True
        )

        fig = px.bar(
            store_df,
            x="store_name",
            y="revenue"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# 2. PRODUCT MANAGEMENT
# ============================================================

elif page == "Product Management":

    st.header("🧴 Product Management")

    st.subheader("🔎 Product Filters")

    col1, col2, col3 = st.columns(3)

    with col1:

        pm_product_type = st.multiselect(
            "Product Type",
            product_types,
            default=product_types,
            key="pm_product_type"
        )

    with col2:

        pm_brand = st.multiselect(
            "Brand",
            brand_names,
            default=brand_names,
            key="pm_brand"
        )

    with col3:

        pm_brand_type = st.multiselect(
            "Brand Type",
            brand_types,
            default=brand_types,
            key="pm_brand_type"
        )


    col4, col5 = st.columns(2)

    with col4:

        pm_category = st.multiselect(
            "Category",
            category_names,
            default=category_names,
            key="pm_category"
        )

    with col5:

        pm_status = st.selectbox(
            "Product Status",
            ["All", "Active", "Inactive"],
            key="pm_status"
        )


    conditions = []
    params = []


    if pm_product_type:

        placeholders = ",".join(
            ["%s"] * len(pm_product_type)
        )

        conditions.append(
            f"p.product_type IN ({placeholders})"
        )

        params.extend(pm_product_type)


    if pm_brand:

        placeholders = ",".join(
            ["%s"] * len(pm_brand)
        )

        conditions.append(
            f"b.brand_name IN ({placeholders})"
        )

        params.extend(pm_brand)


    if pm_brand_type:

        placeholders = ",".join(
            ["%s"] * len(pm_brand_type)
        )

        conditions.append(
            f"b.brand_type IN ({placeholders})"
        )

        params.extend(pm_brand_type)


    if pm_category:

        placeholders = ",".join(
            ["%s"] * len(pm_category)
        )

        conditions.append(
            f"c.category_name IN ({placeholders})"
        )

        params.extend(pm_category)


    if pm_status == "Active":

        conditions.append(
            "p.is_active = TRUE"
        )

    elif pm_status == "Inactive":

        conditions.append(
            "p.is_active = FALSE"
        )


    where_clause = (
        " AND ".join(conditions)
        if conditions
        else "TRUE"
    )


    product_query = f"""

    SELECT

        p.product_id,

        p.product_name,

        b.brand_name,

        b.brand_type,

        c.category_name,

        p.product_type,

        p.unit_cost,

        p.selling_price,

        p.launch_date,

        p.is_active

    FROM products p

    JOIN brands b
        ON p.brand_id = b.brand_id

    JOIN categories c
        ON p.category_id = c.category_id

    WHERE {where_clause}

    ORDER BY p.product_id;

    """

    product_df = run_query(
        product_query,
        params
    )


    if not product_df.empty:

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Products",
            len(product_df)
        )

        c2.metric(
            "Active",
            int(product_df["is_active"].sum())
        )

        c3.metric(
            "Own Brand",
            int(
                (
                    product_df["brand_type"]
                    == "Own Brand"
                ).sum()
            )
        )


        st.subheader("Product Table")

        st.dataframe(
            product_df,
            use_container_width=True,
            height=500
        )


        summary = (
            product_df
            .groupby("product_type")
            .size()
            .reset_index(
                name="product_count"
            )
        )


        fig = px.bar(
            summary,
            x="product_type",
            y="product_count",
            title="Products by Type"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# 3. SALES ANALYTICS
# ============================================================

elif page == "Sales Analytics":

    st.header("📈 Sales Analytics")

    st.subheader("🔎 Sales Filters")

    col1, col2, col3 = st.columns(3)

    with col1:

        sales_dates = st.date_input(
            "Sale Date",
            value=(MIN_DATE, MAX_DATE),
            min_value=MIN_DATE,
            max_value=MAX_DATE,
            key="sales_dates"
        )

    with col2:

        sales_store = st.multiselect(
            "Store",
            store_names,
            default=store_names,
            key="sales_store"
        )

    with col3:

        sales_channel = st.multiselect(
            "Sales Channel",
            ["Store", "Online"],
            default=["Store", "Online"],
            key="sales_channel"
        )


    col4, col5, col6 = st.columns(3)

    with col4:

        sales_product_type = st.multiselect(
            "Product Type",
            product_types,
            default=product_types,
            key="sales_product_type"
        )

    with col5:

        sales_brand = st.multiselect(
            "Brand",
            brand_names,
            default=brand_names,
            key="sales_brand"
        )

    with col6:

        sales_category = st.multiselect(
            "Category",
            category_names,
            default=category_names,
            key="sales_category"
        )


    if isinstance(sales_dates, tuple):

        sales_start = sales_dates[0]
        sales_end = sales_dates[1]

    else:

        sales_start = MIN_DATE
        sales_end = MAX_DATE


    conditions = [
        "s.sale_date::date BETWEEN %s AND %s"
    ]

    params = [
        sales_start,
        sales_end
    ]


    if sales_store:

        placeholders = ",".join(
            ["%s"] * len(sales_store)
        )

        conditions.append(
            f"st.store_name IN ({placeholders})"
        )

        params.extend(sales_store)


    if sales_channel:

        placeholders = ",".join(
            ["%s"] * len(sales_channel)
        )

        conditions.append(
            f"s.sales_channel IN ({placeholders})"
        )

        params.extend(sales_channel)


    if sales_product_type:

        placeholders = ",".join(
            ["%s"] * len(sales_product_type)
        )

        conditions.append(
            f"p.product_type IN ({placeholders})"
        )

        params.extend(sales_product_type)


    if sales_brand:

        placeholders = ",".join(
            ["%s"] * len(sales_brand)
        )

        conditions.append(
            f"b.brand_name IN ({placeholders})"
        )

        params.extend(sales_brand)


    if sales_category:

        placeholders = ",".join(
            ["%s"] * len(sales_category)
        )

        conditions.append(
            f"c.category_name IN ({placeholders})"
        )

        params.extend(sales_category)


    where_clause = " AND ".join(conditions)


    # --------------------------------------------------------
    # TRANSACTIONS
    # --------------------------------------------------------

    sales_query = f"""

    SELECT

        s.sale_id,

        s.sale_date,

        st.store_name,

        s.sales_channel,

        COALESCE(
            cu.customer_name,
            'Walk-in Customer'
        ) AS customer_name,

        SUM(si.quantity) AS units,

        SUM(si.total_amount) AS revenue

    FROM sales s

    JOIN stores st
        ON s.store_id = st.store_id

    LEFT JOIN customers cu
        ON s.customer_id = cu.customer_id

    JOIN sale_items si
        ON s.sale_id = si.sale_id

    JOIN products p
        ON si.product_id = p.product_id

    JOIN brands b
        ON p.brand_id = b.brand_id

    JOIN categories c
        ON p.category_id = c.category_id

    WHERE {where_clause}

    GROUP BY

        s.sale_id,
        s.sale_date,
        st.store_name,
        s.sales_channel,
        cu.customer_name

    ORDER BY
        s.sale_date DESC;

    """

    sales_df = run_query(
        sales_query,
        params
    )


    if not sales_df.empty:

        st.subheader("Sales Transactions")

        st.dataframe(
            sales_df,
            use_container_width=True,
            height=450
        )


    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    category_query = f"""

    SELECT

        c.category_name,

        SUM(si.quantity) AS units_sold,

        SUM(si.total_amount) AS revenue

    FROM sales s

    JOIN sale_items si
        ON s.sale_id = si.sale_id

    JOIN products p
        ON si.product_id = p.product_id

    JOIN brands b
        ON p.brand_id = b.brand_id

    JOIN categories c
        ON p.category_id = c.category_id

    JOIN stores st
        ON s.store_id = st.store_id

    WHERE {where_clause}

    GROUP BY
        c.category_id,
        c.category_name

    ORDER BY revenue DESC;

    """

    category_df = run_query(
        category_query,
        params
    )


    if not category_df.empty:

        st.subheader("Category Performance")

        st.dataframe(
            category_df,
            use_container_width=True
        )

        fig = px.bar(
            category_df,
            x="category_name",
            y="revenue",
            title="Revenue by Category"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # --------------------------------------------------------
    # CHANNEL
    # --------------------------------------------------------

    channel_query = f"""

    SELECT

        s.sales_channel,

        SUM(si.quantity) AS units_sold,

        SUM(si.total_amount) AS revenue

    FROM sales s

    JOIN sale_items si
        ON s.sale_id = si.sale_id

    JOIN products p
        ON si.product_id = p.product_id

    JOIN brands b
        ON p.brand_id = b.brand_id

    JOIN categories c
        ON p.category_id = c.category_id

    JOIN stores st
        ON s.store_id = st.store_id

    WHERE {where_clause}

    GROUP BY s.sales_channel;

    """

    channel_df = run_query(
        channel_query,
        params
    )


    if not channel_df.empty:

        st.subheader("Sales Channel")

        c1, c2 = st.columns(2)

        with c1:

            fig = px.pie(
                channel_df,
                names="sales_channel",
                values="revenue"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        with c2:

            st.dataframe(
                channel_df,
                use_container_width=True
            )


# ============================================================
# 4. INVENTORY MANAGEMENT
# ============================================================

elif page == "Inventory Management":

    st.header("📦 Inventory Management")

    st.subheader("🔎 Inventory Filters")

    col1, col2, col3 = st.columns(3)

    with col1:

        inventory_warehouse = st.multiselect(
            "Warehouse",
            warehouse_names,
            default=warehouse_names,
            key="inventory_warehouse"
        )

    with col2:

        inventory_product_type = st.multiselect(
            "Product Type",
            product_types,
            default=product_types,
            key="inventory_product_type"
        )

    with col3:

        inventory_brand = st.multiselect(
            "Brand",
            brand_names,
            default=brand_names,
            key="inventory_brand"
        )


    col4, col5, col6 = st.columns(3)

    with col4:

        inventory_category = st.multiselect(
            "Category",
            category_names,
            default=category_names,
            key="inventory_category"
        )

    with col5:

        inventory_brand_type = st.multiselect(
            "Brand Type",
            brand_types,
            default=brand_types,
            key="inventory_brand_type"
        )

    with col6:

        inventory_status = st.selectbox(
            "Stock Status",
            [
                "All",
                "Low Stock",
                "Healthy"
            ],
            key="inventory_status"
        )


    conditions = []
    params = []


    if inventory_warehouse:

        placeholders = ",".join(
            ["%s"] * len(inventory_warehouse)
        )

        conditions.append(
            f"w.warehouse_name IN ({placeholders})"
        )

        params.extend(inventory_warehouse)


    if inventory_product_type:

        placeholders = ",".join(
            ["%s"] * len(inventory_product_type)
        )

        conditions.append(
            f"p.product_type IN ({placeholders})"
        )

        params.extend(inventory_product_type)


    if inventory_brand:

        placeholders = ",".join(
            ["%s"] * len(inventory_brand)
        )

        conditions.append(
            f"b.brand_name IN ({placeholders})"
        )

        params.extend(inventory_brand)


    if inventory_category:

        placeholders = ",".join(
            ["%s"] * len(inventory_category)
        )

        conditions.append(
            f"c.category_name IN ({placeholders})"
        )

        params.extend(inventory_category)


    if inventory_brand_type:

        placeholders = ",".join(
            ["%s"] * len(inventory_brand_type)
        )

        conditions.append(
            f"b.brand_type IN ({placeholders})"
        )

        params.extend(inventory_brand_type)


    if inventory_status == "Low Stock":

        conditions.append(
            "i.quantity_in_stock <= i.reorder_level"
        )

    elif inventory_status == "Healthy":

        conditions.append(
            "i.quantity_in_stock > i.reorder_level"
        )


    where_clause = (
        " AND ".join(conditions)
        if conditions
        else "TRUE"
    )


    inventory_query = f"""

    SELECT

        i.inventory_id,

        w.warehouse_name,

        p.product_name,

        b.brand_name,

        b.brand_type,

        c.category_name,

        p.product_type,

        i.quantity_in_stock,

        i.reorder_level,

        CASE

            WHEN
                i.quantity_in_stock
                <= i.reorder_level
            THEN 'Low Stock'

            ELSE 'Healthy'

        END AS stock_status,

        i.last_updated

    FROM inventory i

    JOIN warehouses w
        ON i.warehouse_id = w.warehouse_id

    JOIN products p
        ON i.product_id = p.product_id

    JOIN brands b
        ON p.brand_id = b.brand_id

    JOIN categories c
        ON p.category_id = c.category_id

    WHERE {where_clause}

    ORDER BY
        i.quantity_in_stock ASC;

    """

    inventory_df = run_query(
        inventory_query,
        params
    )


    if not inventory_df.empty:

        total_stock = int(
            inventory_df[
                "quantity_in_stock"
            ].sum()
        )

        low_stock_count = int(
            (
                inventory_df["stock_status"]
                == "Low Stock"
            ).sum()
        )


        c1, c2 = st.columns(2)

        c1.metric(
            "Inventory Units",
            f"{total_stock:,}"
        )

        c2.metric(
            "Low Stock Records",
            f"{low_stock_count:,}"
        )


        st.subheader(
            "Inventory Table"
        )

        st.dataframe(
            inventory_df,
            use_container_width=True,
            height=500
        )


        warehouse_summary = (
            inventory_df
            .groupby("warehouse_name")
            ["quantity_in_stock"]
            .sum()
            .reset_index()
        )


        fig = px.bar(
            warehouse_summary,
            x="warehouse_name",
            y="quantity_in_stock",
            title="Inventory by Warehouse"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# 5. DISTRIBUTION & SUPPLIERS
# ============================================================

elif page == "Distribution & Suppliers":

    st.header("🚚 Distribution & Suppliers")

    st.subheader("🔎 Distribution Filters")

    col1, col2, col3 = st.columns(3)

    with col1:

        distribution_supplier = st.multiselect(
            "Supplier",
            supplier_names,
            default=supplier_names,
            key="distribution_supplier"
        )

    with col2:

        distribution_warehouse = st.multiselect(
            "Warehouse",
            warehouse_names,
            default=warehouse_names,
            key="distribution_warehouse"
        )

    with col3:

        distribution_status = st.multiselect(
            "Order Status",
            [
                "Pending",
                "Delivered",
                "Cancelled"
            ],
            default=[
                "Pending",
                "Delivered",
                "Cancelled"
            ],
            key="distribution_status"
        )


    po_query = """

    SELECT

        po.purchase_order_id,

        s.supplier_name,

        w.warehouse_name,

        po.order_date,

        po.expected_delivery_date,

        po.actual_delivery_date,

        po.order_status,

        po.total_amount

    FROM purchase_orders po

    JOIN suppliers s
        ON po.supplier_id = s.supplier_id

    JOIN warehouses w
        ON po.warehouse_id = w.warehouse_id

    WHERE
        (%s IS NULL OR s.supplier_name = ANY(%s))
        AND
        (%s IS NULL OR w.warehouse_name = ANY(%s))
        AND
        (%s IS NULL OR po.order_status = ANY(%s))

    ORDER BY
        po.order_date DESC;

    """

    supplier_param = (
        distribution_supplier
        if distribution_supplier
        else None
    )

    warehouse_param = (
        distribution_warehouse
        if distribution_warehouse
        else None
    )

    status_param = (
        distribution_status
        if distribution_status
        else None
    )


    po_df = run_query(
        po_query,
        [
            supplier_param,
            supplier_param,
            warehouse_param,
            warehouse_param,
            status_param,
            status_param
        ]
    )


    if not po_df.empty:

        st.subheader(
            "Purchase Orders"
        )

        st.dataframe(
            po_df,
            use_container_width=True,
            height=450
        )


    # --------------------------------------------------------
    # SUPPLIER SUMMARY
    # --------------------------------------------------------

    supplier_query = """

    SELECT

        s.supplier_name,

        COUNT(
            po.purchase_order_id
        ) AS purchase_orders,

        COALESCE(
            SUM(po.total_amount),
            0
        ) AS purchase_value

    FROM suppliers s

    LEFT JOIN purchase_orders po
        ON s.supplier_id = po.supplier_id

    GROUP BY

        s.supplier_id,
        s.supplier_name

    ORDER BY
        purchase_value DESC;

    """

    supplier_summary = run_query(
        supplier_query
    )


    if not supplier_summary.empty:

        st.subheader(
            "Supplier Purchase Analysis"
        )

        st.dataframe(
            supplier_summary,
            use_container_width=True
        )

        fig = px.bar(
            supplier_summary,
            x="supplier_name",
            y="purchase_value",
            title="Purchase Value by Supplier"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # --------------------------------------------------------
    # SUPPLIER MASTER
    # --------------------------------------------------------

    st.subheader(
        "Supplier Master Data"
    )

    supplier_master = run_query(
        """
        SELECT
            supplier_id,
            supplier_name,
            contact_person,
            phone,
            email,
            city,
            state,
            supplier_status
        FROM suppliers
        ORDER BY supplier_name;
        """
    )

    st.dataframe(
        supplier_master,
        use_container_width=True
    )


# ============================================================
# 6. OWN BRAND ANALYTICS
# ============================================================

elif page == "Own Brand Analytics":

    st.header("🏷️ Own Brand Analytics")

    st.subheader("🔎 Own Brand Filters")

    col1, col2, col3 = st.columns(3)

    with col1:

        own_dates = st.date_input(
            "Sale Date",
            value=(MIN_DATE, MAX_DATE),
            min_value=MIN_DATE,
            max_value=MAX_DATE,
            key="own_dates"
        )

    with col2:

        own_category = st.multiselect(
            "Category",
            category_names,
            default=category_names,
            key="own_category"
        )

    with col3:

        own_product_type = st.multiselect(
            "Product Type",
            product_types,
            default=product_types,
            key="own_product_type"
        )


    col4, col5 = st.columns(2)

    with col4:

        own_store = st.multiselect(
            "Store",
            store_names,
            default=store_names,
            key="own_store"
        )

    with col5:

        own_channel = st.multiselect(
            "Sales Channel",
            ["Store", "Online"],
            default=["Store", "Online"],
            key="own_channel"
        )


    if isinstance(own_dates, tuple):

        own_start = own_dates[0]
        own_end = own_dates[1]

    else:

        own_start = MIN_DATE
        own_end = MAX_DATE


    conditions = [
        "s.sale_date::date BETWEEN %s AND %s",
        "b.brand_type = 'Own Brand'"
    ]

    params = [
        own_start,
        own_end
    ]


    if own_category:

        placeholders = ",".join(
            ["%s"] * len(own_category)
        )

        conditions.append(
            f"c.category_name IN ({placeholders})"
        )

        params.extend(own_category)


    if own_product_type:

        placeholders = ",".join(
            ["%s"] * len(own_product_type)
        )

        conditions.append(
            f"p.product_type IN ({placeholders})"
        )

        params.extend(own_product_type)


    if own_store:

        placeholders = ",".join(
            ["%s"] * len(own_store)
        )

        conditions.append(
            f"st.store_name IN ({placeholders})"
        )

        params.extend(own_store)


    if own_channel:

        placeholders = ",".join(
            ["%s"] * len(own_channel)
        )

        conditions.append(
            f"s.sales_channel IN ({placeholders})"
        )

        params.extend(own_channel)


    where_clause = " AND ".join(conditions)


    own_query = f"""

    SELECT

        b.brand_name,

        p.product_name,

        c.category_name,

        p.product_type,

        SUM(si.quantity) AS units_sold,

        SUM(si.total_amount) AS revenue,

        SUM(
            si.total_amount
            -
            (si.quantity * p.unit_cost)
        ) AS gross_profit

    FROM sales s

    JOIN sale_items si
        ON s.sale_id = si.sale_id

    JOIN products p
        ON si.product_id = p.product_id

    JOIN brands b
        ON p.brand_id = b.brand_id

    JOIN categories c
        ON p.category_id = c.category_id

    JOIN stores st
        ON s.store_id = st.store_id

    WHERE {where_clause}

    GROUP BY

        b.brand_name,
        p.product_id,
        p.product_name,
        c.category_name,
        p.product_type

    ORDER BY revenue DESC;

    """

    own_df = run_query(
        own_query,
        params
    )


    if not own_df.empty:

        total_revenue = float(
            own_df["revenue"].sum()
        )

        total_profit = float(
            own_df["gross_profit"].sum()
        )

        total_units = int(
            own_df["units_sold"].sum()
        )


        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Own Brand Revenue",
            f"₹{total_revenue:,.2f}"
        )

        c2.metric(
            "Own Brand Gross Profit",
            f"₹{total_profit:,.2f}"
        )

        c3.metric(
            "Own Brand Units Sold",
            f"{total_units:,}"
        )


        st.subheader(
            "Own Brand Product Performance"
        )

        st.dataframe(
            own_df,
            use_container_width=True
        )


        fig = px.bar(
            own_df,
            x="product_name",
            y="revenue",
            title="Own Brand Revenue by Product"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# 7. CUSTOMER ANALYTICS
# ============================================================

elif page == "Customer Analytics":

    st.header("👥 Customer Analytics")

    st.subheader("🔎 Customer Filters")

    col1, col2, col3 = st.columns(3)

    with col1:

        customer_dates = st.date_input(
            "Sale Date",
            value=(MIN_DATE, MAX_DATE),
            min_value=MIN_DATE,
            max_value=MAX_DATE,
            key="customer_dates"
        )

    with col2:

        customer_store = st.multiselect(
            "Store",
            store_names,
            default=store_names,
            key="customer_store"
        )

    with col3:

        customer_channel = st.multiselect(
            "Sales Channel",
            ["Store", "Online"],
            default=["Store", "Online"],
            key="customer_channel"
        )


    if isinstance(customer_dates, tuple):

        customer_start = customer_dates[0]
        customer_end = customer_dates[1]

    else:

        customer_start = MIN_DATE
        customer_end = MAX_DATE


    conditions = [
        "s.sale_date::date BETWEEN %s AND %s"
    ]

    params = [
        customer_start,
        customer_end
    ]


    if customer_store:

        placeholders = ",".join(
            ["%s"] * len(customer_store)
        )

        conditions.append(
            f"st.store_name IN ({placeholders})"
        )

        params.extend(customer_store)


    if customer_channel:

        placeholders = ",".join(
            ["%s"] * len(customer_channel)
        )

        conditions.append(
            f"s.sales_channel IN ({placeholders})"
        )

        params.extend(customer_channel)


    where_clause = " AND ".join(
        conditions
    )


    customer_sales_query = f"""

    SELECT

        COALESCE(
            c.customer_name,
            'Walk-in Customer'
        ) AS customer_name,

        COUNT(
            DISTINCT s.sale_id
        ) AS orders,

        SUM(
            si.quantity
        ) AS units_bought,

        SUM(
            si.total_amount
        ) AS total_spend

    FROM sales s

    LEFT JOIN customers c
        ON s.customer_id = c.customer_id

    JOIN sale_items si
        ON s.sale_id = si.sale_id

    JOIN products p
        ON si.product_id = p.product_id

    JOIN brands b
        ON p.brand_id = b.brand_id

    JOIN categories cat
        ON p.category_id = cat.category_id

    JOIN stores st
        ON s.store_id = st.store_id

    WHERE {where_clause}

    GROUP BY
        c.customer_id,
        c.customer_name

    ORDER BY
        total_spend DESC;

    """

    customer_sales_df = run_query(
        customer_sales_query,
        params
    )


    if not customer_sales_df.empty:

        total_customers = len(
            customer_sales_df
        )

        total_spend = float(
            customer_sales_df[
                "total_spend"
            ].sum()
        )


        c1, c2 = st.columns(2)

        c1.metric(
            "Customers",
            f"{total_customers:,}"
        )

        c2.metric(
            "Total Customer Spend",
            f"₹{total_spend:,.2f}"
        )


        st.subheader(
            "Customer Purchase Analysis"
        )

        st.dataframe(
            customer_sales_df,
            use_container_width=True
        )


        top_customers = (
            customer_sales_df
            .head(10)
        )


        fig = px.bar(
            top_customers,
            x="customer_name",
            y="total_spend",
            title="Top Customers by Spending"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # --------------------------------------------------------
    # CUSTOMER MASTER
    # --------------------------------------------------------

    st.subheader(
        "Customer Master Data"
    )

    customer_master = run_query(
        """
        SELECT
            customer_id,
            customer_name,
            phone,
            email,
            city,
            state,
            registration_date
        FROM customers
        ORDER BY customer_id;
        """
    )

    st.dataframe(
        customer_master,
        use_container_width=True
    )


# ============================================================
# 8. SQL EXPLORER
# ============================================================

elif page == "SQL Explorer":

    st.header("🧮 SQL Explorer")

    st.markdown(
        """
        Run read-only SQL queries directly against
        your Supabase PostgreSQL database.
        """
    )


    sql_query = st.text_area(
        "Enter SQL Query",
        value="""
SELECT
    p.product_name,
    b.brand_name,
    c.category_name,
    SUM(si.quantity) AS units_sold,
    SUM(si.total_amount) AS revenue
FROM sale_items si
JOIN products p
    ON si.product_id = p.product_id
JOIN brands b
    ON p.brand_id = b.brand_id
JOIN categories c
    ON p.category_id = c.category_id
GROUP BY
    p.product_name,
    b.brand_name,
    c.category_name
ORDER BY revenue DESC;
""",
        height=300
    )


    if st.button(
        "▶ Run SQL",
        type="primary"
    ):

        cleaned = sql_query.strip()

        upper = cleaned.upper()

        if not (
            upper.startswith("SELECT")
            or upper.startswith("WITH")
        ):

            st.error(
                "Only SELECT and WITH queries are allowed."
            )

        else:

            result = run_query(
                cleaned
            )

            if not result.empty:

                st.success(
                    f"{len(result)} rows returned."
                )

                st.dataframe(
                    result,
                    use_container_width=True
                )

                csv = result.to_csv(
                    index=False
                )

                st.download_button(
                    "⬇️ Download CSV",
                    csv,
                    "sql_results.csv",
                    "text/csv"
                )

            else:

                st.info(
                    "The query returned no records."
                )


# ============================================================
# 9. DATABASE TABLES
# ============================================================

elif page == "Database Tables":

    st.header("🗄️ Database Tables")

    st.markdown(
        """
        Select any table from the Supabase PostgreSQL
        database and view its actual records.
        """
    )


    tables = [

        "brands",
        "categories",
        "suppliers",
        "products",
        "warehouses",
        "stores",
        "customers",
        "purchase_orders",
        "purchase_order_items",
        "inventory",
        "sales",
        "sale_items",
        "payments"

    ]


    col1, col2 = st.columns(2)

    with col1:

        selected_table = st.selectbox(
            "Select Table",
            tables,
            key="database_table"
        )

    with col2:

        row_limit = st.number_input(
            "Rows to Display",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
            key="database_row_limit"
        )


    if st.button(
        "🔄 Load Table",
        type="primary"
    ):

        table_query = f"""

        SELECT *

        FROM {selected_table}

        LIMIT %s;

        """

        table_df = run_query(
            table_query,
            [row_limit]
        )


        if not table_df.empty:

            st.success(
                f"{selected_table} loaded successfully."
            )

            st.subheader(
                f"📋 {selected_table}"
            )

            st.dataframe(
                table_df,
                use_container_width=True,
                height=500
            )


            csv = table_df.to_csv(
                index=False
            )

            st.download_button(
                "⬇️ Download Table CSV",
                csv,
                f"{selected_table}.csv",
                "text/csv"
            )


    # --------------------------------------------------------
    # TABLE STRUCTURE
    # --------------------------------------------------------

    st.markdown("---")

    st.subheader(
        f"📐 Structure of `{selected_table}`"
    )


    structure_query = """

    SELECT

        ordinal_position,

        column_name,

        data_type,

        is_nullable

    FROM information_schema.columns

    WHERE
        table_schema = 'public'

        AND table_name = %s

    ORDER BY
        ordinal_position;

    """

    structure_df = run_query(
        structure_query,
        [selected_table]
    )


    if not structure_df.empty:

        st.dataframe(
            structure_df,
            use_container_width=True
        )


# ============================================================
# FOOTER
# ============================================================

st.sidebar.markdown("---")

st.sidebar.caption(
    "Cosmetics Retail Intelligence"
)

st.sidebar.caption(
    "Streamlit + Supabase PostgreSQL"
)