# santiment_test
Code which connects to Santiment API and once an hour get metrics for Bitcoin and Ethereum and store them into a tables in Clockhouse. 
Choosed metrics: price_usd, volume_usd, marketcap_usd, price_volatility_1d

### Clone repo 
```
git clone git@github.com:SofiaVolk/santiment_test.git
```
### Prepare environment
```
bash ~/santiment_test/make_vanv.sh
```
### Prepare crontab
```
bash ~/santiment_test/cron.sh
```
### Prepare database
- more on https://hub.docker.com/r/clickhouse/clickhouse-server/
```
docker pull clickhouse/clickhouse-server
docker run -d -p 18123:8123 -p19000:9000 --name some-clickhouse-server --ulimit nofile=262144:262144 clickhouse/clickhouse-serve
```


### Check result in database
where <table_name> can be one of this: *price_usd, volume_usd, marketcap_usd, price_volatility_1d*
```
echo 'select * from <table_name>' | curl 'http://localhost:18123/' --data-binary @-
```
