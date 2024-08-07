# Databricks notebook source
dbutils.widgets.text("month", "")
file_month = dbutils.widgets.get("month")

# COMMAND ----------

dbutils.notebook.run("1-decompress-file", 0, {"month": file_month})
dbutils.notebook.run("2-parse-games", 0, {"month": file_month})
dbutils.notebook.run("3-analyze-games", 0, {"month": file_month})
