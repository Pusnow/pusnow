import concurrent.futures
import pathlib
import re
import sys
import tomllib
import urllib.request
import xml.etree.ElementTree as ET

REF_START = "<!-- pusnow reference start -->"
REF_END = "<!-- pusnow reference end -->"
PUB_START = "<!-- pusnow publication start -->"
PUB_END = "<!-- pusnow publication end -->"

MY_NAME = set(["Wonsup Yoon"])

JOURNALS = 1
CONF = 2
BOOK = 3


def add_dot(text):
    if text[-1] == ".":
        return text
    return text + "."


def format_authors(authors):
    author_text = ""

    authors2 = []
    for author in authors:
        if author in MY_NAME:
            authors2.append("**%s**" % author)
        else:
            authors2.append(author)

    if len(authors2) == 1:
        author_text = authors2[0]
    elif len(authors2) == 2:
        author_text = " and ".join(authors2)
    elif len(authors2) > 2:
        author_text = ", ".join(authors2[:-1]) + ", and " + authors2[-1]
    return author_text


def parse_dblp(tp, xml_txt):
    if not tp:
        return None
    tree = ET.fromstring(xml_txt)
    authors = [author.text for author in tree.iter("author")]
    title = " ".join([title.text for title in tree.iter("title")])
    year = "".join([year.text for year in tree.iter("year")][:1])
    ees = [ee.text for ee in tree.iter("ee")]
    where_text = ""
    if tp == CONF:
        booktitles = [booktitle.text for booktitle in tree.iter("booktitle")]

        where_text = "In " + " ".join(booktitles) + " " + year
    elif tp == JOURNALS:
        journals = [journal.text for journal in tree.iter("journal")]
        volumes = [volume.text for volume in tree.iter("volume")]
        numbers = [number.text for number in tree.iter("number")]
        where_text = " ".join(journals)
        if volumes:
            where_text += " " + " ".join(volumes)
            if numbers:
                where_text += "(" + " ".join(numbers) + ")"
    elif tp == BOOK:
        publishers = [publisher.text for publisher in tree.iter("publisher")]
        where_text = " ".join(publishers) + ", " + year

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "ees": ees,
        "where": where_text,
    }


def fetch_dblp(cite):
    if cite.startswith("journals/"):
        tp = JOURNALS
    elif cite.startswith("conf/"):
        tp = CONF
    elif cite.startswith("books/"):
        tp = BOOK
    else:
        tp = None
    if tp:
        url = "https://dblp.org/rec/%s.xml" % cite
        with urllib.request.urlopen(url) as response:
            return (cite, tp, response.read())
    else:
        return (cite, tp, "")


def generate_publication():
    with open("data/publications.toml", "rb") as f:
        data = tomllib.load(f)
        publications = data.get("publication", [])
        pubs = []
        for pub in publications:
            pub2 = {}
            if "dblp" in pub:
                cite, tp, text = fetch_dblp(pub["dblp"])
                if text:
                    pub2 = parse_dblp(tp, text)

            for key in pub:
                pub2[key] = pub[key]

            ees = pub2.get("ees", [])
            slides = pub2.get("slides", "")
            if ees:
                ee = " [[Link]](%s)" % ees[0]
            else:
                ee = ""

            if slides:
                ee += " [[Slides]](%s)" % slides
            authors = pub2.get("authors", [])
            author_text = format_authors(authors)
            note_text = pub2.get("note", "")
            pub_text = "- %s%s\n  - %s\n  - *%s* %s" % (
                add_dot(pub2["title"]),
                ee,
                author_text,
                add_dot(pub2["where"]),
                pub2["year"],
            )
            if note_text:
                pub_text += "\n  - %s" % note_text
            pubs.append(pub_text)
        result = "\n".join(pubs)
        return PUB_START + "\n" + result + "\n" + PUB_END
    return PUB_START + "\n" + PUB_END


def handle_cite(text):
    body = re.sub(REF_START + ".*?" + REF_END, "", text, flags=re.DOTALL).strip()

    cites = re.findall(r"\[\^(.+?)\]", body)
    if not cites:
        return None
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
    futures = [executor.submit(fetch_dblp, cite) for cite in cites]
    to_cites = []
    results = {}
    for future in concurrent.futures.as_completed(futures):
        try:
            cite, tp, text = future.result()
            results[cite] = (tp, text)
        except Exception as e:
            print(f"An error occurred: {e}")
            continue

    for cite in cites:
        tp, text = results.get(cite, (None, None))
        if not tp:
            continue

        parsed = parse_dblp(tp, text)
        author_text = format_authors(parsed["authors"])
        title_text = parsed["title"]

        title_text = add_dot(title_text)
        cite_text = "[^%s]: %s. *%s* %s." % (
            cite,
            author_text,
            title_text,
            parsed["where"],
        )
        if parsed["ees"]:
            ee = parsed["ees"][0]
            cite_text += " [%s](%s)" % (ee, ee)

        to_cites.append(cite_text)

    reference = "\n".join(to_cites)

    updateted_text = body + "\n\n" + REF_START + "\n" + reference + "\n" + REF_END
    return updateted_text


def handle_publication(text):
    if not re.search(PUB_START + ".*?" + PUB_END, text, flags=re.DOTALL):
        return None
    publication_text = generate_publication()
    result = re.sub(
        PUB_START + ".*?" + PUB_END, publication_text, text, flags=re.DOTALL
    )
    return result


def handle_markdown(fname):
    fname = pathlib.Path(fname)
    if not fname.is_file():
        return

    print("Handling:", fname)
    updateted_text = None

    with open(fname, "r", encoding="utf8") as f:
        original = f.read()
        updateted_text = handle_cite(original)
        if updateted_text:
            updateted_text = handle_publication(updateted_text)
        else:
            updateted_text = handle_publication(original)

    if updateted_text:
        with open(fname, "w", encoding="utf8") as f:
            f.write(updateted_text)


if len(sys.argv) > 1:
    for fname in sys.argv[1:]:
        handle_markdown(fname)
else:
    content = pathlib.Path("content/")
    for fname in content.glob("**/*.md"):
        handle_markdown(fname)
