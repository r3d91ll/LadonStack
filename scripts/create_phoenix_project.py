#!/usr/bin/env python3
"""
Create Phoenix Project Script

This script creates a new project in Arize Phoenix for PathRAG monitoring.
"""

import requests
import json
import sys
import time
import os

# Phoenix API settings
PHOENIX_HOST = os.environ.get("PHOENIX_HOST", "localhost")
PHOENIX_PORT = os.environ.get("PHOENIX_PORT", "8084")
PHOENIX_URL = f"http://{PHOENIX_HOST}:{PHOENIX_PORT}"
PROJECT_NAME = os.environ.get("PHOENIX_PROJECT_NAME", "pathrag-inference")

def check_phoenix_health():
    """Check if Phoenix is running and accessible"""
    try:
        response = requests.get(f"{PHOENIX_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Failed to connect to Phoenix: {e}")
        return False

def get_projects():
    """Get list of projects in Phoenix"""
    try:
        response = requests.post(
            f"{PHOENIX_URL}/graphql",
            json={
                "query": """
                query GetProjects {
                    projects {
                        id
                        name
                        createdAt
                    }
                }
                """
            }
        )
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "projects" in data["data"]:
                return data["data"]["projects"]
        print(f"❌ Failed to get projects: {response.text}")
        return []
    except Exception as e:
        print(f"❌ Error getting projects: {e}")
        return []

def create_project(name):
    """Create a new project in Phoenix"""
    try:
        response = requests.post(
            f"{PHOENIX_URL}/graphql",
            json={
                "query": """
                mutation CreateProject($name: String!) {
                    createProject(name: $name) {
                        project {
                            id
                            name
                        }
                    }
                }
                """,
                "variables": {
                    "name": name
                }
            }
        )
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "createProject" in data["data"]:
                return data["data"]["createProject"]["project"]
            else:
                print(f"❌ Failed to create project: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Failed to create project: {response.text}")
        return None
    except Exception as e:
        print(f"❌ Error creating project: {e}")
        return None

def main():
    """Main function"""
    print(f"🔍 Connecting to Phoenix at {PHOENIX_URL}")
    
    # Wait for Phoenix to be ready
    retries = 0
    while retries < 10:
        if check_phoenix_health():
            print("✅ Phoenix is running")
            break
        print(f"⏳ Waiting for Phoenix to be ready (attempt {retries+1}/10)...")
        retries += 1
        time.sleep(2)
    
    if retries == 10:
        print("❌ Phoenix is not running after multiple attempts")
        sys.exit(1)
    
    # Get existing projects
    projects = get_projects()
    print(f"📋 Found {len(projects)} existing projects")
    
    # Check if our project already exists
    project_exists = False
    for project in projects:
        if project["name"] == PROJECT_NAME:
            print(f"✅ Project '{PROJECT_NAME}' already exists with ID: {project['id']}")
            project_exists = True
            break
    
    # Create project if it doesn't exist
    if not project_exists:
        print(f"🔧 Creating new project: {PROJECT_NAME}")
        new_project = create_project(PROJECT_NAME)
        if new_project:
            print(f"✅ Created project '{new_project['name']}' with ID: {new_project['id']}")
        else:
            print(f"❌ Failed to create project: {PROJECT_NAME}")
            sys.exit(1)
    
    print("✅ Phoenix project setup complete")

if __name__ == "__main__":
    main()
