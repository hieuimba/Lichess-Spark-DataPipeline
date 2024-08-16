# Lichess-Spark-DataPipeline

## Description

This project is a data pipeline designed to extract and parse monthly chess games from the Lichess database.

Lichess is a popular online chess platform where millions of chess games are played every day. Each month, these games are compiled and published for free on the Lichess database, making them a great data source for chess-related projects. However, extracting and processing theses games can be challenging due to two key reasons:

- The PGN format: The Portable Game Notation format doesn't have a natural indexing system, making it difficult to access specific games or perform filtering and aggregation. As a result, PGN games must first be parsed into a JSON or tabular format to support these operations.

- Size: Each monthly file from the database contains up to 100 million games which is about 350GB when decompressed. Processing files of this size can be time-consuming and expensive using traditional methods like Python.

This data pipeline aims to address these issues by providing the following features:
- Processing with Spark: Leveraging Spark to process the data file in parallel results in a quick processing time of 60 minutes for 100 million games.
- Parquet Format: Chess games are parsed from PGN format into Parquet format, which is optimized for efficient storage and data analysis.
- Customizable Transformations: Using Spark, the pipeline allows for fully customizable transformation capabilities like filtering and aggregation at scale.
- Automated Processing: Monthly data files can be processed automatically every month using a serverless architecture.

