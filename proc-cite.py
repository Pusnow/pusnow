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
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
    with open(fname, "r", encoding="utf8") as f:
        original = f.read()

        body = re.sub(
            REF_START + ".*?" + REF_END, "", original, flags=re.DOTALL
        ).strip()

        cites = re.findall(r"\[\^(.+?)\]", body)
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
            xml_data = text
            tree = ET.fromstring(xml_data)
            authors = [author.text for author in tree.iter("author")]
            titles = [title.text for title in tree.iter("title")]
            years = [year.text for year in tree.iter("year")]
            author_text = ""
            if len(authors) == 1:
                author_text = authors[0]
            elif len(authors) == 2:
                author_text = " and ".join(authors)
            elif len(authors) > 2:
                author_text = ", ".join(authors[:-1]) + ", and " + authors[-1]

            title_text = " ".join(titles)

            last_text = ""
            if tp == CONF:
                booktitles = [booktitle.text for booktitle in tree.iter("booktitle")]

                last_text = "In " + " ".join(booktitles) + " " + " ".join(years)
            elif tp == JOURNALS:
                journals = [journal.text for journal in tree.iter("journal")]
                volumes = [volume.text for volume in tree.iter("volume")]
                numbers = [number.text for number in tree.iter("number")]
                last_text = " ".join(journals)
                if volumes:
                    last_text += " " + " ".join(volumes)
                    if numbers:
                        last_text += "(" + " ".join(numbers) + ")"
            elif tp == BOOK:
                publishers = [publisher.text for publisher in tree.iter("publisher")]
                last_text = " ".join(publishers) + ", " + " ".join(years)

            if title_text.endswith("."):
                title_text = title_text[:-1]
            cite_text = "[^%s]: %s. *%s*. %s" % (
                cite,
                author_text,
                title_text,
                last_text,
            )
            to_cites.append(cite_text)

        reference = "\n".join(to_cites)

        updateted_text = body + "\n\n" + REF_START + "\n" + reference + "\n" + REF_END

    if updateted_text:
        with open(fname, "w", encoding="utf8") as f:
            f.write(updateted_text)


for fname in sys.argv[1:]:
    handle_markdown(fname)
