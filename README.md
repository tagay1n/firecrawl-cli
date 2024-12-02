# CLI for interaction with self-host Firecrawl

## Self-host Firecrawl 
We use [Firecrawl-simple](https://github.com/devflowinc/firecrawl-simple) as a self-host Firecrawl service

## Autocomplete installation
In the root of the repository run
```console
typer --install-completion
source ~/.bash_completions/typer.sh
```

## CLI

**Usage**:

```console
$ [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `crawl`: Crawl a website.
* `cancel`: Cancel crawling job.
* `status`: Get crawling job status.
* `download`: Download all crawled data if the job is...
* `ls`: List all crawling jobs

## `crawl`

Crawl a website.
Docs: https://docs.firecrawl.dev/api-reference/endpoint/crawl-post

**Usage**:

```console
$ crawl [OPTIONS] URL
```

**Arguments**:

* `URL`: The base URL to start crawling from. Example: https://www.azatliq.org/  [required]

**Options**:

* `--exclude-paths, --ep TEXT`: JSON-array that specifies URL patterns to exclude from the crawl by comparing website paths against the provided regex patterns. For example, if you set &quot;excludePaths&quot;: [&quot;blog/*&quot;] for the base URL firecrawl.dev, any results matching that pattern will be excluded, such as https://www.firecrawl.dev/blog/firecrawl-launch-week-1-recap. Example: &#x27;[&quot;/about/*&quot;]&#x27;  [default: []]
* `--include-paths, --ip TEXT`: JSON-array that specifies URL patterns to include in the crawl by comparing website paths against the provided regex patterns. Only the paths that match the specified patterns will be included in the response. For example, if you set &quot;includePaths&quot;: [&quot;blog/*&quot;] for the base URL firecrawl.dev, only results matching that pattern will be included, such as https://www.firecrawl.dev/blog/firecrawl-launch-week-1-recap. Example: &#x27;[&quot;/news/*&quot;, &quot;/articles&quot;]&#x27;  [default: []]
* `-d, --max-depth INTEGER`: Maximum depth to crawl relative to the entered URL.  [default: 2]
* `-l, --limit INTEGER`: Maximum number of pages to crawl.  [default: 500000]
* `-f, --formats TEXT`: JSON-array with formats to include in the output. Available options: markdown html rawHtml links screenshot. Example: &#x27;[&quot;markdown&quot;, &quot;html&quot;]&#x27;  [default: [&quot;markdown&quot;]]
* `--include-tags, --it TEXT`: JSON-array with tags, class selectors or ids to include in the output. Example: &#x27;[&quot;.class-name&quot;, &quot;article-tag&quot;, &quot;#element-id&quot;]&#x27;  [default: []]
* `--exclude-tags, --et TEXT`: JSON-array with tags, class selectors or ids to exclude from the output. Example: &#x27;[&quot;.class-name&quot;, &quot;article-tag&quot;, &quot;#element-id&quot;]&#x27;  [default: []]
* `-w, --wait-for INTEGER`: Wait x amount of milliseconds for the page to load to fetch content  [default: 1000]
* `--help`: Show this message and exit.

## `cancel`

Cancel crawling job.
Docs: https://docs.firecrawl.dev/api-reference/endpoint/crawl-delete

**Usage**:

```console
$ cancel [OPTIONS] _ID
```

**Arguments**:

* `_ID`: The ID of the crawl job to cancel.  [required]

**Options**:

* `--help`: Show this message and exit.

## `status`

Get crawling job status.
Docs: https://docs.firecrawl.dev/api-reference/endpoint/crawl-get

**Usage**:

```console
$ status [OPTIONS] _ID
```

**Arguments**:

* `_ID`: The ID of the crawl job.  [required]

**Options**:

* `--help`: Show this message and exit.

## `download`

Download all crawled data if the job is completed

**Usage**:

```console
$ download [OPTIONS] _ID
```

**Arguments**:

* `_ID`: The ID of the crawl job to download  [required]

**Options**:

* `--help`: Show this message and exit.

## `ls`

List all crawling jobs

**Usage**:

```console
$ ls [OPTIONS]
```

**Options**:

* `--refresh / --no-refresh`: Request from the server current status for each incomplete job  [default: refresh]
* `--help`: Show this message and exit.
