import glob
import os
import re
from bs4 import BeautifulSoup
from neo4j.v1 import GraphDatabase

driver = GraphDatabase.driver(os.environ["NEO4J_BOLT_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))

paths = glob.glob("/Users/markneedham/projects/twin4j/adoc/*.html")

with driver.session() as session:

    for path in paths[:1]:
        with open(path, "r") as twin4j_file:
            date = path.split("/")[-1]

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
            print("Featured Community Member: ",    [(link.text, link["href"]) for link in link_element])

            for link in [link for link in soup.find_all("a") if "twitter" not in link["href"] and "twitter" not in link.text]:

                params = {"url": link["href"], "date": date}
                result = session.run("""\
                MERGE (twin4j:TWIN4j {date: {date} })
                WITH twin4j
                OPTIONAL MATCH (l:Link) WHERE l.cleanUrl = {url}
                OPTIONAL MATCH (gh:GitHub) WHERE gh.url = {url}
                OPTIONAL MATCH (m:Meetup) WHERE m.link = {url}
                WITH coalesce(gh, m, l) AS link, twin4j
                
                CALL apoc.do.when(link is NOT NULL, 'MERGE (twin4j)-[:LINKED]->(link)', '', {twin4j: twin4j, link: link}) YIELD value
                RETURN value                                
                """, params)

                print(link["href"], link.text, result.peek())
