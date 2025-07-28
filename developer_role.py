import requests
import logging

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# GitLab API settings
GITLAB_API_URL = ''
PRIVATE_TOKEN = ''

def update_user_role(user_id, group_id, role):
    url = f"{GITLAB_API_URL}/groups/{group_id}/members"
    headers = {
        'Private-Token': PRIVATE_TOKEN,
        'Content-Type': 'application/json'
    }
    payload = {
        'user_id': user_id,
        'access_level': role  # GitLab roles: 30 = Developer, 40 = Maintainer, etc.
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.status_code, response.json()

@app.route('/', methods=['POST'])
def handle_event():
    event = request.json

    if event['event_name'] == 'user_create':
        user_id = event['user_id']
        user_name = event.get('name', 'Unknown')
        user_email = event.get('email', 'Unknown')

        # Log user creation event with email
        log_message = f"User created: ID={user_id}, Name={user_name}, Email={user_email}"
        logger.info(log_message)

        group_id = 8506
        role = 30  # Developer role in GitLab
        status_code, response = update_user_role(user_id, group_id, role)
        if status_code == 201:
            logger.info(f"User role updated successfully for user ID={user_id}")
            return jsonify({'message': 'User role updated successfully'}), 200
        else:
            logger.error(f"Failed to update user role for user ID={user_id}, Error: {response}")
            return jsonify({'message': 'Failed to update user role', 'error': response}), 500
    else:
        logger.warning(f"Unhandled event: {event['event_name']}")

    return jsonify({'message': 'Event not handled'}), 400

if __name__ == '__main__':
    app.run(port=5000)
