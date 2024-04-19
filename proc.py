import concurrent.futures
import pathlib
import re
import sys
import json
import tomllib
import urllib.request
import xml.etree.ElementTree as ET
import subprocess

REF_START = "<!-- pusnow reference start -->"
REF_END = "<!-- pusnow reference end -->"
PUB_START = "<!-- pusnow publication start -->"
PUB_END = "<!-- pusnow publication end -->"
AWD_START = "<!-- pusnow award start -->"
AWD_END = "<!-- pusnow award end -->"
ACTIVITY_START = "<!-- pusnow activity start -->"
ACTIVITY_END = "<!-- pusnow activity end -->"

MY_NAME = set(["Wonsup Yoon"])

JOURNALS = 1
CONF = 2
BOOK = 3

ACM_COPYRIGHT = "© %s %s. This is the author's version of the work. It is posted here for your personal use. Not for redistribution. The definitive Version of Record was published in %s%s."

CONFIG = {}
BASE_URL = ""

ABOUT_FILES = {
    "_index.md": "en",
    "about-ko.md": "ko",
}

MONTH_EN = {
    1: "Jan.",
    2: "Feb.",
    3: "Mar.",
    4: "Apr.",
    5: "May",
    6: "Jun.",
    7: "Jul.",
    8: "Aug.",
    9: "Sep.",
    10: "Oct.",
    11: "Nov.",
    12: "Dec.",
}


with open("config.toml", "rb") as f:
    CONFIG = tomllib.load(f)
    BASE_URL = CONFIG["baseURL"]

with open("data/pusnow.toml", "rb") as f:
    PUSNOW = tomllib.load(f)


def add_dot(text):
    if text[-1] == ".":
        return text
    return text + "."


def format_authors(authors, bold=True):
    author_text = ""

    authors2 = []
    for author in authors:
        if bold and author in MY_NAME:
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


def parse_dblp(cite, xml_txt):
    if cite.startswith("journals/"):
        tp = JOURNALS
    elif cite.startswith("conf/"):
        tp = CONF
    elif cite.startswith("books/"):
        tp = BOOK
    else:
        tp = None

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
    if (
        cite.startswith("journals/")
        or cite.startswith("conf/")
        or cite.startswith("books/")
    ):
        url = "https://dblp.org/rec/%s.xml" % cite
        with urllib.request.urlopen(url) as response:
            return (cite, response.read())
    else:
        return (cite, "")


def parse_acm(cite, json_txt):
    if not json_txt:
        return None
    data = json.loads(json_txt)
    if data.get("status", "") != "ok":
        return None
    msg = data["message"]
    authors = [
        "%s %s" % (author["given"], author["family"]) for author in msg["author"]
    ]
    title = " ".join([_title for _title in msg["title"]])
    subtitle = " ".join([_subtitle for _subtitle in msg["subtitle"]])
    if subtitle:
        title += ": " + subtitle

    year = sum(msg["published"]["date-parts"][0][0:1])
    month = sum(msg["published"]["date-parts"][0][1:2])
    day = sum(msg["published"]["date-parts"][0][2:3])

    ees = [link["URL"] for link in msg["link"]]

    where_text = " ".join([_title for _title in msg["container-title"]])
    volume = msg.get("volume", "")
    issue = msg.get("issue", "")
    if volume:
        where_text += " " + str(volume)
        if issue:
            where_text += ", " + str(issue)

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "month": month,
        "day": day,
        "ees": ees,
        "where": where_text,
    }


def fetch_acm(cite):
    if not cite.startswith("10.1145/"):
        return (cite, "")
    url = "https://api.crossref.org/works/%s" % cite
    print("handling:", url)
    with urllib.request.urlopen(url) as response:
        return (cite, response.read())
    return (cite, "")


def fetch_and_parse_cite(cite):
    cite, text = fetch_acm(cite)
    if text:
        return (cite, parse_acm(cite, text))
    cite, text = fetch_dblp(cite)
    if text:
        return (cite, parse_dblp(cite, text))
    return (cite, {})


def generate_publication():
    cp = pathlib.Path("content/publication")
    for child in cp.glob("*.md"):
        if child.is_file():
            child.unlink()
    publications = PUSNOW.get("publication", [])
    pubs = []
    for pub in publications:
        pub2 = {}
        if "cite" in pub:
            _, pub2 = fetch_and_parse_cite(pub["cite"])

        for key in pub:
            pub2[key] = pub[key]

        authors = pub2.get("authors", [])
        ees = pub2.get("ees", [])
        right = pub2.get("right", "acmlicensed")
        pdf = pub2.get("pdf", None)
        if pdf:
            copyright_text = ""
            if ees:
                doi_text = f", [{ees[0]}]({ees[0]})"
            else:
                doi_text = ""
            if right == "acmcopyright":
                copyright_text = ACM_COPYRIGHT % (
                    "ACM",
                    pub2["year"],
                    pub2["where"],
                    doi_text,
                )
            elif right == "acmlicensed":
                copyright_text = ACM_COPYRIGHT % (
                    format_authors(authors, False),
                    pub2["year"],
                    pub2["where"],
                    doi_text,
                )
            with open("content/publication/%s.md" % pdf, "w", encoding="utf8") as f:
                pdf_code = '{{% pdf "' + f"/publication/{pdf}.pdf" + '" %}}'
                f.write(
                    f"""---
title: "{pub2["title"]}"
date: {pub2["year"]}-{pub2["month"]:02}-{pub2["day"]:02}
nogitdate: true
pdf: "/publication/{pdf}.pdf"
tags:
    - Publication
---

{pub2["where"]}

{copyright_text}

[Download PDF](/publication/{pdf}.pdf)

{pdf_code}
"""
                )

        slides = pub2.get("slides", "")
        if pdf:
            ee = f" [[Link]]({BASE_URL}publication/{pdf}/)"
        elif ees:
            ee = " [[Link]](%s)" % ees[0]
        else:
            ee = ""

        if slides:
            ee += " [[Slides]](%s)" % slides
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


