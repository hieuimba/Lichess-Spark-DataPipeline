# Lichess-Spark-DataPipeline

## Description
This project is a data pipeline designed to extract and parse monthly chess games from the Lichess database.

Liches is a popular chess platform that hosts millions of chess games every day. These games are available for free on [the Lichess database](https://database.lichess.org/), which make them a great data source for chess-related projects. However, extracting the dataset can be challenging due to their enormous size. This project aims to provide a solution in the form of a data pipeline capable of:
- Downloading and storing the monthly data files
- Parsing these files into tabular (Parquet) format
- Optionally filtering and/or aggregating games based on specified criteria

The pipeline uses Spark Databricks to efficiently handle the large dataset. It can process up to 100 million games in about 90 minutes. Processing time may vary depending on your data transfer speed and cluster settings

I use the data from this pipeline for my game "Guess The ELO". It's a game where you can test your chess knowledge and intuition by guessing the rating of a given chess match. If you are interested, feel free to check out the game here and [its repo](https://github.com/hieuimba/Guess-The-ELO) 

## Architecture
Below is the process diagram for this data pipeline. 
![chess-app - Page 2 (4)](https://github.com/user-attachments/assets/89c9022f-ee65-4ffc-adc9-438bd2830970)

The main technologies used are:
- Spark Databricks for data processing
- Azure Data Factory for orchestration
- ADLS2 for storage.

The detailed steps are as follows:
1. **Copy Data:** Data Factory copies the compressed data file from the Lichess database to Azure Data Lake Storage Gen2. 
2. **Decompress File:** The downloaded ZST file is decompressed into PGN format.
3. **Parse Games:** Spark parses the PGN file, extracting individual chess games and storing them into Parquet format.
4. **Sample Games:** The parsed data is filtered and sampled to collect chess games that meet the requirements of the "Guess the ELO" game.
5. **Copy Games:** The final dataset is transferred from Azure Data Lake Storage Gen2 to Cosmos DB for efficient retrieval.

## Usage
For replicating this pipeline, ARM templates and Databricks notebooks are provided. 
Please note that additional setups will be required to configure the Databricks workspace, enable Unity Catalog, and ensure that resources can communicate together.

This data pipeline is customized for my Guess the ELO application. If you're only interested in converting the compressed chess games into Parquet format, you only need to use the "1-decompress-file" notebook and part of the "2-parse-game" notebook inside the [databricks folder](https://github.com/hieuimba/Lichess-Spark-DataPipeline/tree/main/databricks).
