# Databricks notebook source
file_month = dbutils.widgets.get("month")
clear_silver = dbutils.widgets.get("clear_silver")

bronze_dir = "/Volumes/main/default/vol-bronze/" + f"{file_month}/"
silver_dir = "/Volumes/main/default/vol-silver/" + f"{file_month}/"

if clear_silver == 'true':
    dbutils.fs.rm(silver_dir, True)
    dbutils.fs.mkdirs(silver_dir)

print(f"Parsing games from: {bronze_dir} \n to {silver_dir}")

# COMMAND ----------

from pyspark.sql.functions import col, when, regexp_extract, monotonically_increasing_id, first, sum, trim, regexp_replace, abs ,lit, floor, concat
from pyspark.sql import Window
from pyspark.sql.types import IntegerType

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
        (col("value") != "")
        & (~col("value").like("%UTCTime%"))
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
        "UTCDate", "Event", "TimeControl", "Opening", "ECO",
        "Site", "Termination", "Moves", "Result",
        "White", "WhiteTitle", "WhiteElo", "WhiteRatingDiff",
        "Black", "BlackTitle", "BlackElo", "BlackRatingDiff"
    ]

    # Pivot the DataFrame based on "GameID" and col_list
    df = df.groupBy("GameID").pivot("Key", col_list).agg(first("Value"))
    return df

def filter_games(df): 
    # Filter out uncomplete games due to chunking
    df = df.filter((col("GameID") > 0) & (col("GameID") < df.count() - 1))

    # Filter for games with evaluations & other conditions
    df = df.filter(
        (col("Moves").contains("eval")) & 
        (col("Event") != "Rated Correspondence game") & 
        (col("Termination").isin(["Normal", "Time forfeit"])) & 
        ((col("WhiteTitle").isNull()) | (col("WhiteTitle") != "BOT")) &
        ((col("BlackTitle").isNull()) | (col("BlackTitle") != "BOT"))
    )

    # Find the number of moves using the find_number_of_moves UDF
    find_number_of_moves_udf = udf(find_number_of_moves, IntegerType())
    df = df.withColumn("NumberOfMoves", find_number_of_moves_udf("Moves"))

    # Filter for games with >= 20 moves
    df = df.filter(col("NumberOfMoves") >= 20)

    # Cast Elo columns to int
    columns_to_cast = ["WhiteElo", "BlackElo", "WhiteRatingDiff", "BlackRatingDiff"]
    for column in columns_to_cast:
        df = df.withColumn(column, col(column).cast("int"))

    # Calculate AvgElo and round it down to the nearest 300 range
    df = df.withColumn("EloRange", (floor(((col("WhiteElo") + col("BlackElo")) / 2) / 300) * 300).cast("int"))

    # Adjust "EloRange" for special cases
    df = df.withColumn("EloRange", when(col("EloRange") <= 300, 0)
                                    .when(col("EloRange") > 3000, 3000)
                                    .otherwise(col("EloRange")))

    # Calculate the difference between White and Black's ELO
    df = df.withColumn("EloDiff", abs(col("WhiteElo") - col("BlackElo")))

    # Calculate the swing in ELO after the match ends
    if "WhiteRatingDiff" in df.columns and "BlackRatingDiff" in df.columns:
        df = df.withColumn("EloSwing", abs(col("WhiteRatingDiff") + col("BlackRatingDiff")))
    else:
        df = df.withColumn("EloSwing", lit(None).cast("int"))

    # Filter based on "EloDiff" and "EloSwing"
    df = df.filter(
        (col("EloDiff") <= 200) & 
        (col("EloSwing") <= 50)
    )

    # Add Opening Comment to Moves
    df = df.withColumn("Moves", concat(lit("{ "), col("ECO"), lit(" "),  col("Opening"), lit(" } "), col("Moves")))

    # Create Result Comment & add to Moves
    df = df.withColumn(
        "ResultComment",
        when(col("Result") == "1/2-1/2", "Draw")
        .when((col("Result") == "1-0") & (col("Termination") == "Time forfeit"), "White wins on time")
        .when((col("Result") == "0-1") & (col("Termination") == "Time forfeit"), "Black wins on time")
        .when((col("Result") == "1-0") & (col("Termination") == "Normal") & regexp_replace(col("Moves"), r"\[\%eval #\d+\]", "").contains("#"), "White wins by checkmate")
        .when((col("Result") == "0-1") & (col("Termination") == "Normal") & regexp_replace(col("Moves"), r"\[\%eval #\d+\]", "").contains("#"), "Black wins by checkmate")
        .when((col("Result") == "1-0") & (col("Termination") == "Normal") & ~regexp_replace(col("Moves"), r"\[\%eval #\d+\]", "").contains("#"), "White wins by resignation")
        .when((col("Result") == "0-1") & (col("Termination") == "Normal") & ~regexp_replace(col("Moves"), r"\[\%eval #\d+\]", "").contains("#"), "Black wins by resignation")
        .otherwise("End of Game")
    )
    df = df.withColumn("Moves", concat(col("Moves"), lit(" { "), col("ResultComment"), lit(" }")))

    # Trim Event
    df = df.withColumn("Event", trim(regexp_replace(df["Event"], "(http\S+)|(game|tournament|Rated|swiss)", "")))
    # Replace "Standard" with "Rapid" in "Event" column
    df = df.withColumn("Event", when(col("Event") == "Standard", "Rapid").otherwise(col("Event")))

    return df

def write_file(df):
    # Write games to silver dir
    df.write.partitionBy("UTCDate").mode("append").parquet(silver_dir)

def process_file(file_name):
    # Process games in the following order
    df = parse_games(file_name)
    df = filter_games(df) # This function filters games for Guess the ELO, can be omitted if needed
    write_file(df)

# COMMAND ----------

from concurrent.futures import ThreadPoolExecutor
import os

# List all files in bronze directory
file_list = dbutils.fs.ls(bronze_dir)
file_names = [file.name for file in file_list]

# Function to parallelize the processing using ThreadPoolExecutor
def parallel_process(file_names):
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        executor.map(process_file, file_names)

parallel_process(file_names)

# COMMAND ----------

# Display parsed games
result = spark.read.parquet(silver_dir)
display(result.count())
display(result)
