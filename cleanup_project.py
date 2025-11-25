"""
Clean up development files before distribution.
Removes test files, migration files, and documentation that's not needed in the package.
"""
import os
import shutil
from pathlib import Path

# Files to remove
FILES_TO_REMOVE = [
    # Test files
    'check_api_key.py',
    'check_database.py',
    'test_api.py',
    'test_database.py',
    'test_http_direct.py',
    'test_neon_connection.py',
    'test_neon_persistence.py',
    'test_simple_connection.py',
    'diagnose_database.py',
    'delete_all_users.py',
    
    # Fix/migration scripts
    'fix_p2p_columns.py',
    'fix_p2p_columns.sql',
    'fix_rls_policies.sql',
    'database_updates.sql',
    'setup_historical_data.py',
    
    # Documentation (keep only README.md)
    'DEPLOYMENT_GUIDE.md',
    'HISTORICAL_DATA_README.md',
    'MIGRATION_READY.md',
    'NEON_MIGRATION.md',
    'QUICKREF_REALDATA.txt',
    
    # SQL files
    'database_schema.sql',
    
    # Example files
    '.env.example',
    
    # Build artifacts
    'DuckyTrading.spec',
    
    # Requirements (keep only requirements.txt)
    'requirements-neon.txt',
    
    # Git files
    '.gitignore',
]

# Directories to remove
DIRS_TO_REMOVE = [
    'migrations',
    'sql',
    '__pycache__',
    'build',
]

def cleanup():
    """Remove development files and directories."""
    print("=" * 80)
    print("  Cleaning up development files")
    print("=" * 80)
    
    removed_files = []
    removed_dirs = []
    errors = []
    
    # Remove files
    for filename in FILES_TO_REMOVE:
        filepath = Path(filename)
        if filepath.exists():
            try:
                filepath.unlink()
                removed_files.append(filename)
                print(f"✅ Removed: {filename}")
            except Exception as e:
                errors.append(f"Failed to remove {filename}: {e}")
                print(f"❌ Failed: {filename} - {e}")
    
    # Remove directories
    for dirname in DIRS_TO_REMOVE:
        dirpath = Path(dirname)
        if dirpath.exists():
            try:
                shutil.rmtree(dirpath)
                removed_dirs.append(dirname)
                print(f"✅ Removed: {dirname}/")
            except Exception as e:
                errors.append(f"Failed to remove {dirname}: {e}")
                print(f"❌ Failed: {dirname}/ - {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("  Cleanup Summary")
    print("=" * 80)
    print(f"Files removed: {len(removed_files)}")
    print(f"Directories removed: {len(removed_dirs)}")
    
    if errors:
        print(f"\n⚠️  Errors: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
    
    print("\n✅ Cleanup complete!")
    print("\nRemaining important files:")
    print("  • main.py - Application entry point")
    print("  • config.py - Configuration")
    print("  • README.md - User documentation")
    print("  • requirements.txt - Dependencies")
    print("  • package_app.py - Build script")
    print("  • encrypt_credentials.py - Credential encryption")
    print("  • master_test.py - Test suite")
    print("  • reset_database.py - Database reset utility")
    print("  • auth/, ui/, utils/, assets/, credentials/ - Core modules")

if __name__ == '__main__':
    response = input("⚠️  This will delete development/test files. Continue? (yes/no): ")
    if response.lower() == 'yes':
        cleanup()
    else:
        print("❌ Cleanup cancelled")