def handle_cite(text):
    body = re.sub(REF_START + ".*?" + REF_END, "", text, flags=re.DOTALL).strip()

    cites = re.findall(r"\[\^(.+?)\]", body)
    if not cites:
        return text
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
    futures = [executor.submit(fetch_and_parse_cite, cite) for cite in cites]
    to_cites = []
    results = {}
    for future in concurrent.futures.as_completed(futures):
        cite, parsed = future.result()
        results[cite] = parsed

    for cite in cites:
        parsed = results.get(cite, {})
        if not parsed:
            continue
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

    if to_cites:
        reference = "\n".join(to_cites)

        updateted_text = body + "\n\n" + REF_START + "\n" + reference + "\n" + REF_END
        return updateted_text
    else:
        return text


def handle_publication(text):
    if not re.search(PUB_START + ".*?" + PUB_END, text, flags=re.DOTALL):
        return text
    publication_text = generate_publication()
    result = re.sub(
        PUB_START + ".*?" + PUB_END, publication_text, text, flags=re.DOTALL
    )
    return result


def handle_award(text, lang="en"):
    if not re.search(AWD_START + ".*?" + AWD_END, text, flags=re.DOTALL):
        return text

    award_dict = {}

    awards = PUSNOW.get("award", [])
    for awd in awards:
        if "year" not in awd or "month" not in awd:
            continue

        year = awd["year"]
        month = awd["month"]

        title = awd.get("title-" + lang, "")
        if not title:
            title = awd.get("title", "")

        org = awd.get("org-" + lang, "")
        if not org:
            org = awd.get("org", "")
        if (title, org) not in award_dict:
            award_dict[(title, org)] = []
        award_dict[(title, org)].append((year, month))

    award_list = [AWD_START]
    for awd_key in sorted(award_dict, key=lambda x: max(award_dict[x]), reverse=True):
        title, org = awd_key
        mon_year_list = []
        for year, month in sorted(award_dict[awd_key]):
            if lang == "en":
                mon_year_list.append("*%s* %s" % (MONTH_EN[month], year))
            elif lang == "ko":
                mon_year_list.append("%s년 %s월" % (year, month))
        mon_year = ", ".join(mon_year_list)
        award_list.append("- %s: %s, **%s**" % (mon_year, title, org))

    award_list.append(AWD_END)
    result = re.sub(
        AWD_START + ".*?" + AWD_END, "\n".join(award_list), text, flags=re.DOTALL
    )
    return result


def handle_activity(text, lang="en"):
    if not re.search(ACTIVITY_START + ".*?" + ACTIVITY_END, text, flags=re.DOTALL):
        return text

    activity_dict = {}

    activities = sorted(
        filter(lambda x: "year" in x, PUSNOW.get("activity", [])),
        key=lambda x: x["year"],
        reverse=True,
    )
    activity_list = [ACTIVITY_START]
    for activity in activities:
        year = activity["year"]

        title = activity.get("title-" + lang, "")
        if not title:
            title = activity.get("title", "")
        if lang == "en":
            activity_list.append("* %s: %s" % (year, title))
        elif lang == "ko":
            activity_list.append("* %s년: %s" % (year, title))

    activity_list.append(ACTIVITY_END)
    result = re.sub(
        ACTIVITY_START + ".*?" + ACTIVITY_END,
        "\n".join(activity_list),
        text,
        flags=re.DOTALL,
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
        updateted_text = original
        updateted_text = handle_cite(updateted_text)
        updateted_text = handle_publication(updateted_text)
        basename = pathlib.Path(fname.name).name
        if basename in ABOUT_FILES:
            lang = ABOUT_FILES[basename]
            updateted_text = handle_award(updateted_text, lang)
            updateted_text = handle_activity(updateted_text, lang)

    if updateted_text:
        with open(fname, "w", encoding="utf8") as f:
            f.write(updateted_text)


def handle_latex(fname):
    fname = pathlib.Path(fname)
    if not fname.is_file():
        return

    print("Handling:", fname)

    subprocess.run(["pdflatex", "-output-directory", "latex", fname])
    subprocess.run(
        ["cp", fname.with_suffix(".pdf"), "static/pdf/"],
    )


if len(sys.argv) > 1:
    for fname in sys.argv[1:]:
        handle_markdown(fname)
else:
    content = pathlib.Path("content/")
    for fname in content.glob("**/*.md"):
        handle_markdown(fname)

    latex = pathlib.Path("latex/")
    for fname in latex.glob("**/*.tex"):
        handle_latex(fname)
