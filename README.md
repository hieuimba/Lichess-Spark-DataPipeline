# Lichess-Spark-DataPipeline

## Description

This project is a data pipeline designed to extract and parse monthly chess games from the Lichess database.

Lichess is a popular online chess platform where millions of chess games are played every day. Each month, these games are compiled and published on the Lichess database for public use, making them a great data source for chess-related projects. However, extracting and processing these games poses several challenges due to the dataset's large size. Key challenges include:

- Parsing chess games from a large PGN (Portable Game Notation) file
- Converting and storing these games in a more accessible format
- Applying custom transformations like filters, and aggregation on a large collection of games

This data pipeline aims to address these issues by providing the following features:

- Automated processing of monthly data files using an Azure-based serverless architecture.
- Efficient extraction and parsing of large volumes of chess games using Spark Databricks. The current processing time is about 60 minutes for 100 million games (one month's worth of data).
- Storage of parsed games in Parquet format, optimizing for storage and retrieval
- Fully customizable filtering and aggregation capabilities leveraging Spark's functionality.

This solution streamlines the handling of Lichess's monthly data files, making them more accessible and manageable for developers and researchers.

## Technologies used

- Spark Databricks for data processing
- Azure Data Factory (ADF) for orchestration, and
- Azure Data Lake Storage Gen2 (ADLS2) for storage.

## Architecture

See the process diagram for this data pipeline below:
![chess-app - Copy of Page 2 (1).png](https://prod-files-secure.s3.us-west-2.amazonaws.com/dc953b33-bf9b-41c6-b383-66eb071b14ac/c2c43bd0-142e-4486-8be6-ebdb52989703/chess-app_-_Copy_of_Page_2_(1).png)
The detailed steps are:

1. **Copy Data:** Data Factory copies the compressed data file from the Lichess database to ADLS2.
2. **Decompress File:** The downloaded ZST file is decompressed into PGN format.
3. **Parse Games:** Spark parses the PGN file, extracting individual chess games and storing them into Parquet format.
4. **(Optional) Analyze Games:** Spark can be used to further filter, enhance, or aggregate the dataset.

## Application

As an example of how this pipeline can be customized for specific applications, I use the data from this pipeline for my game "Guess The ELO". It's a chess-based quiz game where your goal is to guess the correct Elo rating of a chess match.

For “Guess the ELO”, I made some modifications to the data pipeline:

- Silver layer: Added additional filtering logic after parsing to select suitable chess games such as games with evaluation, more than 20 moves, etc.
- Gold layer: Applied custom sampling logic to ensure random distribution of chess games. This makes sure that games from all ELO ranges have the same chance to be chosen.
- Added a final step to transfer the processed dataset into MongoDB for application usage.
https://github.com/user-attachments/assets/db1211af-9701-42e1-a60c-ffeefc3eff51
The modified notebooks along with the Data Factory code are provided [here](https://github.com/hieuimba/Lichess-Spark-DataPipeline/tree/main/guess-the-elo).

If you're interested in "Guess the ELO", feel free to check out [the game here](https://hieuimba.itch.io/guess-the-elo) and [its source code](https://github.com/hieuimba/Guess-The-ELO).

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

Navigate to Azure portal's Template Deployment service, choose "Build your own template" and paste the provided [ARM template](https://github.com/hieuimba/Lichess-Spark-DataPipeline/blob/main/default-pipeline/ARMTemplate.json).
![Untitled](https://prod-files-secure.s3.us-west-2.amazonaws.com/dc953b33-bf9b-41c6-b383-66eb071b14ac/2c87a16a-51a7-4060-b093-479e5fe376ea/Untitled.png)
This ARM template will deploy:

- ADLS2 storage account with four containers: raw, bronze, silver, gold
- Access Connector for Azure Databricks
- Empty Databricks workspace
- Data Factory containing the primary pipeline for this project.

Provide names for these resources in the deployment screen and click "Create" to deploy.

### 2. Enable Unity Catalog

After the resources are deployed, you'll need to grant your Databricks workspace access to the storage account. This involves enabling [Unity Catalog](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/) by creating a Metastore and assigning it to your workspace. Here's how to do it:

2.1. Access the Databricks Account Console:

- In your Databricks workspace, click on your workspace name
- Select "Manage Account" from the dropdown menu

2.2. Create a Metastore (if necessary):

- Inside the Account Console, navigate to the "Data" tab
- If you don't already have a Metastore for your region, create a new one
- Choose a generic name for the Metastore, as there's a limit of one per region
- You don't need to provide an ADLS2 path, as you'll be using external tables.

2.3. Assign the Metastore to Your Workspace:

- After creating or selecting an existing Metastore, you'll see an option to assign it to your workspace
- Select your workspace and confirm the assignment.

Note: A Metastore is a top-level container that's required by Databricks to manage your data sources so by assigning a Metastore, you're essentially enabling Unity Catalog functionality for your workspace.

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

3.2. Create External Locations:

- Still in the Catalog tab, under External Data, select "External Locations"
- Click "Create Location"
- Provide a name for the location (e.g., "raw")
- Enter the ADLS Gen2 path for the container (e.g., "abfss://raw@yourstorageaccount.dfs.core.windows.net/")
- Select the storage credential you created in step 1
- Save the location
- Repeat steps b-f for the other three containers: bronze, silver, and gold.

3.3. Create a Schema:

- In the Catalog tab, under the main Catalog, click "Create" and select "Schema"
- Name the schema "lichess"
- Save the schema.

3.4. Create External Volumes:

- Within the "lichess" schema, click "Create" and select "Volume"
- Name the volume (e.g., "vol-raw")
- Select "External volume" as the volume type
- Choose the corresponding external location you created in step 2
- Save the volume
- Repeat steps a-e for the other three volumes: vol-bronze, vol-silver, and vol-gold.

### 4. Import Databricks Notebooks

Next, upload notebooks from the `default-pipeline/databricks/notebooks` folder to your Databricks workspace:

- Go to the Workspace tab, click "Import" to import the notebooks.
- Place the notebooks in your Home folder. If you use a different location, make sure that all the notebooks are in the same folder.
- Review the notebooks and make sure that the paths to your volumes are correctly defined. For example, "/Volumes/main/lichess/vol-raw/" refers to your "vol-raw" volume inside the "lichess" schema under the "main" catalog.

Here is a brief description of what each notebook does:

- `1-decompress-file`: Extracts the data file from Raw layer to Bronze layer.
- `2-parse-games`: Parses data from Bronze to Silver layer, converting from PGN to Parquet format.
- `3-analyze-games`: Template for custom Spark logic (filtering, enhancing, or aggregating data)
- `0-run-all`: Orchestrates the execution of the above notebooks

These notebooks form the core of the data pipeline, managing the decompression, parsing, and analysis of chess game data. They're designed to be executed as a single activity in Azure Data Factory.

For a detailed explanation of the development process behind these notebooks, please refer to this blog post:

### 5. Generate access token and create custom cluster policy

Your Databricks workspace should be ready, the next step will be to generate the following parameter values for the Databricks linked service in Data Factory:

4.1. Generate access token

- In your Databricks workspace, go to Settings
- Select "Developer"
- Next to Access tokens, click "Manage" and select "Generate a new access token"
- Copy and securely store the new token (it won't be displayed again)

4.2. Create a custom cluster policy

- Go to the Compute tab in your Databricks workspace
- Under Policies, select "Create policy"
- Paste the content from the sparkClusterPolicy file into the policy definition
- Save the policy
- Copy the policy ID for later use in Data Factory

Note: This custom cluster policy defines a single-node cluster. This type of cluster works best for this project because the PGN file format doesn't fully support Spark's distributed computing capabilities.

### 6. Configure Data Factory

The last step is to configure Data Factory connection to Databricks:

- In Data Factory, go to Manage, click "Linked services"
- Select the "ls_databricks" linked service
- Provide the Databricks access token and policy ID from step 5
- Save the linked service
- Navigate to Author, locate "pl_main" under the Pipeline section
- Inside the "Process Data in Databricks" activity settings:
  - Under linked service, select the "ls_databricks" linked service
  - Browse for the `0-run-all` notebook in your Databricks workspace to populate the notebook path.
- Save the pipeline.

This "pl_main" pipeline orchestrates all the data activities, from downloading games from Lichess to parsing them in Databricks.

To trigger the pipeline, provide the Month parameter value which specifies the target month in "yyyy-MM" format (e.g., "2024-06" for June 2024). Afterwards, the data should be automatically downloaded, processed and stored in its respective containers.

Note: To automate execution, a trigger can be set up. This can be a scheduled or tumbling window trigger based on your use case.
