import concurrent.futures
import pathlib
import re
import sys
import json
import tomllib
import urllib.request
import xml.etree.ElementTree as ET
import subprocess


def latex(text):
    if isinstance(text, str):
        return text.replace("%", "\\%")
    else:
        return text


class BaseBlock:
    def __init__(self, mode="md", lang="en"):
        self.mode = mode
        self.lang = lang

    def comment_start(self):
        if self.mode == "md":
            return "<!-- pusnow %s start -->" % self.name
        elif self.mode == "latex":
            return "%%%%%% pusnow %s start %%%%%%" % self.name
        else:
            raise NotImplementedError

    def comment_end(self):
        if self.mode == "md":
            return "<!-- pusnow %s end -->" % self.name
        elif self.mode == "latex":
            return "%%%%%% pusnow %s end %%%%%%" % self.name
        else:
            raise NotImplementedError

    def block(self):
        block = ""
        if self.mode == "md":
            block = self.do_markdown()
        elif self.mode == "latex":
            block = self.do_latex()
        else:
            raise NotImplementedError
        return "%s\n%s\n%s" % (
            self.comment_start(),
            block,
            self.comment_end(),
        )

    def find_block(self, text):
        return re.search(
            "%s.*?%s" % (self.comment_start(), self.comment_end()),
            text,
            flags=re.DOTALL,
        )

    def replace_block(self, text):
        block = self.block()
        return re.sub(
            "%s.*?%s" % (self.comment_start(), self.comment_end()),
            lambda x: block,
            text,
            flags=re.DOTALL,
        )


class Awards(BaseBlock):
    name = "award"

    def __init__(self, mode="md", lang="en"):
        super().__init__(mode, lang)
        self.awards = {}
        self.awards_note = {}

    def add(self, title, org, year, month, note):
        if (title, org) not in self.awards:
            self.awards[(title, org)] = []
        self.awards[(title, org)].append((year, month))
        if (title, org) not in self.awards_note:
            self.awards_note[(title, org)] = ""
        if not self.awards_note[(title, org)]:
            self.awards_note[(title, org)] = note

    def do_common(self, func):
        award_list = []
        for awd_key in sorted(
            self.awards, key=lambda x: max(self.awards[x]), reverse=True
        ):
            title, org = awd_key
            mon_year_list = []
            for year, month in sorted(self.awards[awd_key]):
                if self.lang == "en":
                    if self.mode == "md":
                        mon_year_list.append("*%s* %s" % (MONTH_EN[month], year))
                    elif self.mode == "latex":
                        mon_year_list.append("%s %s" % (MONTH_EN[month], year))
                elif self.lang == "ko":
                    mon_year_list.append("%s년 %s월" % (year, month))
            note = self.awards_note[awd_key]
            award_list.append(func(mon_year_list, title, org, note))
        return "\n".join(award_list)

    def do_markdown(self):
        return self.do_common(
            lambda mon_year, title, org, note: "- %s: %s, **%s**"
            % (", ".join(mon_year), title, org)
        )

    def do_latex(self):
        return self.do_common(
            lambda mon_year, title, org, note: "\\resumeSubheading {%s}{%s}{%s}{%s}"
            % (latex(title), latex(org), latex(note), latex(format_and(mon_year)))
        )


def format_and(words):
    if len(words) == 1:
        text = words[0]
    elif len(words) == 2:
        text = " and ".join(words)
    elif len(words) > 2:
        text = ", ".join(words[:-1]) + ", and " + words[-1]
    return text


def format_authors(authors, bold=None):
    authors2 = []
    for author in authors:
        if bold and author in MY_NAME:
            authors2.append(bold % author)
        else:
            authors2.append(author)

    return format_and(authors2)


def add_dot(text):
    if text[-1] == ".":
        return text
    return text + "."


class Publications(BaseBlock):
    name = "publication"

    def __init__(self, mode="md", lang="en"):
        super().__init__(mode, lang)
        self.pubs = []

    def add(self, title, url, slides, authors, where, year, note):
        self.pubs.append((title, url, slides, authors, where, year, note))

    def do_markdown(self):
        pub_texts = []
        for title, url, slides, authors, where, year, note in self.pubs:
            ee = ""

            if url:
                ee = " [[Link]](%s)" % url
            if slides:
                ee += " [[Slides]](%s)" % slides

            pub_text = "- %s%s\n  - %s\n  - *%s* %s" % (
                add_dot(title),
                ee,
                format_authors(authors, "**%s**"),
                add_dot(where),
                year,
            )
            if note:
                pub_text += "\n  - %s" % note
            pub_texts.append(pub_text)

        return "\n".join(pub_texts)

    def do_latex(self):
        pub_texts = []
        for title, url, slides, authors, where, year, note in self.pubs:
            pub_text = "\\resumePub{%s. %s In \\textit{%s} %s.}" % (
                format_authors(authors, "\\textbf{%s}"),
                add_dot(latex(title)),
                add_dot(latex(where)),
                year,
            )
            pub_texts.append(pub_text)

        return "\n".join(pub_texts)


