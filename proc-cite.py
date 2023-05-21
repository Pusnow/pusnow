import re
import sys
import urllib.request
import pathlib
import xml.etree.ElementTree as ET

REF_START = "<!-- pusnow reference start -->"
REF_END = "<!-- pusnow reference end -->"


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
        to_cites = []
        for cite in cites:
            is_journals = cite.startswith("journals/")
            is_conf = cite.startswith("conf/")
            is_book = cite.startswith("books/")
            if is_journals or is_conf or is_book:
                dblp_url = "https://dblp.org/rec/%s.xml" % cite
                resp = urllib.request.urlopen(dblp_url)
                xml_data = resp.read()
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
                if is_conf:
                    booktitles = [
                        booktitle.text for booktitle in tree.iter("booktitle")
                    ]

                    last_text = "In " + " ".join(booktitles) + " " + " ".join(years)
                elif is_journals:
                    journals = [journal.text for journal in tree.iter("journal")]
                    volumes = [volume.text for volume in tree.iter("volume")]
                    numbers = [number.text for number in tree.iter("number")]
                    last_text = " ".join(journals)
                    if volumes:
                        last_text += " " + " ".join(volumes)
                        if numbers:
                            last_text += "(" + " ".join(numbers) + ")"
                elif is_book:
                    publishers = [
                        publisher.text for publisher in tree.iter("publisher")
                    ]
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
