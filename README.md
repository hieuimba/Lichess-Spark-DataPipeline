# Lichess-Spark-DataPipeline

## Description
This project is a data pipeline designed to extract and parse monthly chess games from the Lichess database.

The Lichess database provides free access to millions of chess games played on Lichess each month, making it a great data source for chess-related projects. This massive collection of games can provide valuable insights into chess statistics and trends, or enable applications that rely on chess data. However, the sheer volume of each dataset presents significant challenges for users trying to extract and access the information. These challenges include:
- Parsing chess games from a large PGN (Portable Game Notation) file
- Converting and storing these games in a more accessible format
- Applying filters and/or aggregating games based on specific criteria
  
This data pipeline aims to address these issues by providing the following features:
- Automated processing of monthly data files using an Azure-based serverless architecture
- Using Spark Databricks to extract and parse the large dataset efficiently. The current processing is about 60 minutes for 100 million games (one month's worth of data)
- Fully customizable filtering and/or aggregation capabilities with Spark once the games have been parsed
- Games are stored in Parquet format for optimized storage and retrieval

This solution streamlines the handling of Lichess's monthly data files, making it more accessible and manageable for many users.

## Technologies used
- Spark Databricks for data processing
- Azure Data Factory for orchestration, and
- Azure Data Lake Storage Gen2 (ADLS2) for storage.
  
## Architecture
See the process diagram for this data pipeline below: 
![chess-app - Page 2 (5)](https://github.com/user-attachments/assets/db1211af-9701-42e1-a60c-ffeefc3eff51)
The detailed steps are as follows:
1. **Copy Data:** Data Factory copies the compressed data file from the Lichess database to ADLS2. 
2. **Decompress File:** The downloaded ZST file is decompressed into PGN format.
3. **Parse Games:** Spark parses the PGN file, extracting individual chess games and storing them into Parquet format.
4. **Sample Games:** The parsed data is filtered and sampled to collect chess games for "Guess the ELO".
5. **Copy Games:** The final dataset is transferred from ADLS2 to MongoDB for application usage.

## Application
Once the chess games are parsed into Parquet format, Spark can be used to analyze or modify the data as you see fit. 

I use the data from this pipeline in my game "Guess The ELO". It's a chess-based quiz game where your goal is to guess the correct Elo rating of a chess match. If you're interested, feel free to check out [the game here](https://hieuimba.itch.io/guess-the-elo) and [its source code](https://github.com/hieuimba/Guess-The-ELO).

## Usage
To replicate this pipeline:

1. Use the provided ARM templates for Azure resources.
2. Set up Data Factory, ADLS2 and a Databricks workspace
3. Configure the Databricks workspace and enable Unity Catalog.
4. Ensure proper communication between all resources.
5. Utilize the Databricks notebooks in the databricks folder.
6. 



To replicate this pipeline, ARM templates for Azure resources and Databricks notebooks are provided. 
Please note that additional setups will be required to configure the Databricks workspace, enable Unity Catalog, and ensure that resources can communicate with each other.

This data pipeline is customized for my "Guess the ELO" application. If you're only interested in converting the compressed chess games into Parquet format, you only need to use the `1-decompress-file` notebook and part of the `2-parse-game` notebook inside the [databricks folder](https://github.com/hieuimba/Lichess-Spark-DataPipeline/tree/main/databricks).
