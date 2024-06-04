# Databricks notebook source
file_month = dbutils.widgets.get("month")
clear_gold = dbutils.widgets.get("clear_gold")

silver_dir = "/Volumes/main/default/vol-silver/" + f"{file_month}/"
gold_all_keys_dir =  "/Volumes/main/default/vol-gold/Keys"

gold_games_dir = "/Volumes/main/default/vol-gold/Games/" + f"{file_month}/"
gold_keys_dir = "/Volumes/main/default/vol-gold/Keys/" + f"{file_month}/"
gold_keys_consolidated_dir = "/Volumes/main/default/vol-gold/Keys/Consolidated"

if clear_gold == 'true':
    dbutils.fs.rm(gold_games_dir, True)
    dbutils.fs.rm(gold_keys_dir, True)
    dbutils.fs.mkdirs(gold_games_dir)
    dbutils.fs.mkdirs(gold_keys_dir)

print(f"Sampling games from: {silver_dir} \n to {gold_games_dir}")

# COMMAND ----------

# This notebook is specific to Guess the ELO, can be omitted if not needed

from pyspark.sql.functions import col, lit, min, concat, row_number, max
from pyspark.sql import Window
from concurrent.futures import ThreadPoolExecutor, as_completed
from pyspark.sql import DataFrame

df = spark.read.parquet(silver_dir)

grouped_df = df.groupBy("Event", "EloRange").count()

# Get the distinct event groups as a list
event_groups = grouped_df.select("Event").distinct().collect()
event_groups = [row["Event"] for row in event_groups]

# Initialize an empty DataFrame with the same schema as df
all_df = spark.createDataFrame([], schema=df.schema)

def process_event(event: str) -> DataFrame:
    # Process each Event separately
    df_group = grouped_df.where(col("Event") == event)

    # Get the smallest count of games across all EloRanges 
    min_count = df_group.agg(min(col('count'))).collect()[0][0]

    # Calculate the sample fraction - ensure that counts across all EloRanges are equal to the min_count
    df_group = df_group.withColumn('sample_fraction', lit(min_count) / col('count'))

    # Extract the columns "EloRange" and "sample_fraction" and collect them as a list of rows
    rows = df_group.select('EloRange', 'sample_fraction').collect()

    # Construct the sample dictionary
    sample_dict = {row['EloRange']: row['sample_fraction'] for row in rows}

    # Sample the source df
    sampled_df = df.where(col("Event") == event)
    sampled_df = sampled_df.sampleBy("EloRange", fractions=sample_dict, seed=10)
    
    return sampled_df

# Use ThreadPoolExecutor to process each event group in parallel
with ThreadPoolExecutor() as executor:
    futures = {executor.submit(process_event, event): event for event in event_groups}

    for future in as_completed(futures):
        event = futures[future]
        try:
            result_df = future.result()
            all_df = all_df.union(result_df)
        except Exception as exc:
            print(exc)


# Add a 'NumericGameID' column using the row_number function
window_spec = Window.orderBy('Event')
all_df = all_df.withColumn('NumericGameID', row_number().over(window_spec))

# Replace GameID with NumericGameID, rename to ID
all_df = all_df.withColumn('GameID', concat(lit(file_month), lit('-'), col('NumericGameID')))
all_df = all_df.withColumn('ID', col('GameID'))

# Write games to gold dir
all_df.write.partitionBy('Event','EloRange').mode("overwrite").parquet(gold_games_dir)

# Display result
all_df_result = all_df.groupBy("Event", "EloRange").count()
display(all_df_result)

# Create a key df based on sampled games
key_df = all_df.groupBy("Event").agg(min("NumericGameID").alias("MinGameID"), max("NumericGameID").alias("MaxGameID"))
key_df = key_df.withColumn("Month", lit(file_month))
key_df = key_df.withColumn("KeyID", concat(lit(file_month), lit("-"), lit(col("Event"))))

# Write keys to gold dir
key_df.write.mode("overwrite").parquet(gold_keys_dir)

display(key_df)

# COMMAND ----------

from functools import reduce
from pyspark.sql import DataFrame
from pyspark.sql.functions import struct, collect_list, create_map,col

# Function to read all folders in keys_path and combine them into one DataFrame
def read_and_combine_dataframes(keys_path):
    # List all folders in keys_path
    folders = [file.path for file in dbutils.fs.ls(keys_path) if 'Consolidated' not in file.path]
    print(folders)
    
    # Read each folder as a DataFrame and store them in a list
    dfs = [spark.read.parquet(folder) for folder in folders]
    
    # Combine all DataFrames into one DataFrame using union
    combined_df = reduce(DataFrame.union, dfs)
    
    return combined_df

# Read and combine all game DataFrames
df = read_and_combine_dataframes(gold_all_keys_dir)

df = df.withColumnRenamed("MinGameID", "Min")
df = df.withColumnRenamed("MaxGameID", "Max")

# Create a struct column for each month
df = df.withColumn("Range", struct("Min", "Max")) \
       .drop("Min", "Max")

# Group by Event and collect Range structs into a list
df = df.groupBy("Event").agg(collect_list(struct("Month", "Range")).alias("GameIDs"))

# Create ID column
df = df.withColumn("ID", col("Event"))

# Write consolidated keys to gold dir
df.write.mode("overwrite").json(gold_keys_consolidated_dir)

display(df)
