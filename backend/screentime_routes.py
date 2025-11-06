"""
Screen Time Routes for Manual Input
Handles manual screen time logging and tracking
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from .database import db
from .models import ScreenTimeLog
import json

# Create blueprint
screentime_bp = Blueprint("screentime", __name__, url_prefix="/api/screentime")


@screentime_bp.route("/log", methods=["POST"])
@login_required
def log_screen_time():
    """
    Log screen time for a specific date
    
    Expected JSON:
    {
        "date": "2024-01-15",  # optional, defaults to today
        "screen_time_minutes": 180,
        "top_apps": [  # optional
            {"name": "Instagram", "minutes": 60},
            {"name": "TikTok", "minutes": 45},
            {"name": "YouTube", "minutes": 30}
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data or not data.get("screen_time_minutes"):
            return jsonify({"error": "Missing screen_time_minutes"}), 400
            
        screen_time_minutes = data["screen_time_minutes"]
        
        # Validate screen time
        if not isinstance(screen_time_minutes, int) or screen_time_minutes < 0:
            return jsonify({"error": "screen_time_minutes must be a non-negative integer"}), 400
            
        # Parse date (default to today)
        date_str = data.get("date")
        if date_str:
            try:
                log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        else:
            log_date = date.today()
            
        # Parse top apps (optional)
        top_apps = data.get("top_apps", [])
        top_apps_json = None
        if top_apps:
            # Validate top apps format
            if not isinstance(top_apps, list):
                return jsonify({"error": "top_apps must be a list"}), 400
                
            for app in top_apps:
                if not isinstance(app, dict) or "name" not in app or "minutes" not in app:
                    return jsonify({"error": "Each app must have 'name' and 'minutes' fields"}), 400
                if not isinstance(app["minutes"], int) or app["minutes"] < 0:
                    return jsonify({"error": "App minutes must be non-negative integers"}), 400
                    
            top_apps_json = json.dumps(top_apps)
            
        # Check if entry already exists for this date
        existing_log = ScreenTimeLog.query.filter_by(
            user_id=current_user.id,
            date=log_date
        ).first()
        
        if existing_log:
            # Update existing entry
            existing_log.screen_time_minutes = screen_time_minutes
            existing_log.top_apps = top_apps_json
            existing_log.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                "message": "Screen time updated successfully",
                "data": existing_log.to_dict()
            }), 200
        else:
            # Create new entry
            new_log = ScreenTimeLog(
                user_id=current_user.id,
                date=log_date,
                screen_time_minutes=screen_time_minutes,
                top_apps=top_apps_json
            )
            
            db.session.add(new_log)
            db.session.commit()
            
            return jsonify({
                "message": "Screen time logged successfully",
                "data": new_log.to_dict()
            }), 201
            
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to log screen time: {str(e)}"}), 500


@screentime_bp.route("/log", methods=["GET"])
def log_screen_time_info():
    """Informational GET for /log — use POST to create/update a log"""
    return jsonify({
        "message": "Use POST to create or update a screen time log at this endpoint.",
        "example": {
            "date": "2024-01-15",
            "screen_time_minutes": 180,
            "top_apps": [{"name": "Instagram", "minutes": 60}]
        }
    }), 200


@screentime_bp.route("/", methods=["GET"])  # explicit root so /api/screentime works
def screentime_index():
    """Base route for screentime blueprint"""
    return jsonify({
        "message": "Screen time blueprint",
        "endpoints": ["/log (POST)", "/today (GET)", "/history (GET)", "/stats (GET)", "/delete/<YYYY-MM-DD> (DELETE)"]
    }), 200


