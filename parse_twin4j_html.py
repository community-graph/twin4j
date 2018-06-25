import glob
import re

from bs4 import BeautifulSoup

paths = glob.glob("/Users/markneedham/projects/twin4j/adoc/*.html")

for path in paths:
    with open(path, "r") as twin4j_file:
        soup = BeautifulSoup(twin4j_file.read(), "html.parser")
        featured_element = [tag for tag in soup.findAll("h3") if "Featured Community Member" in tag.text][0]

        match = re.match("Featured Community Members?: (.*)", featured_element.text)

        person = match.groups(1)[0].strip()
        people = [p.strip() for p in person.split(" and ")]

        link = featured_element.findNext("a")["href"]
        print(path, people, link)
