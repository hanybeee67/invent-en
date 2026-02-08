"""
Backup utilities for Everest Inventory System
- Automatic backup creation
- Backup restoration
- Old backup cleanup
"""

import os
import shutil
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import pandas as pd


def get_backup_dir(base_dir: str) -> str:
    """Get the backup directory path."""
    return os.path.join(base_dir, "backups")


def create_backup(base_dir: str, files_to_backup: List[str]) -> Tuple[bool, str]:
    """
    Create a backup of specified files.
    
    Args:
        base_dir: Base data directory
        files_to_backup: List of file paths to backup
        
    Returns:
        Tuple of (success, message/error)
    """
    try:
        # Create backup folder with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = os.path.join(get_backup_dir(base_dir), timestamp)
        
        os.makedirs(backup_folder, exist_ok=True)
        
        # Copy files
        backed_up = []
        for file_path in files_to_backup:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                dest = os.path.join(backup_folder, filename)
                shutil.copy2(file_path, dest)
                backed_up.append(filename)
        
        if backed_up:
            return True, f"✅ Backup created: {len(backed_up)} files in {timestamp}"
        else:
            return False, "⚠️ No files found to backup"
            
    except Exception as e:
        return False, f"❌ Backup failed: {str(e)}"


def list_backups(base_dir: str) -> List[dict]:
    """
    List all available backups.
    
    Args:
        base_dir: Base data directory
        
    Returns:
        List of backup info dicts with 'name', 'date', 'path', 'size'
    """
    backup_dir = get_backup_dir(base_dir)
    
    if not os.path.exists(backup_dir):
        return []
    
    backups = []
    for folder_name in os.listdir(backup_dir):
        folder_path = os.path.join(backup_dir, folder_name)
        
        if os.path.isdir(folder_path):
            # Get folder size
            total_size = sum(
                os.path.getsize(os.path.join(folder_path, f))
                for f in os.listdir(folder_path)
                if os.path.isfile(os.path.join(folder_path, f))
            )
            
            # Parse date from folder name
            try:
                backup_date = datetime.strptime(folder_name, "%Y%m%d_%H%M%S")
            except ValueError:
                # Old format or manual folder
                backup_date = datetime.fromtimestamp(os.path.getmtime(folder_path))
            
            backups.append({
                "name": folder_name,
                "date": backup_date,
                "path": folder_path,
                "size": total_size,
                "size_mb": round(total_size / 1024 / 1024, 2)
            })
    
    # Sort by date (newest first)
    backups.sort(key=lambda x: x["date"], reverse=True)
    return backups


def restore_from_backup(backup_path: str, target_dir: str) -> Tuple[bool, str]:
    """
    Restore files from a backup.
    
    Args:
        backup_path: Path to backup folder
        target_dir: Target directory to restore to
        
    Returns:
        Tuple of (success, message/error)
    """
    try:
        if not os.path.exists(backup_path):
            return False, f"❌ Backup not found: {backup_path}"
        
        # Copy all files from backup to target
        restored = []
        for filename in os.listdir(backup_path):
            src = os.path.join(backup_path, filename)
            dest = os.path.join(target_dir, filename)
            
            if os.path.isfile(src):
                shutil.copy2(src, dest)
                restored.append(filename)
        
        return True, f"✅ Restored {len(restored)} files from backup"
        
    except Exception as e:
        return False, f"❌ Restore failed: {str(e)}"


def cleanup_old_backups(base_dir: str, retention_days: int = 30) -> Tuple[bool, str]:
    """
    Delete backups older than retention period.
    
    Args:
        base_dir: Base data directory
        retention_days: Number of days to keep backups
        
    Returns:
        Tuple of (success, message)
    """
    try:
        backup_dir = get_backup_dir(base_dir)
        
        if not os.path.exists(backup_dir):
            return True, "No backups to clean up"
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted = []
        
        for folder_name in os.listdir(backup_dir):
            folder_path = os.path.join(backup_dir, folder_name)
            
            if os.path.isdir(folder_path):
                # Get folder date
                try:
                    folder_date = datetime.strptime(folder_name, "%Y%m%d_%H%M%S")
                except ValueError:
                    # Use modification time for old format
                    folder_date = datetime.fromtimestamp(os.path.getmtime(folder_path))
                
                # Delete if older than cutoff
                if folder_date < cutoff_date:
                    shutil.rmtree(folder_path)
                    deleted.append(folder_name)
        
        if deleted:
            return True, f"🗑️ Deleted {len(deleted)} old backups (>{retention_days} days)"
        else:
            return True, f"✅ No old backups to delete (retention: {retention_days} days)"
            
    except Exception as e:
        return False, f"❌ Cleanup failed: {str(e)}"


def get_backup_stats(base_dir: str) -> dict:
    """
    Get backup statistics.
    
    Args:
        base_dir: Base data directory
        
    Returns:
        Dict with backup statistics
    """
    backups = list_backups(base_dir)
    
    if not backups:
        return {
            "total_backups": 0,
            "total_size_mb": 0,
            "oldest_date": None,
            "newest_date": None
        }
    
    total_size = sum(b["size"] for b in backups)
    
    return {
        "total_backups": len(backups),
        "total_size_mb": round(total_size / 1024 / 1024, 2),
        "oldest_date": backups[-1]["date"],
        "newest_date": backups[0]["date"]
    }


# For testing
if __name__ == "__main__":
    test_dir = "./test_backups"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create dummy file
    test_file = os.path.join(test_dir, "test.csv")
    pd.DataFrame({"a": [1, 2, 3]}).to_csv(test_file, index=False)
    
    # Test backup
    success, msg = create_backup(test_dir, [test_file])
    print(msg)
    
    # List backups
    backups = list_backups(test_dir)
    print(f"Found {len(backups)} backup(s)")
    
    # Stats
    stats = get_backup_stats(test_dir)
    print(f"Stats: {stats}")
    
    # Cleanup (optional)
    # shutil.rmtree(test_dir)
