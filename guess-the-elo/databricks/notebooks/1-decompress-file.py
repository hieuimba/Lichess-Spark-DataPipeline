# Databricks notebook source
# MAGIC %pip install zstandard

# COMMAND ----------

file_month = dbutils.widgets.get("month")

raw_dir = (
    "/Volumes/main/default/vol-raw/" + f"lichess_db_standard_rated_{file_month}.pgn.zst"
)
bronze_dir = "/Volumes/main/default/vol-bronze/" + f"{file_month}/"

dbutils.fs.rm(bronze_dir, True)
dbutils.fs.mkdirs(bronze_dir)

print(f"Decompressing file from: {raw_dir} \n to {bronze_dir}")

# COMMAND ----------

import zstandard as zstd

chunk_group = []
chunk_size = 1024 * 1024 * 32  # 32 MB chunks
group_size = 10 * 3  # Each group has 30 chunks (32 * 30 = 960MB)

# Open the compressed file for reading
with open(raw_dir, "rb") as ifh:
    dctx = zstd.ZstdDecompressor()

    # Create a decompression stream
    with dctx.stream_reader(ifh) as reader:
        chunk_index = 0
        group_index = 0

        while True:
            # Read a chunk of decompressed data
            chunk = reader.read(chunk_size)
            if not chunk:
                break

            # Append chunk to the chunk_group list
            chunk_group.append(chunk)
            chunk_index += 1

            # Check if chunk group is full
            if chunk_index % group_size == 0:
                # Define the chunk group file name
                chunk_group_file = bronze_dir + f"chunk_{group_index:04d}.pgn"

                # Write the chunk group
                with open(chunk_group_file, "wb") as ofh:
                    for chunk in chunk_group:
                        ofh.write(chunk)

                # Clear the chunk_group list for the next group
                chunk_group = []
                group_index += 1

        # Write any remaining chunks if exist
        if chunk_group:
            chunk_group_file = bronze_dir + f"chunk_{group_index:04d}.pgn"
            with open(chunk_group_file, "wb") as ofh:
                for chunk in chunk_group:
                    ofh.write(chunk)
