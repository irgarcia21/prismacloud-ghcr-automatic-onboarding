__author__ = "Simon Melotte"

import os
import json
import requests
import argparse
import logging
from dotenv import load_dotenv

# Create a logger object
logger = logging.getLogger()


def add_container_registries(base_url, token, existing_container_registries, ghcr_list, ghcr_organization, github_token_name):
    url = f"{base_url}/api/v1/settings/registry?project=Central+Console&scanLater=false"
    headers = {"content-type": "application/json; charset=UTF-8", "Authorization": "Bearer " + token}

    for registry in ghcr_list:
        # Check if the registry already exists
        image_name = f"{ghcr_organization.lower()}/{registry['name'].lower()}"
        if not any(
            existing_registry["repository"] == image_name
            for existing_registry in existing_container_registries["specifications"]
        ):
            new_registry = {
                "version": "gitlab",
                "registry": "ghcr.io",
                "namespace": "",
                "repository": image_name,
                "tag": "",
                "credentialID": f"{github_token_name}",
                "os": "linux",
                "harborDeploymentSecurity": False,
                "collections": ["All"],
                "cap": 2,
                "scanners": 10,
                "versionPattern": "",
            }

            # Add the new registry to the specifications list
            existing_container_registries["specifications"].append(new_registry)
            logger.info(f"Registry to be added: {registry['name'].lower()}")
        else:
            logger.info(f"Registry {registry['name']} already exists in Prisma Cloud")

    # Convert the updated registries to JSON
    payload = json.dumps(existing_container_registries)

    try:
        response = requests.request("PUT", url, headers=headers, data=payload)
        response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
    except requests.exceptions.RequestException as err:
        logger.error("Oops! An exception occurred in add_container_registries, ", err)
        logger.error(f"{response.text}")
        return None

    logger.info("All GHCR registry for your Github Organization have been added successfully")


def get_container_registries(base_url, token):
    url = f"{base_url}/api/v1/settings/registry?project=Central+Console"
    headers = {"content-type": "application/json; charset=UTF-8", "Authorization": "Bearer " + token}

    try:
        response = requests.request("GET", url, headers=headers)
        response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
    except requests.exceptions.RequestException as err:
        logger.error("Oops! An exception occurred in get_container_registries, ", err)
        logger.error(f"{response.text}")
        return None

    logger.debug(f"Response status code: {response.status_code}")
    logger.debug(f"Response headers: {response.headers}")
    logger.debug(f"Response text: {response.text}")
    return response.json()


def get_images_number_per_regristry(base_url, token):
    url = f"{base_url}/api/v1/registry?compact=true?project=Central+Console"
    headers = {"content-type": "application/json; charset=UTF-8", "Authorization": "Bearer " + token}

    try:
        response = requests.request("GET", url, headers=headers)
        response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
    except requests.exceptions.RequestException as err:
        logger.error("Oops! An exception occurred in get_container_registries, ", err)
        logger.error(f"{response.text}")
        return None

    response_json = response.json()
    registry_count = {}

    for item in response_json:
        for tag in item["tags"]:
            registry = tag["registry"]
            if registry not in registry_count:
                registry_count[registry] = 1
            else:
                registry_count[registry] += 1

    # Sort the dictionary in descending order by value
    sorted_registry_count = dict(sorted(registry_count.items(), key=lambda item: item[1], reverse=True))
    return sorted_registry_count


def set_github_pat_token(base_url, token, github_token, github_token_name):
    url = f"{base_url}/api/v1/credentials"
    payload = json.dumps(
        {
            "serviceAccount": {},
            "apiToken": {"encrypted": "", "plain": f"{github_token}"},
            "description": "Created by Python Script",
            "url": "",
            "skipVerify": False,
            "_id": f"{github_token_name}",
            "type": "gitlabToken",
        }
    )
    headers = {"content-type": "application/json; charset=UTF-8", "Authorization": "Bearer " + token}

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
    except requests.exceptions.RequestException as err:
        logger.error("Oops! An exception occurred in set_github_pat_token, ", err)
        logger.error(f"{response.text}")
        return None

    logger.debug(f"Response status code: {response.status_code}")
    logger.debug(f"Response headers: {response.headers}")
    logger.debug(f"Response text: {response.text}")