This solution streamlines the handling of Lichess's monthly data files, making the data more accessible and manageable for developers and researchers.

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
The Spark notebooks below form the core of the data pipeline, managing the decompression, parsing, and analysis of chess game data. They can be found in [this folder](https://github.com/hieuimba/Lichess-Spark-DataPipeline/tree/main/default-pipeline/databricks/notebooks).

Here is a brief description of each notebook:

- `1-decompress-file`: Extracts the data file from Raw layer to Bronze layer
- `2-parse-games`: Parses data from Bronze to Silver layer, converting it from PGN to Parquet format
- `3-analyze-games`: Analyzes the parsed chess games and saves the result in the Gold layer. Input your custom Spark logic here to transform the data as needed
- `0-run-all`: Orchestrates the execution of the above notebooks.

In the `2-parse-games` notebook, the parsing process involves several key steps to transform the decompressed PGN data file into the Parquet format. Here's a detailed explanation:

1. Reading Decompressed Data: The parsing process starts by reading the decompressed PGN data file into a DataFrame, where each row represents a single line from the original file.

2. Extracting Key and Value Information: Key and Value information are extracted from each line. For example, keys like Event, Site, Date, etc., are identified and their corresponding values are extracted.

3. Assigning GameIDs: A start-of-game identifier called GameID is assigned to the Event tag. This identifier effectively groups each Event line and the lines following it into a unique game:

![notebook](https://github.com/user-attachments/assets/c354bf75-6790-401c-a67c-07c605677c41)

4. Pivot Operation: Once every lines are assigned with their GameIDs, a pivot operation transforms the grouped lines with the same GameID into one game record. This results in a final table where each row represents a complete game with all its attributes:

![notebook2](https://github.com/user-attachments/assets/38b7dfe2-7db9-44c3-b16d-4668341853db)



This pivot operation can be computationally expensive as it requires sorting the entire dataset to correctly assign the GameID to each line. In the background, Spark moves (or shuffles) the data into a single partition, which can lead to massive data spills and significantly slow down processing time due to the dataset's size.

To address this issue, the data file is split into smaller chunks during the decompression step in the `1-decompress-file` notebook. These chunks are then passed to the `2-parse-games` notebook for parsing. The idea is that each chunk will still be parsed in a single partition but since their size is now significantly smaller, Spark can handle them efficiently without spilling.

Additionally, the `concurrent.futures` module is used to process these chunks in parallel. This approach effectively distributes parallel jobs to all nodes at the same time, ensuring each node is occupied with one chunk of data at a time, optimizing for processing efficiency.

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

To recreate this data pipeline, a number of steps are required:

1. Deploy Azure resources using the provided ARM template.
2. Enable Unity Catalog in the created Databricks workspace.
3. Create external volumes in the Databricks workspace.
4. Import Databricks notebooks
5. Generate access token and create custom cluster policy for ADF
6. Configure ADF linked service.
7. Run pipeline.

The following sections provide a detailed breakdown of each step.

### 1. Deploy resources on Azure

Navigate to Azure portal's Template Deployment service, choose "Build your own template" and paste the provided [ARM template](https://github.com/hieuimba/Lichess-Spark-DataPipeline/blob/main/default-pipeline/ARMTemplate.json) there.

![step1](https://github.com/user-attachments/assets/8375fed7-cac0-4ed1-9f2a-2a686634062f)

This ARM template will deploy:

- ADLS2 storage account with four containers: raw, bronze, silver, gold
- Access Connector for Azure Databricks
- Empty Databricks workspace
- Data Factory containing the primary pipeline for this project.
  
![step1-1](https://github.com/user-attachments/assets/62e67efb-686d-41f7-8d5b-2bee6b15d8ba)

Provide names for these resources in the deployment screen and click "Create" to deploy.

### 2. Enable Unity Catalog

After the resources are deployed, you'll need to grant your Databricks workspace access to your storage account. This involves enabling [Unity Catalog](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/) by creating a Metastore and assigning it to your workspace. Here's how to do it:

2.1. Access the Databricks Account Console:

- In your Databricks workspace, click on your workspace name
- Select "Manage Account" from the dropdown menu

2.2. Create a Metastore (if necessary):

- Inside the Account Console, navigate to the "Data" tab
- If you don't already have a Metastore for your region, create a new one
- Choose a generic name for the Metastore, as there's a limit of one per region
- You don't need to provide an ADLS2 path, as you'll be using external tables.
  
![metastore](https://github.com/user-attachments/assets/d7469555-f756-4de4-9d1a-76affb7b1895)

2.3. Assign the Metastore to Your Workspace:

- After creating or selecting an existing Metastore, you'll see an option to assign it to your workspace in the next screen
- Select your workspace and confirm the assignment.

Note: A Metastore is a top-level container for managing data sources that's required by Unity Catalog so by assigning a Metastore, you're essentially enabling Unity Catalog functionality for your workspace.

### 3. Create External Volumes

Next, you'll need to create external volumes to access the data inside your raw, bronze, silver, and gold containers. Follow these steps:

3.1. Create Storage Credentials:

- In your Databricks workspace, navigate to the Catalog tab
- Under External Data, select "Storage Credentials"
- Click "Create Credential"
- Choose "Azure Managed Identity" as the authentication type
- Provide a name for the credential
- Enter the Connector ID of your Access Connector for Azure Databricks. (You can find this in the connector's details page in Azure.)
- Save the credential.
  
![image](https://github.com/user-attachments/assets/23cb1b58-58dc-4c56-b3ff-1f1f353e4c53)

3.2. Create External Locations:

- Still in the Catalog tab, under External Data, select "External Locations"
- Click "Create Location"
- Provide a name for the location (e.g., "location-raw")
- Enter the ADLS Gen2 path for the container (e.g., "abfss://raw@yourstorageaccount.dfs.core.windows.net/")
- Select the storage credential you created in step 1
- Save the location
- Repeat steps b-f for the other three containers: bronze, silver, and gold.
  
![image](https://github.com/user-attachments/assets/1f03f970-7497-4652-ad73-12c2dca6de7c)

3.3. Create a Schema:

- In the Catalog tab, under the main Catalog, click "Create" and select "Schema"
- Name the schema "lichess", don't specify the storage location
- Save the schema.

3.4. Create External Volumes:

- Within the "lichess" schema, click "Create" and select "Volume"
- Name the volume (e.g., "vol-raw")
- Select "External volume" as the volume type
- Choose the corresponding external location you created in step 2
- Save the volume
- Repeat steps a-e for the other three volumes: vol-bronze, vol-silver, and vol-gold.

![image](https://github.com/user-attachments/assets/20b597bb-dbab-4062-9028-6baac08d1557)

After this step, your schema/database should look like this:

![image](https://github.com/user-attachments/assets/648e8409-b185-489b-b1ab-c4e5240310d0)


### 4. Import Databricks Notebooks

Next, upload notebooks from the [notebooks folder](https://github.com/hieuimba/Lichess-Spark-DataPipeline/tree/main/default-pipeline/databricks/notebooks) to your Databricks workspace:

- Go to the Workspace tab, click "Import" to import from your local machine or provide the link to the files hosted on Github.
- Create a "lichess" folder in your Home directory and place the notebooks in it. Make sure that all the notebooks are in the same folder.

![image](https://github.com/user-attachments/assets/cd79a720-980b-480e-b22e-7f38fc7905ae)

- Review the notebooks to ensure that the paths to your volumes are correctly defined. For example, "/Volumes/main/lichess/vol-bronze/" requires the "vol-bronze" volume present inside the "lichess" schema under the "main" catalog. If you've been following the recommended naming conventions then you shouldn't need to make any changes.

![image](https://github.com/user-attachments/assets/713e94ef-0803-4405-abf9-753c32d655f1)

- Apply your custom Spark logic in the `3-analyze-games` notebook to transform the data further as needed. Alternatively, if you just want to parse the chess games into Parquet format, remove this notebook from the `0-run-all` notebook so it won't be run in the final pipieline.

<!-- For a detailed explanation of the development process behind these notebooks, please refer to this blog post: -->

### 5. Generate access token and create custom cluster policy

Your Databricks workspace should be ready, the next step is to generate the following parameter values for the Databricks linked service in ADF:

5.1. Generate access token

- In your Databricks workspace, go to Settings
- Select "Developer"
- Next to Access tokens, click "Manage" and select "Generate a new access token"
- Copy and save the new token.
  
![image](https://github.com/user-attachments/assets/c1bbe227-2e83-4e83-805f-083f4459d77f)

5.2. Create a custom cluster policy

- Go to the Compute tab in your Databricks workspace
- Under Policies, select "Create policy"
- Paste the content from the [sparkClusterPolicy file](c) into the policy definition field
- Save the policy
- Copy the policy ID for later use in Data Factory.
  
![image](https://github.com/user-attachments/assets/5afa14e2-2e87-49f4-9052-4f6bba43b2fb)

Note: This custom cluster policy defines a single-node cluster. This cluster type works best for this data pipeline because the `concurrent.futures` module is used to distribute tasks across cores which only works on the driver node.

### 6. Configure Data Factory

The last step is to configure Data Factory connection to Databricks:

- In Data Factory, go to Manage, click "Linked services"
- Select the "ls_databricks" linked service
- Provide the Databricks access token in the Access Token field. You might need to choose the cluster node type again, choose Standard_DS4_v2. 
  
![image](https://github.com/user-attachments/assets/05fdd227-c5f0-48c6-8951-e28e98746c10)

- Under Advanced, provide the policy ID
  
![image](https://github.com/user-attachments/assets/c75a1a39-8254-4a63-9f23-2bf818464365)


- Save the linked service
- Navigate to Author, locate "pl_main" under the Pipeline section
- Inside the "Process Data in Databricks" activity settings:
  - Under linked service, select the "ls_databricks" linked service
  - Browse for the `0-run-all` notebook in your Databricks workspace to populate the notebook path

![image](https://github.com/user-attachments/assets/a7056166-a55c-477e-b52f-9923d62b1e71)

- Save the pipeline.

Note: The default cluster type is an 8 core Standard_DS4_v2 cluster. In my tests, I've found that this cluster is the best option in terms of processing time and cost compared to the 4 and 16 cores versions. Upgrading to a larger cluster will improve processing time but comes with extra costs which might not be worth it.
  
### 7. Run pipeline
To trigger the pipeline, provide the Month parameter value which specifies the target month in "yyyy-MM" format (e.g., "2024-06" for June 2024). Afterwards, the data should be automatically downloaded, processed and stored in its respective containers.

Note: To automate execution for every month, a trigger can be set up. This can be a scheduled or tumbling window trigger based on your use case.
