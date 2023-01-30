# santiment_test

## Task 1
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


## Task 2
Given the tweet data examples from [Twitter API v.2.0](https://developer.twitter.com/en/docs/twitter-api/data-dictionary/example-payloads) suggest a solution which would allow to store and analyze textual and numerical features of tweets in a more efficient way.


To store and analyze textual and numerical features of tweets in a more efficient way I propose to define some logical steps:

### 1. Define all possibly useful textual and numerical features from new API version
Possibly useful textual and numerical features from new API version 
(https://developer.twitter.com/en/docs/twitter-api/data-dictionary/using-fields-and-expansions
and
https://developer.twitter.com/en/docs/twitter-api/data-dictionary/example-payloads):
```
	Numerical
- root_level fields 
id(default) - to identify tweet
author_id - to identify the author of post
conversation_id - to restore all chain of tweets
public_metrics(retweet_count, reply_count, like_count) - to get reaction metrics to this post - is it popular opinion/ is the reaction to this post is positive or negative/ is the tweet overall mood positive or negative(https://academy.santiment.net/metrics/sentiment-metrics/#sentiment-score:~:text=Sentiment-,Score,-We%20trained%20a)
created_at - to trace the relevance of content in terms of time scale
referenced_tweets.id - also to restore all chain of tweets and reduce number of requests
geo.place_id - to divide opinions by territory sign (https://developer.twitter.com/en/docs/twitter-api/expansions#:~:text=geo.-,place_id,-Sample%20Request
)

- child objects fields (get via fields and expansions parameters)
includes.tweets.id
includes.tweets.author_id
includes.tweets.conversation_id
includes.tweets.public_metrics(retweet_count, reply_count, like_count)
includes.tweets.created_at
includes.tweets.geo.place_id 


	Textual
- root_level fields
text(default) - content itself
lang - to make text parsing easier and to get language feature into ml-model

- child objects fields
includes.tweets.text
includes.tweets.lang
```

### 2. Define the way to retrieve it from the API response
To retrieve those fields let's use python *requests* library and make request using fields and expansions (https://developer.twitter.com/en/docs/twitter-api/data-dictionary/using-fields-and-expansions) to get extended fields (like 'public_metrics' field) and 'includes' fields:
```
import requests

url = "https://api.twitter.com/2/tweets"
payload = {
  "ids": "1307025659294674945",
  "tweet.fields": "id,author_id,created_at,geo,lang,public_metrics,referenced_tweets,text",
  "expansions":  "referenced_tweets.id"
}
headers = {"Authorization": "some_token"}

r = requests.get(url, params=payload, headers=headers)
```

### 3. Define the way to preprocess this features(filter and combine)
- Since I got a json-structured response with nested tweets I want to retrieve those nested tweets, so I will have each tweet in separate json structure. 
- Next I will drop extra fields from every tweet (ie I don't need 'public_metrics.quote_count' which comes in one scope of 'public_metrics' field; same with 'referenced_tweets.type' field ). 
- One more thing we can make is to divide posts into categories(ie by asset type - bitcoin, ethereum, etc.) - to achieve this parse the 'text' field of json looking for a key-word 'bitcoin' or 'ethereum'.
- Another option is to check the author_id whether this author is trusted/verified
- Also there is possible even deeper analytics to understand whether tweet content is truly relevant for us with the help of ml-model. 
Now I have bunch of relevant tweets with same json-structure and fields.

### 4. Define the way to store it in a most efficient way
Thanks to previous filtration this tweets can be stored in ElasticSearch in different indexes (one for each asset) and with type 'tweet' like this:
```
PUT /bitcoin_tweets_index/tweet/1
{
  "id": "1307025659294674945",
  "conversation_id": "1304102743196356610",
  "public_metrics": {
        "retweet_count": 11,
        "reply_count": 2,
        "like_count": 70
      },
  "text": "Here’s an article that highlights the updates in the new Tweet payload v2 https://t.co/oeF3ZHeKQQ",
  "created_at": "2020-09-18T18:36:15.000Z",
  "author_id": "2244994945",
  "lang": "en",
  "referenced_tweets": [ { "id": "1304102743196356610" }]
}

PUT /bitcoin_tweets_index/tweet/2
{
  "id": "1304102743196356610",
  "conversation_id": "1304102743196356610",
  "public_metrics": {
          "retweet_count": 31,
          "reply_count": 12,
          "like_count": 104
  },
  "text": "The new #TwitterAPI includes some improvements to the Tweet payload. You’re probably wondering — what are the main differences? 🧐\n\nIn this video, @SuhemParack compares the v1.1 Tweet payload with what you’ll find using our v2 endpoints. https://t.co/CjneyMpgCq",
  "created_at": "2020-09-10T17:01:37.000Z",
  "author_id": "2244994945",
  "lang": "en",
  "referenced_tweets": []
}
```

### 5. Define  the way to analyze it in a most efficient way
Since all data has the same structure we could apply custom mapping for an index to define field types - for instance in such way we can explicitly define that field 'text' is text type which is well for full text search or that field 'created_at' is always a date or that field 'lang' is both text and a keyword.- it means, that it can be used for aggregation and exact searches. It will affect positively on store strategy and search speed:
```
PUT /bitcoin_tweets_index // Create index first

PUT /bitcoin_tweets_index/_mappings
{
  "properties": {
    "id": {
      "type": "integer"
    },
    "conversation_id": {
      "type": "integer"
    },
    "public_metrics": {
      "type": "object"
    },
    "text": {
      "type": "text"
    },
    "created_at": {
      "type": "date"
    },
    "author_id": {
      "type": "integer"
    },
    "lang": {
      "type": "text",
      "fields": {
        "keyword": {
          "type": "keyword"
        }
      }
    },
    "referenced_tweets": {
      "type": "object"
    }
  }
}
```
