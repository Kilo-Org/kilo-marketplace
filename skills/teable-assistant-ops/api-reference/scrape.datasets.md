# Scrape Tool — Dataset Reference

Fetch structured data from 1,600+ web platforms. Each dataset requires a `datasetId` identifier and an `inputs` array of objects with the required fields.

The tables below are the curated datasets with known inputs. For any other platform (Glassdoor, Indeed, Trustpilot, ...), call `scrape-search` with `query: "<platform> <data type>"`: each match gives a raw `gd_...` id, the inputs it needs to collect URLs, and its `modes` (discover by keyword, profile, category...) with their own inputs. The same search also covers a curated platform when no curated id fits the request (Amazon by UPC, YouTube by search filters, X posts of several profiles at once): pick the mode from `modes` and pass it as `discoverBy`.

A pending result is resumed with `scrape-status` and its snapshotId, never by running `scrape` again.

Plain datasets scrape the pages you pass; `*_by_*` datasets take a keyword, hashtag, profile, category or shop URL and find the records themselves. Each input yields **at most 10 records**; raise `limitPerInput` (max 50) only when the user asks for more, since every record is billed. It caps the records per input for every dataset, and dataset fields such as `num_of_comments` cannot exceed it. One call is capped at inputs × limitPerInput = 1000 records. Credits for inputs × limitPerInput are held while the scrape runs, so when each input is a single page (a profile, product page, single post or video) pass `limitPerInput: 1`; one call can then carry up to 1000 URLs. Split a larger job into several calls.

## Usage

```
datasetId: "<datasetId>"
inputs: [{ "url": "https://..." }, { "url": "https://..." }]   // one object per item; batch same-dataset items in one call
```

### Long-tail dataset in a discover mode (from scrape-search)
```
datasetId: "gd_..."            // id from scrape-search
discoverBy: "keyword"          // one of its modes[].discoverBy
inputs: [{ "keyword": "...", "location": "..." }]   // that mode's inputs
limitPerInput: 20              // optional, only when the user asks for more than 10
```

---

## E-Commerce

| Dataset ID | Inputs (required first) | Notes |
|---|---|---|
| `amazon_product` | `url` | URL must contain `/dp/`. |
| `amazon_product_reviews` | `url` | URL must contain `/dp/`. |
| `amazon_product_search` | `keyword`, `url` (Amazon domain) |  |
| `amazon_seller` | `url` |  |
| `walmart_product` | `url` | URL must contain `/ip/`. |
| `walmart_seller` | `url` |  |
| `walmart_reviews` | `url` | URL must contain `/ip/`. Optional `sort_by`. |
| `ebay_product` | `url` |  |
| `homedepot_products` | `url` |  |
| `zara_products` | `url` |  |
| `etsy_products` | `url` |  |
| `bestbuy_products` | `url` |  |
| `amazon_product_by_category` | `url` | Pass the category URL. Optional `sort_by`, `zipcode`. |
| `amazon_best_sellers` | `category_url` | Pass the best sellers URL. Optional `zipcode`. |
| `walmart_product_by_keyword` | `keyword` | Default `domain`: https://www.walmart.com. |
| `walmart_product_by_category` | `category_url` | Pass the category URL. |
| `ebay_product_by_keyword` | `keywords` |  |
| `ebay_product_by_shop` | `url` | Pass the store URL. |
| `ebay_product_by_category` | `url` | Pass the category URL. |
| `etsy_products_by_keyword` | `keywords` |  |
| `etsy_products_by_shop` | `url` | Pass the shop URL. |
| `bestbuy_products_by_keyword` | `keywords` |  |
| `homedepot_products_by_keyword` | `keyword` |  |
| `homedepot_products_by_category` | `url` | Pass the category URL. Optional `zipcode`, `max_product`. |
| `zara_products_by_category` | `url` | Pass the category URL. |

## LinkedIn

| Dataset ID | Inputs (required first) | Notes |
|---|---|---|
| `linkedin_person_profile` | `url` |  |
| `linkedin_company_profile` | `url` |  |
| `linkedin_job_listings` | `url` |  |
| `linkedin_posts` | `url` | URL must be a pulse or posts URL. |
| `linkedin_people_search` | `url`, `first_name`, `last_name` |  |
| `linkedin_job_listings_by_keyword` | `location` | Optional `keyword`, `country`, `time_range`, `job_type`, `experience_level`, `remote`. |
| `linkedin_posts_by_profile` | `url` | Pass a `/in/` profile URL. Optional `start_date`, `end_date` (YYYY-MM-DD). |
| `linkedin_posts_by_company` | `url` | Pass a `/company/` URL. Optional `start_date`, `end_date` (YYYY-MM-DD). |

## Business Intelligence

| Dataset ID | Inputs (required first) | Notes |
|---|---|---|
| `crunchbase_company` | `url` |  |
| `crunchbase_person` | `url` | Pass a `/person/` URL. |
| `zoominfo_company_profile` | `url` |  |
| `crunchbase_company_by_keyword` | `keyword` |  |

## Instagram

