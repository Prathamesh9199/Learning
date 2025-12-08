from typing import Dict
from resources.schema.pydantic_schemas import StoredProcedure, ParameterDetail

SP_REGISTRY: Dict[str, StoredProcedure] = {
    # 1. Master Search SP
    "supermarket_sales_SearchTransactions": StoredProcedure(
        name="dbo.supermarket_sales_SearchTransactions",
        description="Master Search SP: Filters transactions by Invoice IDs, Cities, Product Lines, or Date Range. Supports comma-separated lists for text filters.",
        parameters={
            "Invoice_IDs": ParameterDetail(description="Comma-separated list of specific Invoice IDs to retrieve (e.g., '123-ABC, 456-DEF')."),
            "Cities": ParameterDetail(description="Comma-separated list of Cities to filter by (e.g., 'Yangon, Mandalay')."),
            "Product_Lines": ParameterDetail(description="Comma-separated list of Product Lines/Categories to filter."),
            "StartDate": ParameterDetail(description="Filter for transactions occurring on or after this date (Format: YYYY-MM-DD)."),
            "EndDate": ParameterDetail(description="Filter for transactions occurring on or before this date (Format: YYYY-MM-DD).")
        },
        returns={"schema": ["Invoice_ID", "Branch", "City", "Product_line", "Total", "Date", "Payment", "Rating"]},
    ),

    # 2. Branch KPIs
    "supermarket_sales_GetBranchKPIs": StoredProcedure(
        name="dbo.supermarket_sales_GetBranchKPIs",
        description="Provides a high-level view of branch performance, including total revenue, items sold, margin percentage, and customer ratings.",
        parameters={}, 
        returns={"schema": ["Branch", "City", "Total_Transactions", "Items_Sold", "Total_Revenue", "Avg_Margin_Pct", "Avg_Customer_Rating"]},
    ),

    # 3. Product Performance
    "supermarket_sales_GetProductPerformance": StoredProcedure(
        name="dbo.supermarket_sales_GetProductPerformance",
        description="Identifies the best-selling product categories based on total revenue.",
        parameters={
            "TopN": ParameterDetail(description="Integer value specifying how many top product lines to retrieve (default is 5).")
        },
        returns={"schema": ["Product_line", "Revenue", "Units_Sold", "Avg_Price", "Highest_Single_Sale"]},
    ),

    # 4. Customer Demographics
    "supermarket_sales_GetCustomerDemographics": StoredProcedure(
        name="dbo.supermarket_sales_GetCustomerDemographics",
        description="Analyzes customer demographics to see spending habits and ratings based on Customer Type and Gender.",
        parameters={}, 
        returns={"schema": ["Customer_type", "Gender", "Visit_Count", "Total_Spend", "Avg_Spend_Per_Visit", "Avg_Rating"]},
    ),

    # 5. Hourly Sales Trends
    "supermarket_sales_GetHourlySalesTrends": StoredProcedure(
        name="dbo.supermarket_sales_GetHourlySalesTrends",
        description="Aggregates sales data by hour of the day to identify peak business hours.",
        parameters={}, 
        returns={"schema": ["Hour_Of_Day", "Transactions", "Revenue"]},
    )
}