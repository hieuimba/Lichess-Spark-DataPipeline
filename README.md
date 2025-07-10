# Lichess-Spark-DataPipeline

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

## Description

This project is a data pipeline designed to extract and parse monthly chess games from the [Lichess database](https://database.lichess.org/).

Lichess is a popular online chess platform where millions of chess games are played every day. Each month, these games are compiled and published for free on the Lichess database, making them a great data source for chess-related projects. However, extracting and processing theses games poses two key challenges:

- The PGN format: The Portable Game Notation format doesn't have a natural indexing system, making it difficult to access specific games or perform filtering and aggregation. As a result, PGN games must first be parsed into a JSON or tabular format to support these operations.

- Size: Each monthly file from the database contains up to 100 million games which is about 350GB when decompressed. Processing files of this size can be time-consuming and expensive using traditional methods like Python.

This data pipeline aims to address these issues by providing the following features:

- Processing with Spark: Utilizing Apache Spark for parallel processing, the pipeline can handle 100 million games in just under 60 minutes.
- Parquet Format: Chess games are parsed from PGN to Parquet format, optimizing storage and data analysis capabilities.
- Flexible Transformations: Spark enables customizable, large-scale data transformations such as filtering and aggregation.
- Automated Processing: A serverless architecture enables automatic monthly processing of new data files.

This solution streamlines the handling of Lichess's monthly data files, making the data more accessible and manageable for developers and researchers.

![Frame 36359](https://github.com/user-attachments/assets/fd3f11cb-e94d-4a3e-afc5-d5d12009f913)

## Technologies used

- Spark Databricks for data processing
- Azure Data Factory (ADF) for orchestration, and
- Azure Data Lake Storage Gen2 (ADLS2) for storage.

## Architecture

See the process diagram for this data pipeline below:

![default-pipeline](https://github.com/user-attachments/assets/890c6434-f44d-4acb-973b-e54a56bdf7b1)

The pipline has four main stages:

1. **Copy Data:** Data Factory copies the compressed data file from the Lichess database to ADLS2.
2. **Decompress File:** The downloaded ZST file is decompressed into PGN format.
3. **Parse Games:** Spark parses the PGN file, extracting individual chess games and storing them into Parquet format.
4. **(Optional) Analyze Games:** Spark can be used to further filter, enhance, or aggregate the dataset.

## Spark Notebooks

The core of the data pipeline consists of several Spark notebooks, each responsible for a specific stage of processing:

- `1-decompress-file`: Extracts data from the Raw layer to the Bronze layer.
- `2-parse-games`: Parses data from Bronze to Silver layer, converting it from PGN to Parquet format
- `3-analyze-games`: Performs custom analysis on parsed games, saving results in the Gold layer. Input your custom Spark logic here to transform the data as needed.
- `0-run-all`: Orchestrates the execution of the above notebooks.

All the above notebooks can be found in [this folder](https://github.com/hieuimba/Lichess-Spark-DataPipeline/tree/main/default-pipeline/databricks/notebooks).

The `2-parse-games` notebook is the most important, handling the task of parsing PGN data into Parquet format. This process involves:

1. Reading Decompressed Data: The parsing process starts by reading the decompressed PGN data file into a DataFrame, where each row represents a single line from the original file.

2. Extracting Key and Value Information: Key and Value information are extracted from each line. For example, keys like Event, Site, Date, etc., are identified and their corresponding values are extracted.

3. Assigning GameIDs: A start-of-game identifier called GameID is assigned to the Event tag. This identifier effectively groups each Event line and the lines following it into a unique game:

![notebook](https://github.com/user-attachments/assets/c354bf75-6790-401c-a67c-07c605677c41)

4. Pivot Operation: Once every lines are assigned with their GameIDs, a pivot operation transforms the grouped lines with the same GameID into one game record. This results in a final table where each row represents a complete game with all its attributes:

![notebook2](https://github.com/user-attachments/assets/38b7dfe2-7db9-44c3-b16d-4668341853db)

This pivot operation, while necessary, can be computationally expensive as it requires sorting the entire dataset to assign the correct GameID to each line. To perform this sorting task, Spark needs to move (or shuffle) all records into a single partition. Considering the large size of the dataset, this can lead to massive data spills and significantly slow down processing time.

To address this issue, the pipeline implements two key optimizations:

- Data Chunking: In the `1-decompress-file` notebook, the data file is split into smaller, more manageable chunks during the decompression step. These chunks are then passed to the `2-parse-games` notebook for parsing. The idea is that each chunk will still be parsed in a single partition but since their size is now significantly smaller, Spark can handle them efficiently without the risk of spilling.
- Parallel Processing: The `concurrent.futures` module is utilized to process these chunks in parallel. This ensures optimal resource utilization across all available cores, with each core handling one data chunk at a time.

## Application

As an example of how this pipeline can be used and customized for specific applications, I use the data from this pipeline for my game "Guess The ELO". It's a chess-based quiz game where your goal is to guess the Elo rating of a chess match.

For “Guess the ELO”, I made some modifications to the default pipeline:

- Silver layer: Added additional filtering logic after parsing to select suitable chess games such as games with evaluation, with more than 20 moves, etc.
- Gold layer: Applied custom sampling logic to ensure ELO ratings are randomly distributed (as opposed to normally distributed). This makes sure that games from all ELO ranges have the same chance to be shown to the player.
- Added a final step to transfer the processed dataset into MongoDB for application usage.

![gte-pipeline](https://github.com/user-attachments/assets/c6b5b5eb-ffbb-4804-aa15-d9fcc69a0dce)

The modified notebooks are provided [here](https://github.com/hieuimba/Lichess-Spark-DataPipeline/tree/main/guess-the-elo-pipeline/databricks/notebooks).

Addtionally, if you're interested in "Guess the ELO", feel free to check out [the game here](https://hieuimba.itch.io/guess-the-elo) and [its source code](https://github.com/hieuimba/Guess-The-ELO).

## Usage

[You can find the setup guide here](https://github.com/hieuimba/Lichess-Spark-DataPipeline/blob/main/SETUP.md)
