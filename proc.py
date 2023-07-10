import concurrent.futures
import pathlib
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

REF_START = "<!-- pusnow reference start -->"
REF_END = "<!-- pusnow reference end -->"

JOURNALS = 1
CONF = 2
BOOK = 3


def format_authors(authors):
    author_text = ""
    if len(authors) == 1:
        author_text = authors[0]
    elif len(authors) == 2:
        author_text = " and ".join(authors)
    elif len(authors) > 2:
        author_text = ", ".join(authors[:-1]) + ", and " + authors[-1]
    return author_text

def parse_cite(tp, xml_txt):
    if not tp:
        return None
    tree = ET.fromstring(xml_txt)
    authors = [author.text for author in tree.iter("author")]
    title = " ".join([title.text for title in tree.iter("title")])
    years = [year.text for year in tree.iter("year")]
    ees = [ee.text for ee in tree.iter("ee")]
    where_text = ""
    if tp == CONF:
        booktitles = [booktitle.text for booktitle in tree.iter("booktitle")]

        where_text = "In " + " ".join(booktitles) + " " + " ".join(years)
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
        where_text = " ".join(publishers) + ", " + " ".join(years)
    return {
        "title": title,
        "authors": authors,
        "years" : years,
        "ees" : ees,
        "where_text":where_text
    }


def fetch_cite(cite):
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


def handle_markdown(fname):
    fname = pathlib.Path(fname)
    if not fname.is_file():
        return
    updateted_text = None

    with open(fname, "r", encoding="utf8") as f:
        original = f.read()

        body = re.sub(
            REF_START + ".*?" + REF_END, "", original, flags=re.DOTALL
        ).strip()

        cites = re.findall(r"\[\^(.+?)\]", body)
        if not cites:
            return
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        futures = [executor.submit(fetch_cite, cite) for cite in cites]
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

            parsed = parse_cite(tp, text)
            author_text = format_authors(parsed["authors"])
            title_text = parsed["title"]

            if title_text.endswith("."):
                title_text = title_text[:-1]
            cite_text = "[^%s]: %s. *%s*. %s." % (
                cite,
                author_text,
                title_text,
                parsed["where_text"],
            )
            if parsed["ees"]:
                ee = parsed["ees"][0]
                cite_text += " [%s](%s)" % (ee, ee)

            to_cites.append(cite_text)

        if not to_cites:
            return

        reference = "\n".join(to_cites)

        updateted_text = body + "\n\n" + REF_START + "\n" + reference + "\n" + REF_END

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