def list_ghcr_images(org_name, github_token, limit=0):
    if limit < 0:
        raise ValueError("Limit must be 0 (for no limit) or a positive integer.")

    headers = {"Authorization": f"Bearer {github_token}"}
    gh_registries = []
    page = 1

    # Continue looping if limit is 0 (no limit) or we haven't reached the limit yet.
    while limit == 0 or len(gh_registries) < limit:
        url = f"https://api.github.com/orgs/{org_name}/packages?package_type=container&page={page}&per_page=100"
        logging.info(f"Fetching data from URL: {url}")

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logging.error(f"Failed to fetch packages, HTTP status code: {response.status_code}")
            break

        packages = response.json()
        if not packages:
            break

        for package in packages:
            if package["package_type"] == "container":
                registry = {"name": package["name"], "visibility": package["visibility"]}
                gh_registries.append(registry)
                if limit != 0 and len(gh_registries) == limit:
                    break
        else:
            page += 1  # Only increment the page if we haven't filled our limit.

    return gh_registries


def get_compute_url(base_url, token):
    url = f"https://{base_url}/meta_info"
    headers = {"content-type": "application/json; charset=UTF-8", "Authorization": "Bearer " + token}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
    except requests.exceptions.RequestException as err:
        logger.error("Oops! An exception occurred in get_compute_url, ", err)
        return None

    response_json = response.json()
    return response_json.get("twistlockUrl", None)


def login_saas(base_url, access_key, secret_key):
    url = f"https://{base_url}/login"
    payload = json.dumps({"username": access_key, "password": secret_key})
    headers = {"content-type": "application/json; charset=UTF-8"}
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
    except Exception as e:
        logger.info(f"Error in login_saas: {e}")
        return None

    return response.json().get("token")


def login_compute(base_url, access_key, secret_key):
    url = f"{base_url}/api/v1/authenticate"

    payload = json.dumps({"username": access_key, "password": secret_key})
    headers = {"content-type": "application/json; charset=UTF-8"}
    response = requests.post(url, headers=headers, data=payload)
    return response.json()["token"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--organization", help="Github Organization")
    parser.add_argument("-t", "--ghcr-token-name", help="Github Token Name in Prisma Cloud")
    parser.add_argument("-l", "--limit", help="Github Token Name in Prisma Cloud", default=0)
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()

    if args.debug:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO

    logging.basicConfig(
        level=logging_level, format="%(asctime)s - %(levelname)s - %(message)s", filename="app.log", filemode="a"
    )

    # Create a console handler
    console_handler = logging.StreamHandler()

    # Add the console handler to the logger
    logger.addHandler(console_handler)

    logger.info("======================= START =======================")
    logger.debug("======================= DEBUG MODE =======================")

    load_dotenv()

    url = os.environ.get("PRISMA_API_URL")
    identity = os.environ.get("PRISMA_ACCESS_KEY")
    secret = os.environ.get("PRISMA_SECRET_KEY")
    github_token = os.environ.get("GITHUB_TOKEN")
    ghcr_orgamization = args.organization
    ghcr_token_name = args.ghcr_token_name
    limit = args.limit

    if not url or not identity or not secret or not github_token:
        logger.error("PRISMA_API_URL, PRISMA_ACCESS_KEY, PRISMA_SECRET_KEY, GITHUB_TOKEN variables are not set.")
        return

    if not ghcr_orgamization:
        logger.error("GitHub organization name is required. Use --organization to specify it.")
        return

    if not ghcr_token_name:
        logger.error("GitHub Token name is required. Use --ghcr-token-name to specify it.")
        return

    token = login_saas(url, identity, secret)
    compute_url = get_compute_url(url, token)
    compute_token = login_compute(compute_url, identity, secret)
    logger.debug(f"Compute url: {compute_url}")

    if token is None:
        logger.error("Unable to authenticate.")
        return
    
    try:
        limit = int(limit)  # Convert limit to an integer
    except ValueError:
        raise ValueError("Limit must be a valid integer.")

    gh_registries = list_ghcr_images(ghcr_orgamization, github_token, limit)

    set_github_pat_token(compute_url, compute_token, github_token, ghcr_token_name)

    container_registries_list_from_cwp = get_container_registries(compute_url, compute_token)
    add_container_registries(
        compute_url, compute_token, container_registries_list_from_cwp, gh_registries, ghcr_orgamization, ghcr_token_name
    )

    logger.info("======================= END =======================")


if __name__ == "__main__":
    main()
