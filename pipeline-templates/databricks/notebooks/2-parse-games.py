# Databricks notebook source
dbutils.widgets.text("month", "")
file_month = dbutils.widgets.get("month")

bronze_dir = "/Volumes/main/lichess/vol-bronze/" + f"{file_month}/"
silver_dir = "/Volumes/main/lichess/vol-silver/" + f"{file_month}/"

dbutils.fs.rm(silver_dir, True)
dbutils.fs.mkdirs(silver_dir)

print(f"Parsing games from: {bronze_dir} \n to {silver_dir}")

# COMMAND ----------

from pyspark.sql.functions import (
    col,
    when,
    regexp_extract,
    monotonically_increasing_id,
    first,
    sum,
)
from pyspark.sql import Window
import re


def find_number_of_moves(moves_string):
    if moves_string is None:
        return 0

    # Search for the move number at the end of the string
    reversed_moves_string = moves_string[::-1]
    last_match = re.search(r"\ \.(\d+)|\ \.\.\.(\d+)", reversed_moves_string)

    if last_match:
        # Reverse the move number
        return int(last_match.group()[::-1].split(".")[0])
    else:
        return 0


def parse_games(file_name):
    df = spark.read.text(bronze_dir + file_name).filter(
        (col("value") != "") & (~col("value").like("%UTCTime%"))
    )

    # Rename "value" column to "Line"
    df = df.withColumnRenamed("value", "Line")

    # Extract the "Key" and "Value" columns based on "Line" column
    df = df.withColumn(
        "Key",
        when(col("Line").startswith("1."), "Moves").otherwise(
            regexp_extract(col("Line"), r"\[(.*?)\s", 1)
        ),
    ).withColumn(
        "Value",
        when(col("Line").startswith("1."), col("Line")).otherwise(
            regexp_extract(col("Line"), r'"(.*)"', 1)
        ),
    )

    # Add a column to identify the start of a game
    df = df.withColumn("StartOfGame", when(col("Key") == "Event", 1).otherwise(0))

    # Define a window spec for calculating cumulative sum
    windowSpec = Window.orderBy(monotonically_increasing_id())

    # Calculate the cumulative sum of "StartOfGame" to create "GameID"
    df = df.withColumn("GameID", sum("StartOfGame").over(windowSpec))

    # Define the list of columns for pivoting
    col_list = [
        "UTCDate",
        "Event",
        "TimeControl",
        "Opening",
        "ECO",
        "Site",
        "Termination",
        "Moves",
        "Result",
        "White",
        "WhiteTitle",
        "WhiteElo",
        "WhiteRatingDiff",
        "Black",
        "BlackTitle",
        "BlackElo",
        "BlackRatingDiff",
    ]

    # Pivot the DataFrame based on "GameID" and col_list
    df = df.groupBy("GameID").pivot("Key", col_list).agg(first("Value"))

    # Filter out uncomplete games due to chunking
    df = df.filter((col("GameID") > 0) & (col("GameID") < df.count() - 1))

    # Write games to silver dir
    df.write.partitionBy("UTCDate").mode("append").parquet(silver_dir)


# COMMAND ----------

from concurrent.futures import ThreadPoolExecutor
import os

# List all files in bronze directory
file_list = dbutils.fs.ls(bronze_dir)
file_names = [file.name for file in file_list]


# Function to parallelize the processing using ThreadPoolExecutor
def parallel_process(file_names):
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        executor.map(parse_games, file_names)


parallel_process(file_names)

# COMMAND ----------

# Display parsed games
result = spark.read.parquet(silver_dir)
display(result.count())
display(result)
