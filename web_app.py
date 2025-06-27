from flask import Flask, jsonify, request, render_template, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from datetime import datetime
import os
import json
from main import fetch_all_issues, stop_sync, is_sync_stopped, setup_logging
from monitoring import monitor_database_size, monitor_memory_usage
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from core.jira.jira_client import JiraClient
import re
from urllib.parse import urlparse, parse_qs
from core.db.db_audit import get_project_update_history, get_entity_history
from datetime import timedelta

# Configure logging using centralized configuration
setup_logging()
logger = logging.getLogger(__name__)

app = Flask(__name__,
    static_folder='static',
    template_folder='templates'
)

# Add prometheus wsgi middleware to route /metrics requests
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config', 'sync_config.json') # Updated path

def load_config():
    """Load configuration from file"""
    try:
        if os.path.exists(CONFIG_FILE):
            logger.info(f"Loading config from {CONFIG_FILE}")
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                interval = config.get('interval')
                logger.info(f"Raw config loaded: {config}")
                if interval is None:
                    logger.warning("No interval found in config, using default")
                    interval = 2
                interval = max(1, int(interval))  # Ensure it's at least 1
                logger.info(f"Loaded interval from config: {interval} minutes")
                return interval
        else:
            logger.warning(f"Config file not found at {CONFIG_FILE}, creating with default interval")
            interval = 2  # Default to 2 minutes
            save_config(interval)
            logger.info(f"Created new config with interval: {interval} minutes")
            return interval
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return 2  # Default to 2 minutes

def save_config(interval):
    """Save configuration to file"""
    try:
        # Ensure interval is at least 1
        interval = max(1, int(interval))
        
        # Don't overwrite if the value is the same
        current = None
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    current = json.load(f).get('interval')
                logger.info(f"Current config value: {current}")
        except Exception as e:
            logger.error(f"Error reading current config: {e}")

        if current == interval:
            logger.info(f"Config already set to {interval} minutes, skipping save")
            return

        with open(CONFIG_FILE, 'w') as f:
            config = {'interval': interval}
            json.dump(config, f, indent=2)
            logger.info(f"Saved new config: {config}")
    except Exception as e:
        logger.error(f"Error saving config: {e}")

# Global variables
current_interval = load_config()  # Load saved interval
sync_job = None
last_sync_time = None
next_sync_time = None
sync_in_progress = False  # Track if sync is currently running
current_project = 0  # Current project being processed
total_projects = 0  # Total number of projects to process
total_issues_processed = 0  # Total number of issues processed

def schedule_sync(interval):
    global sync_job, current_interval, next_sync_time
    
    try:
        # Remove existing job if it exists
        if sync_job:
            scheduler.remove_job(sync_job.id)
        
        # Schedule new job
        sync_job = scheduler.add_job(
            fetch_all_issues,
            'interval',
            minutes=interval,
            id='sync_job'
        )
        current_interval = interval
        next_sync_time = sync_job.next_run_time
        
        # Save the new interval
        save_config(interval)
        logger.info(f"Scheduled sync with interval: {interval} minutes")
    except Exception as e:
        logger.error(f"Error scheduling sync: {e}")
        raise

@app.route('/api/status')
def get_status():
    # Get system metrics
    db_stats = monitor_database_size()
    memory_stats = monitor_memory_usage()
    
    # Calculate sync performance metrics
    sync_stats = None
    if last_sync_time:
        duration = (datetime.now() - last_sync_time).total_seconds()
        if duration > 0:
            sync_stats = {
                'duration': duration,
                'issues_per_second': total_issues_processed / duration if total_issues_processed else 0
            }

    status = {
        'current_interval': current_interval,
        'last_sync': last_sync_time.isoformat() if last_sync_time else None,
        'next_sync': next_sync_time.isoformat() if next_sync_time else None,
        'sync_in_progress': sync_in_progress,
        'sync_stopped': is_sync_stopped(),
        'database': db_stats,
        'memory': memory_stats,
        'sync_stats': sync_stats,
        'sync_progress': (current_project / total_projects * 100) if sync_in_progress and total_projects > 0 else None,
        'total_issues_processed': total_issues_processed
    }
    logger.info(f"Returning status: {status}")
    return jsonify(status)

