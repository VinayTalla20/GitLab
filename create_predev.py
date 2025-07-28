import json
import logging
from flask import Flask, request
import requests

app = Flask(__name__)

# GitLab API details
GITLAB_API_URL = "https://gitlab.com/api/v4"
TOKEN = ""
HEADERS = {"PRIVATE-TOKEN": TOKEN}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_branch_exists(project_id, branch_name):
    url = f"{GITLAB_API_URL}/projects/{project_id}/repository/branches/{branch_name}"
    resp = requests.get(url, headers=HEADERS)
    return resp.status_code == 200

def delete_branch(project_id, branch_name):
    url = f"{GITLAB_API_URL}/projects/{project_id}/repository/branches/{branch_name}"
    resp = requests.delete(url, headers=HEADERS)
    return resp.status_code == 204

def create_branch_from_dev(project_id, new_branch="predev", from_branch="dev"):
    url = f"{GITLAB_API_URL}/projects/{project_id}/repository/branches"
    data = {"branch": new_branch, "ref": from_branch}
    resp = requests.post(url, headers=HEADERS, data=data)
    return resp.status_code == 201

@app.route("/predev", methods=["POST"])
def webhook():
    data = request.json
    logger.info("Received webhook payload: %s", json.dumps(data, indent=2))

    if data.get("event_type") == "merge_request":
        attrs = data.get("object_attributes", {})
        state = attrs.get("state")
        target_branch = attrs.get("target_branch")
        project_id = data.get("project", {}).get("id")
        project_name = data.get("project", {}).get("path_with_namespace")
        project_group = data.get("project", {}).get("namespace")
        logger.info(f"Received merge_request event: state={state}, target_branch={target_branch}, project={project_name}")

        if state == "merged" and target_branch == "dev" and project_group == "XCommunity":
            if check_branch_exists(project_id, "dev"):
                delete_branch(project_id, "predev")
                success = create_branch_from_dev(project_id)
                if success:
                    logger.info(f"✅ Created 'predev' from 'dev' in {project_name}")
                else:
                    logger.error(f"❌ Failed to create 'predev' in {project_name}")
            else:
                logger.warning(f"⚠️ 'dev' branch not found in {project_name}")
        else:
            logger.info(f"⚠️ Ignored merge_request: state={state}, target_branch={target_branch}")

        return "OK", 200

    logger.info(f"Ignored system hook event: {data.get('event_type')}")
    return "Ignored", 200

if __name__ == "__main__":
    app.run(port=5003)
