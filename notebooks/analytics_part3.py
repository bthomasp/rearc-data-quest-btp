# Databricks notebook source
# MAGIC %md
# MAGIC ####Section A — Mean & Stddev (2013–2018)

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Database: rearc_quest
# MAGIC SELECT
# MAGIC   AVG(population)         AS mean_population,
# MAGIC   STDDEV_SAMP(population) AS stddev_population
# MAGIC FROM rearc_quest.us_population_raw
# MAGIC WHERE year BETWEEN 2013 AND 2018;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ####Section B — Best year per series (sum of quarterly values):

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH q AS (
# MAGIC   SELECT TRIM(series_id) AS series_id,
# MAGIC          year,
# MAGIC          CAST(value AS DOUBLE) AS value
# MAGIC   FROM rearc_quest.pr_current
# MAGIC   WHERE period IN ('Q01','Q02','Q03','Q04')
# MAGIC ),
# MAGIC s AS (
# MAGIC   SELECT series_id, year, SUM(value) AS annual_value
# MAGIC   FROM q
# MAGIC   GROUP BY series_id, year
# MAGIC )
# MAGIC SELECT series_id, year, annual_value AS value
# MAGIC FROM (
# MAGIC   SELECT s.*,
# MAGIC          ROW_NUMBER() OVER (PARTITION BY series_id
# MAGIC                             ORDER BY annual_value DESC, year DESC) AS rn
# MAGIC   FROM s
# MAGIC ) t
# MAGIC WHERE rn = 1
# MAGIC ORDER BY series_id;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ####Section C — PRS30006032 / Q01 + population join:

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   TRIM(c.series_id) AS series_id,
# MAGIC   c.year,
# MAGIC   c.period,
# MAGIC   CAST(c.value AS DOUBLE) AS value,
# MAGIC   p.population
# MAGIC FROM rearc_quest.pr_current c
# MAGIC LEFT JOIN rearc_quest.us_population_raw p
# MAGIC   ON p.year = c.year
# MAGIC WHERE TRIM(c.series_id) = 'PRS30006032'
# MAGIC   AND c.period = 'Q01'
# MAGIC ORDER BY c.year;
# MAGIC