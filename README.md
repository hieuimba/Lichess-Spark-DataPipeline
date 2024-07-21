# Lichess-Spark-DataPipeline

## Description
This project is a data pipeline designed to extract and parse monthly chess games from the Lichess database.

Liches is a popular chess platform that hosts millions of chess games every day. This diverse game collection is available for free on [the Lichess database](https://database.lichess.org/), making them a great data source for chess-related projects. However, these games are compressed and released as one large file every month, which can be challenging to extract due to its enormous size. This project provides a solution with a data pipeline capable of:
- Downloading and storing the monthly data files
- Parsing these files into a tabular (Parquet) format
- Filtering and/or aggregating games based on specified criteria

The pipeline uses Spark Databricks to efficiently handle the large dataset, capable of processing up to 100 million games in about 60 minutes.

I use the data from this pipeline for my game "Guess The ELO". In this game, you can test your chess knowledge and intuition by guessing the rating of a given chess match. If you're interested, feel free to check out the game and [its repo](https://github.com/hieuimba/Guess-The-ELO).

## Architecture
Below is the process diagram for this data pipeline. 
![chess-app - Page 2 (5)](https://github.com/user-attachments/assets/db1211af-9701-42e1-a60c-ffeefc3eff51)

The main components are:
- Spark Databricks for data processing
- Azure Data Factory for orchestration
- ADLS2 for storage.

The detailed steps are as follows:
1. **Copy Data:** Data Factory copies the compressed data file from the Lichess database to Azure Data Lake Storage Gen2. 
2. **Decompress File:** The downloaded ZST file is decompressed into PGN format.
3. **Parse Games:** Spark parses the PGN file, extracting individual chess games and storing them into Parquet format.
4. **Sample Games:** The parsed data is filtered and sampled to collect chess games that meet the requirements of the "Guess the ELO" game.
5. **Copy Games:** The final dataset is transferred from Azure Data Lake Storage Gen2 to Mongo DB for efficient retrieval.

## Usage
To replicate this pipeline, ARM templates for Azure resources and Databricks notebooks are provided. 
Please note that additional setups will be required to configure the Databricks workspace, enable Unity Catalog, and ensure that resources can communicate with each other.

This data pipeline is customized for my "Guess the ELO" application. If you're only interested in converting the compressed chess games into Parquet format, you only need to use the `1-decompress-file` notebook and part of the `2-parse-game` notebook inside the [databricks folder](https://github.com/hieuimba/Lichess-Spark-DataPipeline/tree/main/databricks).
