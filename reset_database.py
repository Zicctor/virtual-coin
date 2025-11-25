"""Reset database to initial state for testing."""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.db_factory import get_database
from config import Config

def reset_database():
    """Reset all user data to initial state."""
    try:
        db = get_database()
        
        # Get your user ID (assumes you're the only user or first user)
        print("Finding your user account...")
        
        # Try to find user by Google ID or email
        # You'll need to replace this with your actual Google ID or we'll just reset all users
        
        # For simplicity, let's reset ALL users
        confirm = input("⚠️  This will DELETE ALL transactions and reset ALL wallets to $10,000 USDT. Continue? (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("❌ Reset cancelled.")
            return
        
        print("\n🗑️  Deleting all data...")
        
        # Delete all P2P trade transactions
        db._execute('DELETE FROM "P2PTradeTransactions"')
        print("✅ Deleted all P2P trade transactions")
        
        # Delete all trade offers
        db._execute('DELETE FROM "TradeOffers"')
        print("✅ Deleted all P2P trade offers")
        
        # Delete all orders
        db._execute('DELETE FROM "Orders"')
        print("✅ Deleted all orders")
        
        # Delete all transactions
        db._execute('DELETE FROM "Transactions"')
        print("✅ Deleted all transactions")
        
        # Reset all wallets to initial state
        db._execute('DELETE FROM "Wallets"')
        print("✅ Deleted all wallets")
        
        # Get all users
        users = db._execute('SELECT user_id FROM "Users"')
        print(f"\n🔄 Reinitializing wallets for {len(users)} user(s)...")
        
        for user in users:
            user_id = user['user_id']
            db.initialize_user_wallets(user_id)
            print(f"✅ Reset user {user_id} to $10,000 USDT")
        
        # Reset last login bonus time to allow immediate bonus claim
        db._execute('UPDATE "Users" SET last_login_bonus = NULL')
        print("✅ Reset daily bonus eligibility")
        
        print("\n✨ Database reset complete!")
        print("📊 All users now have:")
        print("   - $10,000 USDT")
        print("   - 0 balance in all other coins")
        print("   - No transaction history")
        print("   - Daily bonus available")
        
    except Exception as e:
        print(f"\n❌ Error resetting database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("🔄 DATABASE RESET TOOL")
    print("=" * 60)
    print("\nThis will:")
    print("  • Delete ALL transactions")
    print("  • Delete ALL P2P trades and offers")
    print("  • Delete ALL orders")
    print("  • Reset ALL wallets to $10,000 USDT")
    print("  • Reset daily bonus eligibility")
    print()
    
    reset_database()
