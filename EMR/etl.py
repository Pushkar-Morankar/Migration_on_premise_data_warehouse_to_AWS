from pyspark.sql import SparkSession
from pyspark.sql.functions import col, year, quarter, month, dayofmonth

# Initialize Spark session
spark = SparkSession.builder \
    .appName("SuperstoreETL") \
    .getOrCreate()

# Redshift connection details
s3_bucket_folder_url = "s3://superstore-migration-007/raw/"
redshift_url = "jdbc:redshift://redshift-cluster-1.cttrghdrytbi.us-east-1.redshift.amazonaws.com:5439/dev"
redshift_user = "awsuser"
redshift_password = "Admin1234"  # Replace with your password

# Read CSV files from S3
customers_df = spark.read.csv(f"{s3_bucket_folder_url}customers.csv", header=True, inferSchema=True)
products_df = spark.read.csv(f"{s3_bucket_folder_url}products.csv", header=True, inferSchema=True)
orders_df = spark.read.csv(f"{s3_bucket_folder_url}orders.csv", header=True, inferSchema=True)

# Transform: Time Dimension
time_df = orders_df.select("order_date").distinct() \
    .withColumn("year", year(col("order_date"))) \
    .withColumn("quarter", quarter(col("order_date"))) \
    .withColumn("month", month(col("order_date"))) \
    .withColumn("day", dayofmonth(col("order_date")))

# Transform: Customers Dimension (direct mapping)
customers_dim_df = customers_df.select(
    col("customer_id"), col("customer_name"), col("segment"),
    col("country"), col("city"), col("state"), col("postal_code"), col("region")
).distinct()

# Transform: Products Dimension (direct mapping)
products_dim_df = products_df.select(
    col("product_id"), col("product_name"), col("category"), col("sub_category")
).distinct()

# Transform: Sales Facts (join with dimensions, use natural keys)
sales_facts_df = orders_df \
    .join(time_df, "order_date", "inner") \
    .join(customers_dim_df, "customer_id", "inner") \
    .join(products_dim_df, "product_id", "inner") \
    .select(
        col("sales_key"),
        col("order_id"),
        col("order_date"),  # Link to time_dim
        col("customer_id"),  # Link to customers_dim
        col("product_id"),   # Link to products_dim
        col("sales").cast("float")
    )

# JDBC properties
jdbc_properties = {
    "user": redshift_user,
    "password": redshift_password,
    "driver": "com.amazon.redshift.jdbc42.Driver"
}

# Write to Redshift directly using JDBC
for df, table in [
    (time_df, "time_dim"),
    (customers_dim_df, "customers_dim"),
    (products_dim_df, "products_dim"),
    (sales_facts_df, "sales_facts")
]:
    df.write \
        .jdbc(
            url=redshift_url,
            table=table,
            mode="append",
            properties=jdbc_properties
        )

# Stop Spark session
spark.stop()
print("ETL completed successfully!")