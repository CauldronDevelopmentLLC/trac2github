# trac2github
A Python script to convert Trac tickets to GitHub issues with a few limitations.

# Limitations
 * Works with new GitHub preview API (codenamed golden-comet-preview)
 * Only works with sqlite Trac DBs.
 * Does not handle milestones.
 * Limits the maximum text size to 10,000 bytes after conversion to markdown.

# Usage
```
Usage: trac2github.py [options]

Options:
  -h, --help            show this help message and exit
  -u USER, --user=USER  GitHub user name
  -o ORG, --org=ORG     GitHub organization
  -r REPO, --repo=REPO  GitHub repo
  -t TOKEN, --token=TOKEN
                        GitHub access token
  -a ASSIGNEE, --assignee=ASSIGNEE
                        Override assignee
  -c, --create          Create the GitHub repo
  -d, --delete          Delete the GitHub repo
  -p, --public          New GitHub repo is public
  --add-labels          Add missing GitHub labels
  --replace-labels      Replace all GitHub labels
  -i, --preserve-ids    Replace all GitHub labels
  --db=TRAC_DB          Trac sqlite DB
  --components=COMPONENTS
                        Restrict to a specific Trac components. Comma
                        separated list.
  -l NUMBER, --limit=NUMBER
                        Limit the number of tickets
  --offset=NUMBER       Start at ticket offset
  -m FILE, --user-map=FILE
                        File containing a map of Trac users to GitHub users in
                        JSON format
  -n NOTE, --note=NOTE  Add this note to all tickets.
```

# Authentication
You can authenticate with either a GitHub user and password (```--user``` and password prompt) or by creating an personal authentication token (```--token``` option).

# Example
```
./trac2github.py -t <token> -o <org> -r <project> --user-map user_map.json --replace-labels --preserve-ids --assignee <user> --delete --create
```

The above will:

 * Delete the repo ```<org>/<project>```, with out confirmation.
 * Recreate the repo ```<org>/<project>```.
 * Delete the set of default labels.
 * Add ```ticket_type``` and ```resolution``` enums from the Trac DB as new labels.
 * Force ```<user>``` as the assignee for all issues.
 * Read ```user_map.json``` and use it to translate Trac user names to GitHub user names.
 * Attempt to preserve Trac IDs by injecting placeholder issues in any numbering gaps.
 * Attempt to convert Trac Wiki text to GitHub flavored Markdown.
 * Copy all issues and their comments from Trac to GitHub.

Note that the process will abort if any tickets fail and ```--preserve-ids``` is enabled.  This is because failed tickets will mess up the order.
