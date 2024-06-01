# Lichess-Spark-DataPipeline

## Description

This project is a data pipeline designed to extract and parse the monthly chess game datasets from the Lichess database. 
It utilizes Spark on Azure Databricks for efficient large-scale data processing.
The processed chess game data is used in my Guess the ELO game, where players aim to guess the ELO (rating) of a random chess game.
Due to the complexity of using Spark to efficiently handle the PGN and ZST format, I have written a post to describe the solution process here.

## Architecture
The data pipeline uses Azure Data Factory to orchestrate the data processing steps and Spark for data processing. Here are the detailed steps:

1. Copy data: Data Factory is used to copy the data file from the Lichess database to Azure Data Lake Storage Gen2. The data file is in a zipped format (ZST).
2. Decompress file: An Azure Databricks notebook decompresses the data file from zipped ZST format to PGN format.
3. Parse Games: Another Azure Databricks notebook parses the decompressed file into parquet format for distributed processing.
4. Sample Games: An Azure Databricks notebook samples the parsed data. This is done to collect games that meet the requirements of the Guess the ELO game.
5. Copy Games: The data is again copied from Azure Data Lake Storage Gen2 to Cosmos DB for application usage

![chess-app - Page 2 (2)](https://github.com/hieuimba/Lichess-Spark-DataPipeline/assets/89481020/8b36b059-25fc-4b7f-9597-d1cdf8b9655d)

## Technology Stack

The following technologies are used to build the project:
1. Azure Databricks: primary data processing engine utilizing Spark for big data workloads.
2. Data Factory: used to move data and orchestrate the data pipeline
3. Data Lake Storage Gen 2: efficient storage for raw and processed files
4. CosmosDB: noSQL database for retrieval of games

## Spark optimization
