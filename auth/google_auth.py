"""Google OAuth authentication handler for PyQt6 crypto trading app."""
import os
import json
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# OAuth 2.0 scopes
SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 
          'https://www.googleapis.com/auth/userinfo.profile']

# File paths for credentials
CREDENTIALS_DIR = Path(__file__).parent.parent / 'credentials'
TOKEN_FILE = CREDENTIALS_DIR / 'token.pickle'
CLIENT_SECRET_FILE = CREDENTIALS_DIR / 'client_secret.json'


class GoogleAuthManager:
    """Manages Google OAuth authentication flow with Supabase integration."""
    
    def __init__(self):
        """Initialize the authentication manager."""
        self.creds = None
        self.user_info = None
        self.db_user = None  # Supabase user record
        CREDENTIALS_DIR.mkdir(exist_ok=True)
    
    def is_authenticated(self):
        """Check if user is already authenticated with valid credentials."""
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, 'rb') as token:
                self.creds = pickle.load(token)
        
        # Check if credentials exist and are valid
        if self.creds and self.creds.valid:
            return True
        
        # Try to refresh expired credentials
        if self.creds and self.creds.expired and self.creds.refresh_token:
            try:
                self.creds.refresh(Request())
                self._save_credentials()
                return True
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                return False
        
        return False
    
    def authenticate(self, force_new_login=False):
        """
        Perform Google OAuth authentication flow.
        Args:
            force_new_login: If True, clears existing token to allow switching accounts
        Returns True if successful, False otherwise.
        """
        # Clear old token if forcing new login (account switching)
        if force_new_login and TOKEN_FILE.exists():
            print("🔄 Clearing old authentication token...")
            TOKEN_FILE.unlink()
            self.creds = None
            self.user_info = None
            self.db_user = None
        
        if not CLIENT_SECRET_FILE.exists():
            raise FileNotFoundError(
                f"Client secret file not found at {CLIENT_SECRET_FILE}\n"
                "Please download your OAuth 2.0 credentials from Google Cloud Console:\n"
                "1. Go to https://console.cloud.google.com/apis/credentials\n"
                "2. Create OAuth 2.0 Client ID (Desktop app)\n"
                "3. Download the JSON file and save it as 'client_secret.json' in the credentials folder"
            )
        
        try:
            print("\n🔐 Starting Google OAuth authentication...")
            print("🌐 A browser window will open for you to sign in with Google")
            print("⏳ Please complete the authorization in your browser...\n")
            
            # Run the OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRET_FILE), 
                SCOPES
            )
            
            # This will open a browser window for authentication
            # Using run_local_server with default settings for Desktop app
            self.creds = flow.run_local_server(
                port=0,  # Use random available port
                prompt='consent',  # Force account selection
                success_message='Authentication successful! You can close this window and return to the app.',
                open_browser=True
            )
            
            print("✅ Authentication successful!")
            
            # Save credentials for future use
            self._save_credentials()
            
            # Get user info
            self._fetch_user_info()
            
            # Sync user with Supabase database
            self._sync_user_to_database()
            
            return True
            
        except Exception as e:
            print(f"\n❌ Authentication error: {e}")
            print("\n💡 Troubleshooting:")
            print("   1. Make sure you completed the authorization in the browser")
            print("   2. Check if your browser is blocking popups")
            print("   3. Verify OAuth consent screen is configured in Google Cloud Console")
            print("   4. Ensure you're using a Desktop app OAuth client (not Web app)\n")
            return False
    
    def _save_credentials(self):
        """Save credentials to file for future use."""
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(self.creds, token)
    
    def _fetch_user_info(self):
        """Fetch user information from Google."""
        if not self.creds:
            print("❌ ERROR: No credentials available to fetch user info")
            return None
            
        try:
            service = build('oauth2', 'v2', credentials=self.creds)
            self.user_info = service.userinfo().get().execute()
            print(f"✅ User info fetched: {self.user_info.get('email', 'Unknown')}")
            return self.user_info
        except Exception as e:
            print(f"❌ Error fetching user info: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _sync_user_to_database(self):
        """Sync authenticated user to Supabase database."""
        try:
            from utils.db_factory import get_database
            
            if not self.user_info:
                print("❌ ERROR: No user info available for database sync")
                return
            
            db = get_database()
            google_id = self.user_info.get('id')
            email = self.user_info.get('email')
            name = self.user_info.get('name', email)
            
            print(f"\n{'='*60}")
            print(f"🔄 Syncing user to database: {email}")
            print(f"   Google ID: {google_id}")
            print(f"   Name: {name}")
            print(f"{'='*60}\n")
            
            # Check if user exists
            print("📌 Checking if user exists in database...")
            existing_user = db.get_user_by_google_id(google_id)
            
            if existing_user:
                # User exists
                self.db_user = existing_user
                print(f"✅ Existing user logged in: {email}")
                print(f"   User ID: {existing_user['user_id']}")
                print(f"   Database record: {existing_user}")
                
                # Check if user has wallets (in case database was reset)
                try:
                    print("   Checking for wallets...")
                    wallets = db.get_user_wallets(existing_user['user_id'])
                    if not wallets or len(wallets) == 0:
                        print("   ⚠️  No wallets found - initializing wallets...")
                        db.initialize_user_wallets(existing_user['user_id'])
                        print("   ✅ Wallets initialized with $10,000 USDT\n")
                    else:
                        print(f"   ✅ {len(wallets)} wallet(s) found\n")
                except Exception as wallet_error:
                    print(f"   ⚠️  Error checking/initializing wallets: {wallet_error}")
                    print("   Continuing anyway...\n")
            else:
                # Create new user
                print(f"👤 Creating new user: {email}")
                new_user = db.create_user(google_id, email, name)
                
                if new_user:
                    self.db_user = new_user
                    print(f"✅ New user created successfully!")
                    print(f"   User ID: {new_user['user_id']}")
                    print(f"   Initial balance: $10,000 USDT")
                    print(f"   Database record: {new_user}\n")
                else:
                    print("❌ ERROR: Failed to create new user in database")
                    print("   Please check Supabase connection and credentials\n")
                    self.db_user = None
            
        except Exception as e:
            print(f"\n❌ ERROR syncing user to database: {e}")
            import traceback
            traceback.print_exc()
            print()
            self.db_user = None
    
    def get_user_info(self):
        """Get authenticated user information."""
        if not self.user_info and self.creds:
            self._fetch_user_info()
        return self.user_info
    
    def get_db_user(self):
        """Get Supabase database user record."""
        return self.db_user
    
    def logout(self):
        """Clear authentication and remove stored credentials."""
        print("🚪 Logging out...")
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
            print("✅ Credentials deleted")
        self.creds = None
        self.user_info = None
        self.db_user = None
        print("✅ Logout complete - all session data cleared")
    
    def get_user_email(self):
        """Get the authenticated user's email."""
        info = self.get_user_info()
        return info.get('email', '') if info else ''
    
    def get_user_name(self):
        """Get the authenticated user's name."""
        info = self.get_user_info()
        return info.get('name', '') if info else ''
    
    def get_user_picture(self):
        """Get the authenticated user's profile picture URL."""
        info = self.get_user_info()
        return info.get('picture', '') if info else ''
