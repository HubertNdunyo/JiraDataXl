"""
Monitoring functions for the application
"""
import psutil
from core.db.db_core import get_connection

def monitor_database_size():
    """Monitor database size and statistics"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Get database size
        cur.execute("""
            SELECT pg_database_size(current_database()) as size,
                   (SELECT count(*) FROM jira_issues_v2) as issue_count
        """)
        result = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return {
            'size_bytes': result[0] if result else 0,
            'size_mb': round(result[0] / 1024 / 1024, 2) if result else 0,
            'issue_count': result[1] if result else 0
        }
    except Exception as e:
        return {
            'size_bytes': 0,
            'size_mb': 0,
            'issue_count': 0,
            'error': str(e)
        }

def monitor_memory_usage():
    """Monitor system memory usage"""
    memory = psutil.virtual_memory()
    return {
        'total': memory.total,
        'available': memory.available,
        'percent': memory.percent,
        'used': memory.used
    }