import datetime
import json
import os.path
import re
from urllib.parse import urlparse, urlunsplit

import typer
from bs4 import BeautifulSoup
from firecrawl import FirecrawlApp
from rich import print, box
from rich.progress import Progress, MofNCompleteColumn, BarColumn, TimeElapsedColumn, TaskProgressColumn, \
    TimeRemainingColumn
from rich.table import Table
from typing_extensions import Annotated

# typer main.py run crawl https://tatar-inform.tatar --ip '["news/*"]' -l 900000 -w 1000 -f '["markdown", "rawHtml"]' --it '[".main__news-container"]' --et '[".main__icons", ".page-main__social-share", ".main__info-container", ".page-main__embed-media", ".page-main__tags"]' --ep '["news/tag/*", "news/date/*", "news/2014/*", "news/2015/*", "news/2016/*", "news/2017/*", "news/2018/*", "news/2019/*", "news/2020/*", "news/2021/*", "news/2022/*", "news/2023/*", "news/2024/*", "news/2025/*", "news/rubric/*", "news/author/*"]'
# typer main.py run ls

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})
supported_formats = ["markdown", "html", "rawHtml", "links", "screenshot"]

client_config = {
    'api_key': <SET-ME>,
    'api_url': <SET-ME>,
}

app_config = {
    "reports_dir": "firecrawl-cli-workdir/reports",
    "contents_dir": "firecrawl-cli-workdir/content",
    "visited_pages_dir": "firecrawl-cli-workdir/visited_pages",
}




def _complete_limit(incomplete: str):
    if not incomplete:
        return ["500000"]
    if incomplete.isdigit():
        return [f"{incomplete}0"]
    return []


def _complete_ids(incomplete: str):
    return [
        file_name[:file_name.find(".json")]
        for file_name
        in _report_names()
        if (file_name.startswith(incomplete) if incomplete else True)
    ]


@app.command()
def crawl(
        url: Annotated[
            str,
            typer.Argument(
                help="The base URL to start crawling from. Example: https://www.azatliq.org/",
            )
        ],
        exclude_paths: Annotated[
            str,
            typer.Option(
                "--exclude-paths", "--ep",
                help='JSON-array that specifies URL patterns to exclude from the crawl by comparing website paths against the provided regex patterns. For example, if you set "excludePaths": ["blog/*"] for the base URL firecrawl.dev, any results matching that pattern will be excluded, such as https://www.firecrawl.dev/blog/firecrawl-launch-week-1-recap. Example: \'["/about/*"]\'',
            )
        ] = "[]",
        include_paths: Annotated[
            str,
            typer.Option(
                "--include-paths", "--ip",
                help='JSON-array that specifies URL patterns to include in the crawl by comparing website paths against the provided regex patterns. Only the paths that match the specified patterns will be included in the response. For example, if you set "includePaths": ["blog/*"] for the base URL firecrawl.dev, only results matching that pattern will be included, such as https://www.firecrawl.dev/blog/firecrawl-launch-week-1-recap. Example: \'["/news/*", "/articles"]\'')
        ] = "[]",
        max_depth: Annotated[
            int,
            typer.Option(
                "--max-depth", "-d",
                help="Maximum depth to crawl relative to the entered URL.")
        ] = 2,
        limit: Annotated[
            int,
            typer.Option(
                "--limit", "-l",
                help="Maximum number of pages to crawl.",
                autocompletion=_complete_limit
            )
        ] = 500000,
        formats: Annotated[
            str,
            typer.Option(
                "--formats", "-f",
                help=f"JSON-array with formats to include in the output. Available options: {' '.join(supported_formats)}. Example: '[\"markdown\", \"html\"]\'",
            )
        ] = '["markdown"]',
        include_tags: Annotated[
            str,
            typer.Option(
                "--include-tags", "--it",
                help='JSON-array with tags, class selectors or ids to include in the output. Example: \'[".class-name", "article-tag", "#element-id"]\'')
        ] = '[]',
        exclude_tags: Annotated[
            str,
            typer.Option(
                "--exclude-tags", "--et",
                help='JSON-array with tags, class selectors or ids to exclude from the output. Example: \'[".class-name", "article-tag", "#element-id"]\'')
        ] = '[]',
        wait_for: Annotated[
            int,
            typer.Option(
                "--wait-for", "-w",
                help="Wait x amount of milliseconds for the page to load to fetch content")
        ] = 1000,

):
    """
    Crawl a website.
    Docs: https://docs.firecrawl.dev/api-reference/endpoint/crawl-post
    """
    params = {
        "excludePaths": _parse_json(exclude_paths),
        "includePaths": _parse_json(include_paths),
        "maxDepth": max_depth,
        "ignoreSitemap": True,
        "limit": limit,
        "allowBackwardLinks": False,
        "allowExternalLinks": False,
        "scrapeOptions": {
            "formats": _parse_json(formats),
            "includeTags": _parse_json(include_tags),
            "excludeTags": _parse_json(exclude_tags),
            "waitFor": wait_for,
            # "onlyMainContent": only_main_content,
            # "removeBase64Images": True,
            # "mobile": False,
            "parsePDF": False,
        }
    }
    print(f"About to start crawling of '{url}' with such params:")
    print(_pretty_json(params))
    if typer.confirm("Proceed?", default=True):
        _crawl(url, params)