@app.route('/api/interval', methods=['POST'])
def set_interval():
    try:
        data = request.get_json()
        logger.info(f"Received interval update request: {data}")
        
        if not data or 'interval' not in data:
            logger.error("No interval provided in request")
            return jsonify({'error': 'No interval provided'}), 400
            
        try:
            new_interval = int(data['interval'])
        except (TypeError, ValueError) as e:
            logger.error(f"Invalid interval format: {e}")
            return jsonify({'error': 'Invalid interval format'}), 400
            
        if new_interval < 1:
            logger.error(f"Invalid interval value: {new_interval}")
            return jsonify({'error': 'Interval must be at least 1 minute'}), 400
            
        schedule_sync(new_interval)
        return jsonify({'message': f'Interval set to {new_interval} minutes'})
    except Exception as e:
        logger.error(f"Error setting interval: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/sync/start', methods=['POST'])
def start_sync():
    try:
        # Reset counters
        global current_project, total_projects, total_issues_processed
        current_project = 0
        total_projects = 0
        total_issues_processed = 0
        
        schedule_sync(current_interval)
        return jsonify({'message': 'Sync scheduled successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync/stop', methods=['POST'])
def stop_all_sync():
    """Stop both scheduled and in-progress sync operations."""
    global sync_job, next_sync_time, sync_in_progress
    try:
        # Stop scheduled job if exists
        if sync_job:
            scheduler.remove_job(sync_job.id)
            sync_job = None
            next_sync_time = None
            
        # Stop in-progress sync if running
        if sync_in_progress:
            if stop_sync():
                sync_in_progress = False
                logger.info("Stopped in-progress sync")
            else:
                return jsonify({'error': 'Failed to stop in-progress sync'}), 500
                
        return jsonify({'message': 'All sync operations stopped successfully'})
    except Exception as e:
        logger.exception("Failed to stop sync operations")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync/force', methods=['POST'])
def force_sync():
    global sync_in_progress, current_project, total_projects, total_issues_processed, last_sync_time
    try:
        # Check if sync is already running
        if sync_in_progress:
            if not is_sync_stopped():
                return jsonify({
                    'error': 'Sync already in progress. Stop current sync first.'
                }), 409
            else:
                # Reset state if stopped but flag wasn't cleared
                sync_in_progress = False
                logger.info("Resetting stale sync state")

        # Reset progress tracking
        current_project = 0
        total_projects = 0
        total_issues_processed = 0
        last_sync_time = datetime.now()

        # Set up logging with timestamp
        log_name = f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        setup_logging(log_name)
        logger.info("Starting force sync")
        
        # Mark sync as started and ensure stop flag is cleared
        sync_in_progress = True
        stop_sync()  # Reset any previous stop flag
        
        try:
            success = fetch_all_issues()
            status = "stopped by user" if is_sync_stopped() else "completed"
            
            if success and not is_sync_stopped():
                logger.info("Force sync completed successfully")
                return jsonify({
                    'message': f'Force sync {status} successfully',
                    'log_file': log_name,
                    'stats': {
                        'total_projects': total_projects,
                        'total_issues': total_issues_processed,
                        'duration': (datetime.now() - last_sync_time).total_seconds()
                    }
                })
            else:
                msg = "Force sync stopped by user" if is_sync_stopped() else "Force sync completed with errors"
                logger.error(msg)
                return jsonify({
                    'error': msg,
                    'log_file': log_name
                }), 500
        finally:
            # Always mark sync as finished and reset stop flag
            sync_in_progress = False
            if is_sync_stopped():
                stop_sync()  # Reset the stop flag
            
    except Exception as e:
        sync_in_progress = False  # Ensure we reset on error
        if is_sync_stopped():
            stop_sync()  # Reset the stop flag
        logger.exception("Force sync failed")
        return jsonify({
            'error': str(e),
            'log_file': log_name
        }), 500

@app.route('/')
def dashboard():
    """Render the main dashboard."""
    return render_template('base.html')

@app.route('/jira-dashboard')
def jira_dashboard():
    """Render the JIRA query dashboard."""
    return render_template('jira_dashboard.html')

@app.route('/dropbox-viewer')
def dropbox_viewer():
    """Render the Dropbox metadata viewer."""
    return render_template('dropbox_viewer.html')

@app.route('/api/jira/issue/<issue_key>')
def get_jira_issue(issue_key):
    """Fetch a specific JIRA issue from both instances."""
    try:
        results = {}
        
        # Try instance 1
        try:
            jira1_username = os.environ.get('JIRA_USERNAME_1')
            jira1_password = os.environ.get('JIRA_PASSWORD_1')
            if jira1_username and jira1_password:
                jira1 = JiraClient(
                    'https://betteredits.atlassian.net',
                    jira1_username,
                    jira1_password
                )
                issue1 = jira1.get_issue(issue_key)
                if issue1:
                    results['instance1'] = issue1
        except Exception as e:
            logger.warning(f"Failed to fetch from instance 1: {e}")
        
        # Try instance 2
        try:
            jira2_username = os.environ.get('JIRA_USERNAME_2')
            jira2_password = os.environ.get('JIRA_PASSWORD_2')
            if jira2_username and jira2_password:
                jira2 = JiraClient(
                    'https://betteredits2.atlassian.net',
                    jira2_username,
                    jira2_password
                )
                issue2 = jira2.get_issue(issue_key)
                if issue2:
                    results['instance2'] = issue2
        except Exception as e:
            logger.warning(f"Failed to fetch from instance 2: {e}")
        
        if not results:
            return jsonify({'error': f'Issue {issue_key} not found in either instance'}), 404
            
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error fetching JIRA issue {issue_key}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dropbox/metadata', methods=['POST'])
def get_dropbox_metadata():
    """Fetch metadata for a Dropbox shared link."""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'No URL provided'}), 400
        
        url = data['url']
        
        # Parse Dropbox URL
        parsed_url = urlparse(url)
        if 'dropbox.com' not in parsed_url.netloc:
            return jsonify({'error': 'Invalid Dropbox URL'}), 400
        
        # Extract share ID from URL
        # URLs can be in formats like:
        # https://www.dropbox.com/sh/SHARE_ID/SECURITY_HASH?dl=0
        # https://www.dropbox.com/s/SHARE_ID/filename?dl=0
        path_parts = parsed_url.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            return jsonify({'error': 'Invalid Dropbox share URL format'}), 400
        
        share_type = path_parts[0]  # 'sh' for shared folder, 's' for shared file
        share_id = path_parts[1]
        
        # For demonstration, we'll return mock metadata
        # In a production environment, you would use the Dropbox API here
        metadata = {
            'share_type': 'folder' if share_type == 'sh' else 'file',
            'share_id': share_id,
            'url': url,
            'folder_name': 'Sample Dropbox Folder',
            'file_count': 15,
            'total_size': 125829120,  # 120 MB in bytes
            'files': [
                {
                    'name': 'IMG_001.jpg',
                    'type': 'image/jpeg',
                    'size': 2457600,
                    'modified': '2025-06-25T10:30:00Z'
                },
                {
                    'name': 'IMG_002.jpg', 
                    'type': 'image/jpeg',
                    'size': 3145728,
                    'modified': '2025-06-25T10:31:00Z'
                },
                {
                    'name': 'IMG_003.jpg',
                    'type': 'image/jpeg', 
                    'size': 2097152,
                    'modified': '2025-06-25T10:32:00Z'
                }
            ],
            'raw_metadata': {
                'share_type': share_type,
                'share_id': share_id,
                'parsed_url': {
                    'scheme': parsed_url.scheme,
                    'netloc': parsed_url.netloc,
                    'path': parsed_url.path,
                    'params': parsed_url.params,
                    'query': parsed_url.query,
                    'fragment': parsed_url.fragment
                }
            }
        }
        
        # Note: To implement actual Dropbox API integration, you would need:
        # 1. Dropbox API credentials (App key and secret)
        # 2. Use dropbox-sdk-python library
        # 3. Handle OAuth flow for authentication
        # 4. Use the sharing API to get metadata
        
        return jsonify(metadata)
        
    except Exception as e:
        logger.error(f"Error fetching Dropbox metadata: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync/history', methods=['GET'])
def get_sync_history():
    """Get paginated sync history."""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        project_key = request.args.get('project_key')
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Get sync history from database
        history = get_project_update_history(
            project_key=project_key,
            limit=per_page,
            offset=(page - 1) * per_page
        )
        
        # Filter by status if provided
        if status:
            history = [h for h in history if h.get('status', '').lower() == status.lower()]
        
        # Filter by date range if provided
        if start_date or end_date:
            filtered_history = []
            for h in history:
                sync_time = h.get('last_update_time')
                if sync_time:
                    if start_date and sync_time < datetime.fromisoformat(start_date):
                        continue
                    if end_date and sync_time > datetime.fromisoformat(end_date):
                        continue
                    filtered_history.append(h)
            history = filtered_history
        
        # Calculate total count (simplified - in production, do this in the query)
        total = len(history) + (page - 1) * per_page if len(history) == per_page else (page - 1) * per_page + len(history)
        
        # Format response
        response = {
            'syncs': history,
            'total': total,
            'page': page,
            'per_page': per_page,
            'has_next': len(history) == per_page
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error fetching sync history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync/stats', methods=['GET'])
def get_sync_stats():
    """Get aggregated sync statistics."""
    try:
        # Get time period
        days = int(request.args.get('days', 7))
        start_date = datetime.now() - timedelta(days=days)
        
        # Get all sync history for the period
        history = get_project_update_history(limit=1000)  # Get more records for stats
        
        # Filter by date
        recent_syncs = []
        for h in history:
            sync_time = h.get('last_update_time')
            if sync_time and sync_time >= start_date:
                recent_syncs.append(h)
        
        # Calculate statistics
        total_syncs = len(recent_syncs)
        successful_syncs = sum(1 for h in recent_syncs if h.get('status') == 'Success')
        failed_syncs = sum(1 for h in recent_syncs if h.get('status') == 'Failed')
        empty_syncs = sum(1 for h in recent_syncs if h.get('status') == 'Empty')
        
        # Calculate average duration for successful syncs
        durations = [h.get('duration', 0) for h in recent_syncs if h.get('status') == 'Success' and h.get('duration')]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Calculate syncs per day
        syncs_by_day = {}
        for h in recent_syncs:
            sync_time = h.get('last_update_time')
            if sync_time:
                day_key = sync_time.strftime('%Y-%m-%d')
                syncs_by_day[day_key] = syncs_by_day.get(day_key, 0) + 1
        
        # Get today's stats
        today = datetime.now().strftime('%Y-%m-%d')
        today_syncs = [h for h in recent_syncs if h.get('last_update_time') and h.get('last_update_time').strftime('%Y-%m-%d') == today]
        
        stats = {
            'period_days': days,
            'total_syncs': total_syncs,
            'successful_syncs': successful_syncs,
            'failed_syncs': failed_syncs,
            'empty_syncs': empty_syncs,
            'success_rate': (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0,
            'average_duration': round(avg_duration, 2),
            'syncs_by_day': syncs_by_day,
            'today': {
                'total': len(today_syncs),
                'successful': sum(1 for h in today_syncs if h.get('status') == 'Success')
            }
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error fetching sync stats: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Schedule initial sync with saved interval
    logger.info(f"Starting application with interval: {current_interval} minutes")
    schedule_sync(current_interval)
    port = int(os.environ.get('PORT', 3545))
    app.run(host='0.0.0.0', port=port)