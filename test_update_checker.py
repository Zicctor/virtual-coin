"""Test the update checker"""
from utils.update_checker import UpdateChecker

print("Checking for updates...")
result = UpdateChecker.check_for_updates()

print(f"Current version: {result['current_version']}")
print(f"Latest version: {result['latest_version']}")
print(f"Update available: {result['update_available']}")

if result.get('error'):
    print(f"Error: {result['error']}")
elif result['update_available']:
    print(f"Download from: {result['download_url']}")
    print(f"\nRelease notes:\n{result['release_notes']}")
else:
    print("App is up to date!")