@app.command()
def cancel(
        _id: Annotated[
            str,
            typer.Argument(
                help="The ID of the crawl job to cancel.",
                autocompletion=_complete_ids,
            )
        ],
):
    """
    Cancel crawling job.
    Docs: https://docs.firecrawl.dev/api-reference/endpoint/crawl-delete
    """
    _, result = _cancel(_id)
    print(_pretty_json({_id: result}))


@app.command()
def status(
        _id: Annotated[
            str,
            typer.Argument(
                help="The ID of the crawl job.",
                autocompletion=_complete_ids,
            )
        ]
):
    """
    Get crawling job status.
    Docs: https://docs.firecrawl.dev/api-reference/endpoint/crawl-get
    """
    _, result = _status(_id)
    print(_pretty_json({_id: result}))


@app.command()
def download(
        _id: Annotated[
            str,
            typer.Argument(
                help="The ID of the crawl job to download",
                autocompletion=_complete_ids,
            )
        ],
):
    """
    Download all crawled data if the job is completed
    """
    _download(_id)


@app.command()
def ls(
        refresh: Annotated[
            bool,
            typer.Option(
                help="Request from the server current status for each incomplete job"
            )
        ] = True,
):
    """
    List all crawling jobs
    """
    _ls(refresh)

@app.command()
def visited_pages(
        url: Annotated[
            str,
            typer.Argument(
                help="The base URL to collect visited pages",
            )
        ],
):
    """
    Collect visited pages of url
    """
    _collect_visited_pages(url)


def _crawl(url, params):
    url = normalize_url(url)

    _visited_pages_file = os.path.join(app_config["visited_pages_dir"], url.replace("/", "#"))
    _visited_pages = []
    if os.path.exists(_visited_pages_file):
        with open(_visited_pages_file, "r") as f:
            _visited_pages = json.load(f)

    orig_excluded_path = params['excludePaths'].copy()
    params['excludePaths'] += _visited_pages[:122_000]

    print("Sending request to server")
    result = _create_client().async_crawl_url(
        url,
        params=params
    )

    # do not save full exclude path because it can be very large
    params['excludePaths'] = orig_excluded_path
    if not result.get("success"):
        print(f"Could not start crawling by url {url}")
        raise typer.Abort()

    result['params'] = params
    result['crawl_url'] = url
    _upsert_report(result['id'], result)


def _cancel(_id: str):
    result = _create_client().cancel_crawl(_id)
    report = _upsert_report(_id, result)
    return report, result


def _status(_id):
    result = _check_crawl_status(_id)
    report = _upsert_report(_id, result)
    return report, result


