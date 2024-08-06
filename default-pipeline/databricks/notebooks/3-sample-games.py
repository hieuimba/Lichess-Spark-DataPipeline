# Databricks notebook source
dbutils.widgets.text("month", "")
file_month = dbutils.widgets.get("month")

silver_dir = "/Volumes/main/lichess/vol-silver/" + f"{file_month}/"
gold_dir = "/Volumes/main/lichess/vol-gold/" + f"{file_month}/"


dbutils.fs.rm(gold_dir, True)
dbutils.fs.mkdirs(gold_dir)

print(f"Filtering games from: {silver_dir} \n to {gold_dir}")

# COMMAND ----------


from pyspark.sql.functions import col

df = spark.read.parquet(silver_dir)

# Example: Get games with eval
df = df.filter((col("Moves").contains("eval")))

# Write to gold dir
df.write.partitionBy("UTCDate").mode("overwrite").parquet(gold_dir)