class Activities(BaseBlock):
    name = "activity"

    def __init__(self, mode="md", lang="en"):
        super().__init__(mode, lang)
        self.activity = []

    def add(self, year, title, org, note):
        self.activity.append((year, title, org, note))

    def do_markdown(self):
        activity_texts = []
        for year, title, _, _ in sorted(self.activity, reverse=True):
            if self.lang == "en":
                activity_texts.append("* %s: %s" % (year, title))
            elif self.lang == "ko":
                activity_texts.append("* %s년: %s" % (year, title))
        return "\n".join(activity_texts)

    def do_latex(self):
        activity_texts = []
        for year, title, org, note in sorted(self.activity, reverse=True):
            activity_texts.append(
                "\\resumeSubheading{%s}{%s}{%s}{%s}"
                % (latex(title), latex(org), latex(note), latex(year))
            )
        return "\n".join(activity_texts)


class Talks(BaseBlock):
    name = "talk"

    def __init__(self, mode="md", lang="en"):
        super().__init__(mode, lang)
        self.talks = []

    def add(self, year, title, org, note):
        self.talks.append((year, title, org, note))

    def do_markdown(self):
        talk_text = []
        for year, title, org, _ in sorted(self.talks, reverse=True):
            talk_text.append("* %s %s: %s" % (org, year, title))
        return "\n".join(talk_text)

    def do_latex(self):
        talk_text = []
        for year, title, org, note in sorted(self.talks, reverse=True):
            talk_text.append(
                "\\resumeSubheading{%s}{%s}{%s}{%s}"
                % (latex(title), latex(org), latex(note), latex(year))
            )
        return "\n".join(talk_text)


REF_START = "<!-- pusnow reference start -->"
REF_END = "<!-- pusnow reference end -->"

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


PUBLICATIONS_LIST = None


def list_publication():
    global PUBLICATIONS_LIST
    if PUBLICATIONS_LIST is not None:
        return PUBLICATIONS_LIST

    PUBLICATIONS_LIST = []
    publications = PUSNOW.get("publication", [])
    for pub in publications:
        pub2 = {}
        if "cite" in pub:
            _, pub2 = fetch_and_parse_cite(pub["cite"])

        for key in pub:
            pub2[key] = pub[key]

        PUBLICATIONS_LIST.append(
            {
                "authors": pub2.get("authors", []),
                "ees": pub2.get("ees", []),
                "right": pub2.get("right", "acmlicensed"),
                "pdf": pub2.get("pdf", None),
                "slides": pub2.get("slides", ""),
                "note": pub2.get("note", ""),
                "title": pub2["title"],
                "where": pub2["where"],
                "year": pub2["year"],
                "month": pub2["month"],
                "day": pub2["day"],
            }
        )
    return PUBLICATIONS_LIST


def generate_publication():
    cp = pathlib.Path("content/publication")
    for child in cp.glob("*.md"):
        if child.is_file():
            child.unlink()
    for pub in list_publication():
        pdf = pub["pdf"]
        ees = pub["ees"]
        authors = pub["authors"]
        right = pub["right"]

        if pub["pdf"]:
            copyright_text = ""
            if ees:
                doi_text = f", [{ees[0]}]({ees[0]})"
            else:
                doi_text = ""
            if right == "acmcopyright":
                copyright_text = ACM_COPYRIGHT % (
                    "ACM",
                    pub["year"],
                    pub["where"],
                    doi_text,
                )
            elif right == "acmlicensed":
                copyright_text = ACM_COPYRIGHT % (
                    format_authors(authors, False),
                    pub["year"],
                    pub["where"],
                    doi_text,
                )
            with open("content/publication/%s.md" % pdf, "w", encoding="utf8") as f:
                pdf_code = '{{% pdf "' + f"/publication/{pdf}.pdf" + '" %}}'
                f.write(
                    f"""---
title: "{pub["title"]}"
date: {pub["year"]}-{pub["month"]:02}-{pub["day"]:02}
nogitdate: true
pdf: "/publication/{pdf}.pdf"
tags:
    - Publication
---

{pub["where"]}

{copyright_text}

[Download PDF](/publication/{pdf}.pdf)

{pdf_code}
"""
                )