def _ls(refresh: bool):
    reports_dir = app_config["reports_dir"]
    os.makedirs(reports_dir, exist_ok=True)
    files = _report_names()
    if not files:
        print("No reports found")
        return

    table = Table(box=box.ASCII_DOUBLE_HEAD)
    table.add_column("id", justify="center")
    table.add_column("status", justify="center")
    table.add_column("url", justify="center")
    table.add_column("total/completed", justify="center")
    table.add_column("created_at", justify="center")
    table.add_column("updated_at", justify="center")
    reports = []
    for f in files:
        with open(os.path.join(reports_dir, f), "r") as report_file:
            report = json.load(report_file)
        if refresh and report['status'] not in ["cancelled", "completed"]:
            report, _ = _status(report['id'])
        reports.append(report)

    for report in sorted(reports, key=lambda x: x['created_at'], reverse=True):
        table.add_row(
            report['id'],
            report['status'],
            report['crawl_url'],
            f"{report.get('total', "N/A")}/{report.get('completed', "N/A")}",
            report['created_at'],
            report['updated_at']
        )
    print(table)

def _collect_visited_pages(url):
    url = normalize_url(url)

    def __read_json(__path):
        with open(__path, "r") as _f:
            return json.load(_f)

    def __report_match(__path, __url):
        __report = __read_json(__path)
        return __report.get('crawl_url') == __url and __report.get("status") == 'completed'

    # get a list with crawl job id's for the required url
    crawl_job_ids = [
        f[:f.find(".json")]
        for
        f in
        _report_names()
        if __report_match(os.path.join(app_config["reports_dir"], f), url)
    ]

    v_pages = set()
    url_len = len(url) + 1 # +1 to take slash '/' after the netloc
    for cjid in crawl_job_ids:
        content_dir = os.path.join(app_config['contents_dir'], cjid)
        visited_by_job_pages = set(
            __read_json(os.path.join(content_dir, f)).get('url')[url_len:].lstrip()
            for f
            in os.listdir(content_dir)
            if f.endswith(".json")
        )
        v_pages.update(visited_by_job_pages)

    os.makedirs(app_config['visited_pages_dir'], exist_ok=True)
    file_name = os.path.join(app_config['visited_pages_dir'], url.replace("/", "#"))
    with open(file_name, "w") as f:
        json.dump(list(v_pages), f, indent=4, ensure_ascii=False)
    print(f"Found {len(v_pages)} crawled pages by url '{url}'")


def _check_crawl_status(_id: str):
    """
    Check the status of a crawl job using the Firecrawl API.

    Args:
        _id (str): The ID of the crawl job.

    Returns:
        Any: The status of the crawl job.

    Raises:
        Exception: If the status check request fails.
    """
    endpoint = f'/v1/crawl/{_id}'
    client = _create_client()
    headers = client._prepare_headers()
    response = client._get_request(f'{client.api_url}{endpoint}', headers)
    if response.status_code == 200:
        status_data = response.json()

        return {
            'success': True,
            'status': status_data.get('status'),
            'total': status_data.get('total'),
            'completed': status_data.get('completed'),
            'creditsUsed': status_data.get('creditsUsed'),
            'expiresAt': status_data.get('expiresAt'),
            'data': status_data.get('data', None),
            'error': status_data.get('error'),
            'next': status_data.get('next', None)
        }
    else:
        client._handle_error(response, 'check crawl status')


def _create_client():
    return FirecrawlApp(**client_config)


def _upsert_report(_id, item: dict):
    os.makedirs(app_config["reports_dir"], exist_ok=True)
    report_path = os.path.join(app_config['reports_dir'], f"{_id}.json")
    if os.path.exists(report_path):
        with open(report_path, "r") as _in:
            report = json.load(_in)
    else:
        report = {
            "id": _id,
            "created_at": datetime.datetime.now().replace(microsecond=0).isoformat(),
            "status": "scraping",
        }

    report.update(item)
    report['updated_at'] = datetime.datetime.now().replace(microsecond=0).isoformat()
    report.pop('data', None)
    with open(report_path, "w") as out:
        out.write(_pretty_json(report))
    return report


