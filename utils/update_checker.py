"""
Update checker for DuckyTrading
Checks GitHub releases for new versions
"""
import requests
from packaging import version as pkg_version
from version import VERSION


class UpdateChecker:
    """Check for app updates from GitHub releases."""
    
    GITHUB_REPO = "Zicctor/virtual-coin"  # Your GitHub repo
    GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    
    @staticmethod
    def check_for_updates():
        """
        Check if a new version is available.
        
        Returns:
            dict: {
                'update_available': bool,
                'current_version': str,
                'latest_version': str,
                'download_url': str,
                'release_notes': str
            }
        """
        try:
            response = requests.get(UpdateChecker.GITHUB_API, timeout=5)
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data['tag_name'].lstrip('v')  # Remove 'v' prefix if present
            current_version = VERSION
            
            # Compare versions
            update_available = pkg_version.parse(latest_version) > pkg_version.parse(current_version)
            
            # Get download URL for the zip file
            download_url = None
            for asset in release_data.get('assets', []):
                if asset['name'].endswith('.zip'):
                    download_url = asset['browser_download_url']
                    break
            
            if not download_url:
                download_url = release_data.get('html_url', '')
            
            return {
                'update_available': update_available,
                'current_version': current_version,
                'latest_version': latest_version,
                'download_url': download_url,
                'release_notes': release_data.get('body', 'No release notes available.'),
                'release_name': release_data.get('name', f'v{latest_version}')
            }
            
        except requests.RequestException as e:
            print(f"Failed to check for updates: {e}")
            return {
                'update_available': False,
                'current_version': VERSION,
                'latest_version': VERSION,
                'download_url': '',
                'release_notes': '',
                'error': str(e)
            }
        except Exception as e:
            print(f"Error checking for updates: {e}")
            return {
                'update_available': False,
                'current_version': VERSION,
                'latest_version': VERSION,
                'download_url': '',
                'release_notes': '',
                'error': str(e)
            }


if __name__ == '__main__':
    # Test the update checker
    print("Checking for updates...")
    result = UpdateChecker.check_for_updates()
    print(f"Current version: {result['current_version']}")
    print(f"Latest version: {result['latest_version']}")
    print(f"Update available: {result['update_available']}")
    if result['update_available']:
        print(f"Download from: {result['download_url']}")