| Dataset ID | Inputs (required first) | Notes |
|---|---|---|
| `instagram_profiles` | `url` |  |
| `instagram_posts` | `url` |  |
| `instagram_reels` | `url` |  |
| `instagram_comments` | `url` |  |
| `instagram_posts_by_profile` | `url` | Pass the profile URL. Optional `start_date`, `end_date` (YYYY-MM-DD), `post_type`. |
| `instagram_reels_by_profile` | `url` | Pass the profile URL. Optional `start_date`, `end_date` (YYYY-MM-DD). |

## Facebook

| Dataset ID | Inputs (required first) | Notes |
|---|---|---|
| `facebook_posts` | `url` |  |
| `facebook_marketplace_listings` | `url` |  |
| `facebook_company_reviews` | `url`, `num_of_reviews` | Default `num_of_reviews`: 10. |
| `facebook_events` | `url` |  |
| `facebook_page_profile` | `url` |  |
| `facebook_page_posts` | `url` | Pass the page or profile URL. Optional `start_date`, `end_date` (YYYY-MM-DD). |
| `facebook_group_posts` | `url` | Pass the `/groups/` URL. Optional `start_date`, `end_date` (YYYY-MM-DD). |
| `facebook_reels` | `url` | Pass the profile URL. Optional `start_date`, `end_date` (YYYY-MM-DD). |
| `facebook_comments` | `url` | Pass the post URL. Optional `comments_sort`. |
| `facebook_marketplace_by_keyword` | `keyword`, `city` | Optional `date_listed`. |

## TikTok

| Dataset ID | Inputs (required first) | Notes |
|---|---|---|
| `tiktok_profiles` | `url` |  |
| `tiktok_posts` | `url` |  |
| `tiktok_shop` | `url` |  |
| `tiktok_comments` | `url` |  |
| `tiktok_posts_by_keyword` | `search_keyword` | Optional `country`. |
| `tiktok_posts_by_profile` | `url` | Pass the profile URL. Optional `start_date`, `end_date` (YYYY-MM-DD), `post_type`, `sort_by`. |
| `tiktok_shop_by_keyword` | `keyword` |  |
| `tiktok_shop_by_category` | `category_url` | Pass the category URL. |
| `tiktok_shop_by_shop` | `url` | Pass the shop URL. |

## X (Twitter)

| Dataset ID | Inputs (required first) | Notes |
|---|---|---|
| `x_posts` | `url` |  |
| `x_profiles` | `url` |  |
| `x_profile_posts` | `url`, `start_date`, `end_date` | Optional `start_date`, `end_date` (YYYY-MM-DD). |

## YouTube

| Dataset ID | Inputs (required first) | Notes |
|---|---|---|
| `youtube_profiles` | `url` |  |
| `youtube_comments` | `url`, `num_of_comments` | Default `num_of_comments`: 10. |
| `youtube_videos` | `url` |  |
| `youtube_videos_by_keyword` | `keyword` | Optional `start_date`, `end_date` (YYYY-MM-DD), `country`. |
| `youtube_videos_by_hashtag` | `hashtag` | Discover YouTube videos tagged with a hashtag (without `#`). Optional `start_date`, `end_date` (YYYY-MM-DD), `country`. |
| `youtube_videos_by_channel` | `url` | Pass the channel or playlist URL. Optional `start_date`, `end_date` (YYYY-MM-DD), `order_by`. |
| `youtube_profiles_by_keyword` | `keyword` |  |

## Reddit

| Dataset ID | Inputs (required first) | Notes |
|---|---|---|
| `reddit_posts` | `url` |  |
| `reddit_comments` | `url`, `days_back` | Optional `days_back` limits by recency. |
| `reddit_posts_by_keyword` | `keyword` | Default `date`: All time (also Past hour/day/week/month/year). Optional `sort_by`. |
| `reddit_posts_by_subreddit` | `url` | Pass the subreddit URL. Optional `sort_by` (new/top/hot), `keyword`, `start_date`. |
| `reddit_posts_by_author` | `url` | Pass the user URL. Optional `sort_by`. |

## Other platforms

| Dataset ID | Inputs (required first) | Notes |
|---|---|---|
| `google_maps_reviews` | `url`, `days_limit` | Default `days_limit`: 3. |
| `google_shopping` | `url` |  |
| `google_play_store` | `url` |  |
| `apple_app_store` | `url` |  |
| `reuter_news` | `url` |  |
| `github_repository_file` | `url` |  |
| `yahoo_finance_business` | `url` |  |
| `yahoo_finance_by_keyword` | `keyword` |  |
| `zillow_properties_listing` | `url` |  |
| `booking_hotel_listings` | `url` |  |

---

## Examples

```
datasetId: "amazon_product"
inputs: [{ "url": "https://www.amazon.com/dp/B0CFLD1MQ1" }]
```

```
datasetId: "tiktok_posts_by_keyword"        // field name is search_keyword for this dataset
inputs: [{ "search_keyword": "home espresso" }]
```

```
datasetId: "linkedin_job_listings_by_keyword"
inputs: [{ "keyword": "data engineer", "location": "Berlin" }]
```
