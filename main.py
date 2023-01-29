import san
import logging
import clickhouse_connect


logging.basicConfig(format='%(levelname)s - %(asctime)s: %(message)s', level=logging.INFO)


def get_metrics(metric_name, slugs_list, from_date="utc_now-1h", to_date="utc_now", interval="5m"):
    """
    Makes a request to SanAPI to get <metric_name> for all slugs in <slugs_list>
    :param metric_name: list of metrics to request
    :param slugs_list: list of assets
    :param from_date: from which day to return the activity
    :param to_date: till which day to return the activity
    :param interval: the intervals that should be returned
    :return: pandas dataframe
    """

    return san.get_many(
        metric_name,
        slugs=slugs_list,
        from_date=from_date,
        to_date=to_date,
        interval=interval
        )


def write_to_db(client, table, df):
    """
    Writes dataframe into <table>;
    checks whether table exists, if yes - filters data to get only new values,
    otherwise - creates table and writes full unfiltered dataframe
    :param client: connection to clickhouse
    :param table: name of the table to write into
    :param df: dataframe to write
    :return:
    """
    # check whether table exists
    result = client.query(f"SHOW TABLES FROM default LIKE '{table}'").result_rows
    result = [item for i in result for item in i]

    if table not in result:
        client.command(f"CREATE TABLE {table} (datetime DateTime , bitcoin Float64, ethereum Float64) ENGINE TinyLog")
        logging.info(f"Table '{table}' was created")

    # write data into table
    df.loc[:, 'datetime'] = df.index
    client.insert_df(table, df)


if __name__ == '__main__':
    metrics = ["price_usd", "volume_usd", "marketcap_usd", "price_volatility_1d"]
    slugs = ["bitcoin", "ethereum"]

    # create connection
    client = clickhouse_connect.get_client(host='localhost', port='18123', username='default')

    for metric in metrics:
        # get full metric data frame for current date
        try:
            df = get_metrics(metric, slugs)
            logging.info(f"Received data for {metric} metric")
            print(df)
        except Exception as e:
            logging.error(f"SanAPI request failed: {e}")
            continue

        # store final metric data frame to database
        try:
            write_to_db(client, metric, df)
            logging.info(f"Successfully stored data into '{metric}' table")
        except Exception as e:
            logging.error(f"Write to DB failed: {e}")
        finally:
            client.close()