@screentime_bp.route("/today", methods=["GET"])
@login_required
def get_today_screen_time():
    """Get today's screen time log"""
    try:
        today = date.today()
        today_log = ScreenTimeLog.query.filter_by(
            user_id=current_user.id,
            date=today
        ).first()
        
        if not today_log:
            return jsonify({
                "data": None,
                "message": "No screen time logged for today"
            }), 200
            
        return jsonify({"data": today_log.to_dict()}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch today's screen time: {str(e)}"}), 500


@screentime_bp.route("/history", methods=["GET"])
@login_required
def get_screen_time_history():
    """
    Get screen time history
    Query params:
    - days: number of days to look back (default: 7)
    - start_date: start date in YYYY-MM-DD format
    - end_date: end date in YYYY-MM-DD format
    """
    try:
        # Get query parameters
        days = request.args.get("days", 7, type=int)
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        
        # Calculate date range
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        else:
            end_date = date.today()
            start_date = end_date - timedelta(days=days-1)
            
        # Query screen time logs
        logs = ScreenTimeLog.query.filter(
            ScreenTimeLog.user_id == current_user.id,
            ScreenTimeLog.date >= start_date,
            ScreenTimeLog.date <= end_date
        ).order_by(ScreenTimeLog.date.desc()).all()
        
        return jsonify({
            "data": [log.to_dict() for log in logs],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_entries": len(logs)
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch screen time history: {str(e)}"}), 500


@screentime_bp.route("/stats", methods=["GET"])
@login_required
def get_screen_time_stats():
    """
    Get screen time statistics
    Query params:
    - period: '7d', '30d', '90d' (default: '7d')
    """
    try:
        period = request.args.get("period", "7d")
        
        # Calculate date range
        end_date = date.today()
        if period == "7d":
            start_date = end_date - timedelta(days=6)
        elif period == "30d":
            start_date = end_date - timedelta(days=29)
        elif period == "90d":
            start_date = end_date - timedelta(days=89)
        else:
            return jsonify({"error": "Invalid period. Use '7d', '30d', or '90d'"}), 400
            
        # Query screen time logs
        logs = ScreenTimeLog.query.filter(
            ScreenTimeLog.user_id == current_user.id,
            ScreenTimeLog.date >= start_date,
            ScreenTimeLog.date <= end_date
        ).all()
        
        if not logs:
            return jsonify({
                "period": period,
                "total_days": 0,
                "total_screen_time": 0,
                "average_screen_time": 0,
                "top_apps": [],
                "daily_data": []
            }), 200
            
        # Calculate statistics
        total_screen_time = sum(log.screen_time_minutes for log in logs)
        total_days = len(logs)
        average_screen_time = total_screen_time // total_days if total_days > 0 else 0
        
        # Aggregate top apps
        app_usage = {}
        for log in logs:
            if log.top_apps:
                try:
                    apps = json.loads(log.top_apps)
                    for app in apps:
                        app_name = app["name"]
                        app_minutes = app["minutes"]
                        if app_name in app_usage:
                            app_usage[app_name] += app_minutes
                        else:
                            app_usage[app_name] = app_minutes
                except:
                    continue
                    
        # Sort top apps
        top_apps = [
            {"name": name, "minutes": minutes}
            for name, minutes in sorted(app_usage.items(), key=lambda x: x[1], reverse=True)
        ][:5]  # Top 5 apps
        
        # Daily data for charts
        daily_data = [
            {
                "date": log.date.isoformat(),
                "screen_time_minutes": log.screen_time_minutes
            }
            for log in sorted(logs, key=lambda x: x.date)
        ]
        
        return jsonify({
            "period": period,
            "total_days": total_days,
            "total_screen_time": total_screen_time,
            "average_screen_time": average_screen_time,
            "top_apps": top_apps,
            "daily_data": daily_data
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch screen time stats: {str(e)}"}), 500


@screentime_bp.route("/delete/<date_str>", methods=["DELETE"])
@login_required
def delete_screen_time_log(date_str):
    """Delete a screen time log for a specific date"""
    try:
        # Parse date
        try:
            log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
            
        # Find and delete log
        log = ScreenTimeLog.query.filter_by(
            user_id=current_user.id,
            date=log_date
        ).first()
        
        if not log:
            return jsonify({"error": "No screen time log found for this date"}), 404
            
        db.session.delete(log)
        db.session.commit()
        
        return jsonify({"message": "Screen time log deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete screen time log: {str(e)}"}), 500