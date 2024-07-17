# Lichess-Spark-DataPipeline

## Description
This project is a data pipeline designed to extract and parse monthly chess games from the Lichess database.

Liches is a popular chess platform that hosts millions of chess games every day. In order to use these games for your personal projects, you can download them for free from [the Lichess database](https://database.lichess.org/). However, extracting games from the database can be challenging due to the enormous size of the data files. This project aims to provide a solution in the form of a data pipeline capable of:
- Downloading and storing the monthly data files
- Parsing these files into tabular (Parquet) format
- Optionally filtering and/or aggregating games based on specified criteria

The pipeline uses Spark on Databricks for efficient large-scale data processing and can currently process 100 million games in about 90 minutes, depending on your data transfer speed and the chosen cluster size.

I use the data from this pipeline for my game "Guess The ELO". It's a game where you can test your chess knowledge and intuition by guessing the Elo or rating of a given chess match. If you are interested, feel free to check out the game here and [its repo](https://github.com/hieuimba/Guess-The-ELO) 

## Architecture
Here is the process diagram for this data pipeline, its main components are Spark Databricks for data processing, Azure Data Factory for orchestration, and ADLS2 for storage.
![chess-app - Page 2 (4)](https://github.com/user-attachments/assets/89c9022f-ee65-4ffc-adc9-438bd2830970)
The detailed steps are as follows:
1. **Copy Data:** Data Factory copies the compressed data file from the Lichess database to Azure Data Lake Storage Gen2. 
2. **Decompress File:** The downloaded ZST file is decompressed into PGN format.
3. **Parse Games:** Spark parses the PGN file, extracting individual chess games and storing them into Parquet format.
4. **Sample Games:** The parsed data is filtered and sampled to collect chess games that meet the requirements of the "Guess the ELO" game.
5. **Copy Games:** The final dataset is transferred from Azure Data Lake Storage Gen2 to Cosmos DB for efficient retrieval.

## Usage
To replicate this pipeline, ARM templates for Azure resources and Databricks notebooks are provided. 
Please note that additional setups will be required to configure the Databricks workspace, enable Unity Catalog, and ensure that resources can communicate together.

This data pipeline is customized for my Guess the ELO application. If you're only interested in converting the zipped chess games into Parquet format, you only need to use the "1-decompress-file" notebook and part of the "2-parse-game" notebook inside the [databricks folder](https://github.com/hieuimba/Lichess-Spark-DataPipeline/tree/main/databricks).