def handle_cite(text):
    body = re.sub(REF_START + ".*?" + REF_END, "", text, flags=re.DOTALL).strip()

    cites = re.findall(r"\[\^(.+?)\]", body)
    if not cites:
        return text
    cites = sorted(list(set(cites)))
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
        author_text = format_authors(parsed["authors"], "**%s**")
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


def handle_publication(text, mode="md"):
    publications_blk = Publications(mode)
    if not publications_blk.find_block(text):
        return text

    for pub in list_publication():
        if pub["pdf"]:
            url = f"{BASE_URL}publication/{pub["pdf"]}/"
        elif pub["ees"]:
            url = pub["ees"][0]
        else:
            url = ""

        publications_blk.add(
            pub["title"],
            url,
            pub["slides"],
            pub["authors"],
            pub["where"],
            pub["year"],
            pub["note"],
        )

    result = publications_blk.replace_block(text)
    return result


def handle_award(text, lang="en", mode="md"):
    awards_blk = Awards(mode, lang)
    if not awards_blk.find_block(text):
        return text

    awards = PUSNOW.get("award", [])
    for awd in awards:
        if "year" not in awd or "month" not in awd:
            continue

        year = awd["year"]
        month = awd["month"]
        note = awd.get("note", "")

        title = awd.get("title-" + lang, "")
        if not title:
            title = awd.get("title", "")

        org = awd.get("org-" + lang, "")
        if not org:
            org = awd.get("org", "")

        awards_blk.add(title, org, year, month, note)

    result = awards_blk.replace_block(text)
    return result


def handle_activity(text, lang="en", mode="md"):
    activities_blk = Activities(mode, lang)
    if not activities_blk.find_block(text):
        return text
    for activity in PUSNOW.get("activity", []):
        year = activity["year"]

        title = activity.get("title-" + lang, "")
        if not title:
            title = activity.get("title", "")

        note = activity.get("note", "")
        org = activity.get("org", "")
        activities_blk.add(year, title, org, note)

    result = activities_blk.replace_block(text)
    return result

def handle_talk(text, lang="en", mode="md"):
    talks_blk = Talks(mode, lang)
    if not talks_blk.find_block(text):
        return text
    for talk in PUSNOW.get("talk", []):
        year = talk["year"]

        title = talk.get("title-" + lang, "")
        if not title:
            title = talk.get("title", "")

        note = talk.get("note", "")
        org = talk.get("org", "")
        talks_blk.add(year, title, org, note)

    result = talks_blk.replace_block(text)
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
        basename = pathlib.Path(fname.name).name
        if basename in ABOUT_FILES:
            lang = ABOUT_FILES[basename]
            updateted_text = handle_publication(updateted_text)
            updateted_text = handle_award(updateted_text, lang)
            updateted_text = handle_activity(updateted_text, lang)
            updateted_text = handle_talk(updateted_text, lang)

    if updateted_text:
        with open(fname, "w", encoding="utf8") as f:
            f.write(updateted_text)


def handle_latex(fname):
    fname = pathlib.Path(fname)
    if not fname.is_file():
        return

    print("Handling:", fname)
    updateted_text = None
    with open(fname, "r", encoding="utf8") as f:
        original = f.read()
        updateted_text = original
        updateted_text = handle_publication(updateted_text, "latex")
        updateted_text = handle_award(updateted_text, "en", "latex")
        updateted_text = handle_activity(updateted_text, "en", "latex")
        updateted_text = handle_talk(updateted_text, "en", "latex")

    if updateted_text:
        with open(fname, "w", encoding="utf8") as f:
            f.write(updateted_text)

    subprocess.run(["pdflatex", "-output-directory", "latex", fname])
    subprocess.run(
        ["cp", fname.with_suffix(".pdf"), "static/pdf/"],
    )


if len(sys.argv) > 1:
    for fname in sys.argv[1:]:
        handle_markdown(fname)
else:
    generate_publication()
    content = pathlib.Path("content/")
    for fname in content.glob("**/*.md"):
        handle_markdown(fname)

    for fname in pathlib.Path("latex/").glob("**/*.tex"):
        handle_latex(fname)
