# Lichess-Spark-DataPipeline

## Description

This project is a data pipeline designed to extract and parse monthly chess games from the Lichess database.

Lichess is a popular chess platform where millions of chess games are played everyday. The Lichess database provides free access to these games in the form of file exports every month, making it a great data source for chess-related projects. This massive collection of games can provide valuable insights into chess statistics and trends, or enable other chess applications. However, the large size of each dataset presents significant challenges for users trying to access the chess game information. These challenges include:

- Parsing chess games from a large PGN (Portable Game Notation) file
- Converting and storing these games in a more accessible format
- Applying filters and/or aggregating games based on custom criteria

This data pipeline aims to address these issues by providing the following features:

- Automated processing of monthly data files using an Azure-based serverless architecture
- Using Spark Databricks to extract and parse the large dataset efficiently. The current processing time is about 60 minutes for 100 million games (one month's worth of data)
- Storing the parsed chess games in Parquet format for optimized storage and retrieval
- Fully customizable filtering and/or aggregation capabilities with Spark

This solution streamlines the handling of Lichess's monthly data files, making it more accessible and manageable for many users.

## Technologies used

- Spark Databricks for data processing
- Azure Data Factory for orchestration, and
- Azure Data Lake Storage Gen2 (ADLS2) for storage.

## Architecture

See the process diagram for this data pipeline below:

![chess-app - Copy of Page 2.png](https://prod-files-secure.s3.us-west-2.amazonaws.com/dc953b33-bf9b-41c6-b383-66eb071b14ac/95f68820-07fd-406b-ae7b-01369b593c30/chess-app_-_Copy_of_Page_2.png)

The detailed steps are:

1. **Copy Data:** Data Factory copies the compressed data file from the Lichess database to ADLS2.
2. **Decompress File:** The downloaded ZST file is decompressed into PGN format.
3. **Parse Games:** Spark parses the PGN file, extracting individual chess games and storing them into Parquet format.
4. **(Optional) Filter Games:** Spark can be used to further filter, aggregate, or sample the dataset.

## Application

Personally, I use the data from this pipeline in my game "Guess The ELO". It's a chess-based quiz game where your goal is to guess the correct Elo rating of a chess match. If you're interested, feel free to check out [the game here](https://hieuimba.itch.io/guess-the-elo) and [its source code](https://github.com/hieuimba/Guess-The-ELO).

For my purposes, I applied custom sampling logic to collect chess games for "Guess the ELO" in the gold layer and added a final step to move the processed dataset into MongoDB for application usage

https://github.com/user-attachments/assets/db1211af-9701-42e1-a60c-ffeefc3eff51

## Usage

To recreate this pipeline, you will need the following resources created in Azure:

- Azure Datalake Storage Gen 2 (ARM template provided)
- Azure Databricks (Notebooks provided)
- Azure Data Factory (ARM template provided)

The following sections details the setup required for each resource. 

1/ ADLS2

Deploy the pre-configured ADLS2 resource using the provided ARM template.

You can do that in the Azure portal through the Template Deployment service, choose “build your own template” then copy & paste the template into the code editor.

![Untitled](https://prod-files-secure.s3.us-west-2.amazonaws.com/dc953b33-bf9b-41c6-b383-66eb071b14ac/2c87a16a-51a7-4060-b093-479e5fe376ea/Untitled.png)

Once the storage account is created, make sure that:

- Hierarchical namespace is enabled. This is required by Databricks to enable Unity Catalog in the next step, and
- The following four containers are present: raw, bronze, silver, gold.

![Untitled](https://prod-files-secure.s3.us-west-2.amazonaws.com/dc953b33-bf9b-41c6-b383-66eb071b14ac/3d802be5-5629-43d8-9160-1383527dbc69/Untitled.png)

2/ Databricks - Setup Unity Catalog & connect to ADLS2

In this step, you will connect Databricks to ADLS2 through Unity Catalog. This is Databricks’ preferred way of managing data, and provides many benefits in terms of data governance and security. For more details, visit their documentation here: https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/

Enabling Unity Catalog requires a few steps:

- Create an Access Connector
- Create a Metastore
- Create external locations to connect to ADLS2 containers

First, find the Access Connector for Azure Databricks in the marketplace and create one. This is a managed account that will handle the authentication from Databricks to ADLS2.

![Untitled](https://prod-files-secure.s3.us-west-2.amazonaws.com/dc953b33-bf9b-41c6-b383-66eb071b14ac/827d4b30-0849-4714-bc55-19ff10fb0b7c/Untitled.png)

Give this account access to your ADLS2 storage by navigating to the IAM tab in the storage account, then assign the Storage Blob Data Contributor role to the connector.

Once this is done, you are ready to create a Metastore. This is essentially a top-level container that Databricks uses to manage your data sources. Inside your Databricks workspace, access the Account Console through the user menu under Manage Account.

![Untitled](https://prod-files-secure.s3.us-west-2.amazonaws.com/dc953b33-bf9b-41c6-b383-66eb071b14ac/7f2099b6-c184-43c2-846b-af6d9c3b6c27/Untitled.png)

Navigate to the Data tab and create a new Metastore

![Untitled](https://prod-files-secure.s3.us-west-2.amazonaws.com/dc953b33-bf9b-41c6-b383-66eb071b14ac/ea234d56-93b5-443b-ae39-8d4127c23da8/Untitled.png)

Since metastores are limited to one per region, I recommend you give it a generic name. Here you don’t need to provide an ADLS2 path since you’ll be using external tables. However, if you want to have managed tables, I recommend providing the path to a “master” ADLS2 account in a separate resource group since this metastore is intended for managing data for all projects in this region. More information on external vs managed tables here: https://learn.microsoft.com/en-us/azure/databricks/tables/

In the following screen, assign the metastore to your workspace to enable UC in the workspace.

Next, you’ll need to create external locations in your Databricks workspace to connect it to the containers inside your ADLS2 storage account. In your Databricks workspace, inside the Catalog tab, you should now see an External Data menu that lets you set up storage credentials and external locations.

First, create a new storage credential and link it to the Access Connector for Azure Databricks account that you created above. The Access connector ID is the resource ID found in the connector’s details.

![Untitled](https://prod-files-secure.s3.us-west-2.amazonaws.com/dc953b33-bf9b-41c6-b383-66eb071b14ac/61762165-9e9c-43cc-be41-a3437d282d0c/Untitled.png)

Next, create four external locations to reference each of your containers created in ADLS2: raw, bronze, silver, gold.

![Untitled](https://prod-files-secure.s3.us-west-2.amazonaws.com/dc953b33-bf9b-41c6-b383-66eb071b14ac/8fd21c42-a972-4f13-bde2-154eeecd1362/Untitled.png)

Now your Databricks workspace should be able to read and write data to the ADLS2 containers. You can reference containers in your notebooks by using the following path:

```python
dbutils.fs.ls("abfss://<container>@<storage-account>.dfs.core.windows.net")
```

3/ Databricks - Create notebooks

Copy the notebooks provided in the databricks-notebooks-default folder into the Home folder of your Databricks workspace (or any folder structure you’d like). They are ready for use as is, but I recommend you review them to make sure you understand what the code does. 

There are 4 notebooks:

- “1-decompress-file”: Extracts the data file from Raw layer to Bronze layer.
- “2-parse-games”: Parse the extracted data into Parquet from Bronze to Silver layer.
- “3-filter-games”: Boilerplate notebook. Apply custom Spark logic here to filter, modify, or aggregate the dataset to your liking.
- “0-run-all”: Chains the above notebooks to be run sequentially. The following ADF pipeline will use this notebook to effectively call all three notebooks above.

For more information on the development process of the provided notebooks, please visit this blog post

4/ Data Factory 

The last step is to configure the monthly data pipeline. 

To begin, deploy the ADF resource using the provided ARM template. To do this on the Azure portal, you’ll need to create the Data Factory instance first then use the “Import ARM template” feature inside the application to update it.

![Untitled](https://prod-files-secure.s3.us-west-2.amazonaws.com/dc953b33-bf9b-41c6-b383-66eb071b14ac/f04d5a37-7ed6-4dea-863d-bff73ef0f724/Untitled.png)

When setting up your ADF resource, you’ll need to provide the following keys: 

- The storage account key to connect ADF to the storage account created in step 1
- The Databricks access token to connect ADF to the Databricks workspace created in step 2

These keys can be generated in the settings of the respective resources. 

Also make sure that the storage account URL reflects your storage account name.

![Untitled](https://prod-files-secure.s3.us-west-2.amazonaws.com/dc953b33-bf9b-41c6-b383-66eb071b14ac/fbaf0e09-8153-47ab-b9e0-cd49bda7a9ff/Untitled.png)

Once the ADF resource has been updated, navigate to the Author section, under Pipelines there should be a pl_main pipeline.

![Untitled](https://prod-files-secure.s3.us-west-2.amazonaws.com/dc953b33-bf9b-41c6-b383-66eb071b14ac/48c9d902-833b-43ac-b437-b2a19e3c2481/Untitled.png)

This is the main pipeline that contains all the data activities for this project. These activities are:

- Copy from Lichess to Raw: Downloads the data file from the Lichess database to the raw Layer
- Process Data in Databricks: Trigger the “0-process-all” notebook which contains the 3 child notebooks to process data from raw to bronze, silver and gold Layer

To trigger the pipeline, provide the following values for the parameters:

- Month: Specifies the month of the data file to process using the “yyyy-MM” format. For example input 2024-06 to process June 2024 data.
- DatabricksWorkspaceURL: The URL of your Databricks workspace. It will be something like this:
"https://adb-XXX.azuredatabricks.net/”.
- DatabricksNotebookPath: The notebook path to the  “0-process-all” notebook. It will be something like this: “/Users/Your-Name/0-run-all”.

Couple of things to keep in mind before you trigger the pipeline:

- Feel free to replace the DatabricksWorkspaceURL and DatabricksNotebookPath parameters with permanent values for your use case.
- I’ve set up the default Databricks cluster to be a 4 core cluster with 1 worker. This can be changed in the Databricks linked service.
- A trigger can be set up to run this pipeline on a schedule. This can be a scheduled or tumbling window trigger based on your use case.