def _pretty_json(item):
    return json.dumps(item, ensure_ascii=False, indent=4)


def _parse_json(_str):
    try:
        return json.loads(_str)
    except Exception as e:
        print(f"Error during parsing argument: '{_str}'. Expected valid json string. Error: [red]{e}[/red]")
        raise typer.Abort()


def _report_names():
    return os.listdir(app_config["reports_dir"])


def _download(_id):
    report, result = _status(_id)
    if result['status'] != 'completed':
        print(f"The job '{_id}' is not completed. Current status is '{result['status']}'")
        return

    downloaded_files = report.get('downloaded_files', 0)
    next_url = f"{client_config['api_url']}/v1/crawl/{_id}?skip={downloaded_files}"
    client = _create_client()
    headers = client._prepare_headers()

    with Progress(
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
    ) as progress:
        task_id = progress.add_task("Downloading...", total=report['completed'],
                                    completed=report.get('downloaded_files', 0))
        while next_url:
            print(f"Requesting '{next_url}'")
            status_response = client._get_request(next_url, headers)
            if status_response.status_code != 200:
                print(f"Failed to fetch next page: {status_response.status_code}")
                raise typer.Abort()
            result = status_response.json()
            report = _extract_data(result.get('data', []), report)
            progress.update(task_id, completed=report['downloaded_files'])
            if next_url := result.get('next'):
                next_url = next_url.replace("https://", "http://", 1)


def _extract_data(data, report):
    counter = 0
    contents_dir = os.path.join(app_config["contents_dir"], report['id'])
    os.makedirs(contents_dir, exist_ok=True)

    for d in data:
        counter += 1
        if not d:
            continue

        m = d['metadata']
        metadata = {
            "url": (m.get('sourceURL') or m['ogUrl']).strip(),
            "source": "tatarinform",
            "source_type": "mass_media",
        }

        file_name = metadata['url'][len(report['crawl_url']):].strip("/").replace("/", "::")
        if html := d.get('rawHtml'):
            bs = BeautifulSoup(html, "html.parser")

            topic = bs.find("a", class_="main__rubric")
            metadata["topics"] = topic.text.strip() if topic else None

            date = bs.find("a", class_="main__date")
            metadata['created_date'] = date.text.strip() if date else None

            title = bs.find("h1", class_="main__news-title")
            metadata['title'] = title.text.strip() if title else (m.get('title') or m.get('ogTitle')) or None

            article_summary = bs.find("p", class_="main__news-lead")
            metadata['article_summary'] = article_summary.text.strip() if article_summary else (m.get(
                'description') or m.get('ogDescription')) or None

            tags = bs.find("div", class_="page-main__tags")
            metadata['tags'] = [t.text.strip() for t in tags.findAll("a", class_="page-main__option") if
                                t] if tags else None

        if md := d['markdown']:
            metadata['article_text'] = md
            with open(os.path.join(contents_dir, f"{file_name}.md"), "w") as f:
                f.write(md)
            with open(os.path.join(contents_dir, f"{file_name}.json"), "w") as f:
                f.write(_pretty_json(metadata))
            if html:
                with open(os.path.join(contents_dir, f"{file_name}.html"), "w") as f:
                    f.write(html)
        else:
            print("No markdown on a page:", metadata["url"])

    return _upsert_report(report['id'], {'downloaded_files': (counter + report.get('downloaded_files', 0))})


def _escape(text):
    return f"\"{text}\"" if ": " in text else text

def normalize_url(url):
    """
    Normalize here means drop everything but scheme and netloc
    """
    parse_url = urlparse(url)
    return urlunsplit([parse_url.scheme, parse_url.netloc, "", "", ""])


if __name__ == "__main__":
    app()
