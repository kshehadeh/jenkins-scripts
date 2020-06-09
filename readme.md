# Jenkins Scripts

Utilities for querying jenkins for helpful information.  This was created for a very specific need but one that will likely require repeated usage.  

## Usage

Environment variables are how the utility is configured.  In order to function properly, the following is needed to exist in the environment

1. JENKINS_HOSTNAME (the full url to the root of the jenkins instance)
2. JENKINS_USERNAME (a login username that has access to all relevant jobs)
3. JENKINS_PASSWORD (a login password for the given username)

### `age.py`

age.py will look at every job in the instance and provide the following information:

* Folder name (if any)
* Jenkins name
* Jenkins URL
* Associated Repo (if any)
* Date of last successful build (if any)

The data will be written to a CSV file named after the jenkins instance **and** will be output as JSON to stdout.  The JSON output has a hierarchy to it and the CSV is a flat list.

This script is meant to be used to identify the jobs that may not be needed anymore.  At the time this was written the measure of whether a build is needed is based entirely on the last successful build.  When this was created, the assumption was that a job that was either never built or built successfully so long ago that it is unlikely that the job is in use any more.  But the script makes no assumptions - rather it just outputs the relevant information.

   

