# Databricks notebook source
dbutils.widgets.text("month", "")
file_month = dbutils.widgets.get("month")

silver_dir = "/Volumes/main/lichess/vol-silver/" + f"{file_month}/"
gold_dir = "/Volumes/main/lichess/vol-gold/" + f"{file_month}/"


dbutils.fs.rm(gold_dir, True)
dbutils.fs.mkdirs(gold_dir)

print(f"Filtering games from: {silver_dir} \n to {gold_dir}")

# COMMAND ----------


from pyspark.sql.functions import col, count, avg, when

df = spark.read.parquet(silver_dir)

# Example 1: Save games with eval
games_with_eval = df.filter((col("Moves").contains("eval")))
games_with_eval.write.mode("overwrite").parquet(gold_dir + "games_with_eval")

# Example 2: Count games by opening
opening_counts = df.groupBy("Opening").agg(count("*").alias("game_count"))
display(opening_counts.orderBy(col("game_count").desc()).limit(10))

# Example 3: Win rate for white players
white_win_rate = df.withColumn(
    "white_win", when(col("Result") == "1-0", 1).otherwise(0)
).agg(avg("white_win").alias("white_win_rate"))
display(white_win_rate)

# Example 4: Most common termination reasons
termination_counts = df.groupBy("Termination").agg(count("*").alias("count"))
display(termination_counts.orderBy(col("count").desc()))
