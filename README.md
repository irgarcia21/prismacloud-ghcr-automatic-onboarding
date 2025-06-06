# GitHub Container Registry Vulnerability Scanning

This Python application lists the GitHub Container Registries (GHCR) for a specified GitHub organization. It utilizes the GitHub API to fetch registry details and supports limiting the number of registries returned. It also onboard these registries to Prisma Cloud for periodic vulnerability scans.  

## Features

- Fetch GHCR details for a specific GitHub organization.
- Limit the number of registries returned.
- Onboard GHCR registries to Prisma Cloud
- Debug logging for troubleshooting and development purposes.

## Prerequisites

Before running this application, ensure you have the following:

- Python 3.9 or higher installed.
- A GitHub Personal Access Token with permissions to access the organization's packages.
- Prisma Cloud Access Key and Secret Key for vulnerability scanning integration.

## Setup
1. Generate a GitHub Personal Access Token:  
Ensure the token has read:packages permission to interact with GitHub Package Registry.

2. Create Prisma Cloud Access Keys:  
Obtain your access key and secret from your Prisma Cloud console to enable API interactions.

3. Fork and Configure the Repository:  
Fork this repository and configure the necessary secrets for automation:
    ```bash
    MY_GITHUB_PAT #Your GitHub Personal Access Token.
    PRISMA_API_URL #Your Prisma Cloud API URL.
    PRISMA_ACCESS_KEY #Your Prisma Cloud Access Key.
    PRISMA_SECRET_KEY #Your Prisma Cloud Secret Key.
    ```

## Usage

Run the script from the command line, providing the necessary arguments:

```bash
python main.py -o <OrganizationName> -t <GHCRTokenName> -l <Limit> --debug
```

