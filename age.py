import json
import os
from urllib.parse import urljoin
import requests
import munch
import datetime
from xml.etree import ElementTree

import csv
from urllib.parse import urlparse

from requests.auth import HTTPBasicAuth

hostname = os.environ.get('JENKINS_HOST')
username = os.environ.get('JENKINS_USERNAME')
password = os.environ.get('JENKINS_PASSWORD')

def yesno(b: bool) -> str:
    return "Yes" if b else "No"


# server = Jenkins(os.environ.get('JENKINS_HOST'),
#                  username=os.environ.get('JENKINS_USERNAME'),
#                  password=os.environ.get('JENKINS_PASSWORD'),
#                  lazy=True)


def make_request(url, path=None, tree="jobs[name,url]"):
    if path:
        url = urljoin(os.environ.get('JENKINS_HOST'), path)

    url = urljoin(url, "api/json")
    r = requests.get(url,
                     params={
                         "tree": tree
                     },
                     auth=HTTPBasicAuth(username, password))

    if r.status_code == 200:
        return munch.DefaultMunch.fromDict(r.json())
    else:
        return None


def create_empty_hierarchy():
    return munch.Munch({
        "root": [],
        "folders": {}
    })


def get_job_repo(url):
    url = urljoin(url, "config.xml")
    r = requests.get(url, auth=HTTPBasicAuth(username,password))
    if r.status_code == 200:
        tree = ElementTree.fromstring(r.content)
        try:
            results = None
            root = tree.find('scm')
            if not root:
                root = tree.find('sources')
                if root:
                    results = root.find('data').find('jenkins.branch.BranchSource').find('source').find('remote').text
            else:
                results = root.find('userRemoteConfigs').find('hudson.plugins.git.UserRemoteConfig').find('url').text

            if isinstance(results, list):
                return results[0] if results else None
            elif isinstance(results, str):
                return results
            else:
                return None
        except Exception as e:
            print(f"Failed to get config for job {url}: {str(e)}")
    else:
        return None


def collect_jobs(url, job_hierarchy, flat_list):
    results = make_request(url, tree="jobs[fullName, name,url,jobs[lastSuccessfulBuild[*]]]")
    for job in results.jobs:
        path_parts = os.path.split(job.fullName)
        job_name = path_parts[-1]
        folder_name = path_parts[0] if len(path_parts) > 1 else None

        if "Folder" in job._class:
            job_hierarchy['folders'][job_name] = collect_jobs(job.url, create_empty_hierarchy(), flat_list)
        else:
            if 'jobs' in job and job.jobs and 'lastSuccessfulBuild' in job.jobs[0]:
                last_build_info = job.jobs[0].lastSuccessfulBuild if 'jobs' in job else None
            else:
                last_build_info = None

            build_date = None
            try:
                build_date = datetime.datetime.fromtimestamp(last_build_info.timestamp / 1000).isoformat() if last_build_info else None
            except ValueError as e:
                print(f"Failed to get build date for job {job.url}: {str(e)}")

            new_repo = {
                "folder": folder_name,
                "name": job_name,
                "url": job.url,
                "repo": get_job_repo(job.url),
                "build_date": build_date
            }
            job_hierarchy["root"].append(new_repo)
            flat_list.append(new_repo)

    return job_hierarchy


flat_list_of_repos = []
hierarchy = collect_jobs(os.environ.get('JENKINS_HOST'), create_empty_hierarchy(), flat_list_of_repos)

print(json.dumps(hierarchy, indent=2))

if len(flat_list_of_repos) > 0:

    filename = urlparse(hostname).netloc.replace(".","-")

    with open(f'{filename}-jobs.csv', 'w+') as csvfile:
        fieldnames = list(flat_list_of_repos[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in flat_list_of_repos:
            writer.writerow(r)
else:
    print("No jobs found")
