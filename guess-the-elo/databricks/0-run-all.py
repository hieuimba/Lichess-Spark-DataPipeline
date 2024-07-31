# Databricks notebook source
file_month = dbutils.widgets.get("month")

# COMMAND ----------
# test
dbutils.notebook.run("1-decompress-file", 0, {"clear_bronze": "false", "month":file_month})
dbutils.notebook.run("2-parse-games", 0, {"clear_silver": "false", "month":file_month})
dbutils.notebook.run("3-sample-games", 0, {"clear_gold": "false", "month":file_month})
