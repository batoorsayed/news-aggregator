import json

from function_app import enrich_articles

#top_headlines = {
#    "status": "ok",
#    "totalResults": 35,
#    "articles": [
#        {
#            "source": {"id": "the-washington-post", "name": "The Washington Post"},
#            "author": "Hannah Natanson, Meryl Kornfield",
#            "title": "Roughly 140 EPA staffers who signed ‘dissent’ letter are put on leave - The Washington Post",
#            "description": "Trump officials have placed 139 employees who signed a letter of dissent protesting the Environmental Protection Agency’s current direction and policies on leave Thursday.",
#            "url": "https://www.washingtonpost.com/climate-environment/2025/07/03/epa-dissent-letter-employees-leave/",
#            "urlToImage": "https://www.washingtonpost.com/wp-apps/imrs.php?src=https://arc-anglerfish-washpost-prod-washpost.s3.amazonaws.com/public/AO53QIW5ZE6QUOYGWCHY2WU6VU_size-normalized.JPG&w=1440",
#            "publishedAt": "2025-07-03T23:35:10Z",
#            "content": "The Trump administration has placed on leave roughly 140 staffers at the Environmental Protection Agency who signed a letter of dissent protesting the agencys current direction and policies, accordin… [+4649 chars]",
#        },
#        {
#            "source": {"id": "abc-news", "name": "ABC News"},
#            "author": "ABC News - Breaking News, Latest News and Videos",
#            "title": "'Reservoir Dogs' star Michael Madsen dies at 67 - ABC News - Breaking News, Latest News and Videos",
#            "description": None,
#            "url": "https://abcnews.go.com/GMA/Culture/reservoir-dogs-star-michael-madsen-dies-67/story?id\\\\u003d123455997",
#            "urlToImage": None,
#            "publishedAt": "2025-07-03T23:29:36Z",
#            "content": None,
#        },
#        {
#            "source": {"id": "axios", "name": "Axios"},
#            "author": "Barak Ravid",
#            "title": "Trump says he made no progress on Ukraine in his call with Putin - Axios",
#            "description": "The call took place amid a stalemate in Trump's efforts to end the war between Russia and Ukraine.",
#            "url": "https://www.axios.com/2025/07/03/trump-putin-speak-ukraine-iran",
#            "urlToImage": "https://images.axios.com/H34kWb17QLC-UwYgF8cvO0qAQQA=/0x160:6000x3535/1366x768/2025/07/03/1751561049626.jpg",
#            "publishedAt": "2025-07-03T22:44:15Z",
#            "content": "<ul><li>Putin's foreign policy adviser Yuri Ushakov said the issue of U.S. weapons supply to Ukraine didn't come up during the call between Putin and Trump. </li><li>Trump told reporters on Thursday … [+1318 chars]",
#        },
#        {
#            "source": {"id": "the-washington-post", "name": "The Washington Post"},
#            "author": "Angie Orellana Hernandez",
#            "title": "At least 5 dead after ferry sinks on its way to Bali, Indonesia - The Washington Post",
#            "description": "Some 30 people remain missing, Indonesian authorities said. The death toll could rise as search efforts continue.",
#            "url": "https://www.washingtonpost.com/world/2025/07/03/bali-indonesia-ferry-sinks/",
#            "urlToImage": "https://www.washingtonpost.com/wp-apps/imrs.php?src=https://arc-anglerfish-washpost-prod-washpost.s3.amazonaws.com/public/FJ6LNPUOW7N4QI5QZDIXW6TXIY.JPG&w=1440",
#            "publishedAt": "2025-07-03T22:35:24Z",
#            "content": "An Indonesian ferry carrying at least 65 passengers sank in the Bali Strait on Wednesday night, leaving at least five people dead and more than 30 missing, according to local reports and Indonesias N… [+2282 chars]",
#        },
#    ],
#}
#
#headlines = enrich_articles(top_headlines["articles"])
#print(json.dumps(headlines, indent=2))




