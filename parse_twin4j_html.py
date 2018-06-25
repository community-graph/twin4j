import glob
import os
import re
from bs4 import BeautifulSoup
from neo4j.v1 import GraphDatabase

bolt_uri = os.environ["NEO4J_BOLT_URI"]
user = os.environ["NEO4J_USER"]
password = os.environ["NEO4J_PASSWORD"]
driver = GraphDatabase.driver(bolt_uri, auth=(user, password))

paths = glob.glob("/Users/markneedham/projects/twin4j/adoc/*.html")

with driver.session() as session:
    for path in paths:
        with open(path, "r") as twin4j_file:
            date = path.split("/")[-1].replace(".html", "")

            soup = BeautifulSoup(twin4j_file.read(), "html.parser")
            featured_element = [tag for tag in soup.findAll("h3") if "Featured Community Member" in tag.text][0]
            match = re.match("Featured Community Members?: (.*)", featured_element.text)

            person = match.groups(1)[0].strip()
            people = [p.strip() for p in person.split(" and ")]

            if len(people) == 1:
                link_element = featured_element.find_all_next("a")[:1]
            else:
                link_element = featured_element.find_all_next("a")[:2]

            print(date)
            print("Featured Community Member: ", [(link.text, link["href"]) for link in link_element])

            session.run("MERGE (twin4j:TWIN4j {date: {date} }) RETURN twin4j", {"date": date})

            print(link_element)
            params = {"people": [{"name": link.text,
                                  "screenName": link["href"].split("/")[-1],
                                  "stackOverflowId": link["href"].split("/")[-2] if "stackoverflow" in link["href"] else -1
                                  }
                                 for link in link_element],
                      "date": date}
            print(params)
            result = session.run("""\
            MATCH (twin4j:TWIN4j {date: {date} })
            WITH twin4j
            UNWIND {people} AS person
            OPTIONAL MATCH (twitter:User:Twitter) WHERE twitter.screen_name = person.screenName
            OPTIONAL MATCH (user:User) where user.id = toInteger(person.stackOverflowId)
            WITH coalesce(twitter, user) AS u, twin4j
            
            CALL apoc.do.when(u is NOT NULL, 'MERGE (twin4j)-[:FEATURED]->(u)', '', {twin4j: twin4j, u: u}) YIELD value
            RETURN value            
            """, params)

            for link in [link for link in soup.find_all("a") if
                         "twitter" not in link["href"] and "twitter" not in link.text]:
                params = {"url": link["href"], "date": date}
                result = session.run("""\
                MATCH (twin4j:TWIN4j {date: {date} })
                WITH twin4j
                OPTIONAL MATCH (l:Link) WHERE l.cleanUrl = {url}
                OPTIONAL MATCH (gh:GitHub) WHERE gh.url = {url}
                OPTIONAL MATCH (m:Meetup) WHERE m.link = {url}
                WITH coalesce(gh, m, l) AS link, twin4j
                
                CALL apoc.do.when(link is NOT NULL, 'MERGE (twin4j)-[:LINKED]->(link)', '', {twin4j: twin4j, link: link}) YIELD value
                RETURN value                                
                """, params)
