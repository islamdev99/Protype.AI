
import os
import time
import json
import datetime
import re
import pytz
import requests
import torch
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta

class TemporalAwareness:
    def __init__(self):
        self.time_data_file = "temporal_data.json"
        self.load_time_data()
        self.current_timezone = pytz.timezone('UTC')
        self.relative_time_patterns = {
            'yesterday': datetime.timedelta(days=1),
            'last week': datetime.timedelta(weeks=1),
            'last month': relativedelta(months=1),
            'last year': relativedelta(years=1),
            'two days ago': datetime.timedelta(days=2),
            'two weeks ago': datetime.timedelta(weeks=2),
            'two months ago': relativedelta(months=2),
            'two years ago': relativedelta(years=2),
            'a week ago': datetime.timedelta(weeks=1),
            'a month ago': relativedelta(months=1),
            'a year ago': relativedelta(years=1),
        }
        
    def load_time_data(self):
        """Load temporal data from file"""
        try:
            with open(self.time_data_file, 'r') as f:
                self.time_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.time_data = {
                "last_updated": time.time(),
                "temporal_facts": [],
                "time_dependent_knowledge": {},
                "events": []
            }
            self.save_time_data()
            
    def save_time_data(self):
        """Save temporal data to file"""
        try:
            with open(self.time_data_file, 'w') as f:
                json.dump(self.time_data, f, indent=2)
        except Exception as e:
            print(f"Error saving temporal data: {e}")
    
    def set_timezone(self, timezone_str):
        """Set the current timezone"""
        try:
            self.current_timezone = pytz.timezone(timezone_str)
            return True
        except:
            print(f"Invalid timezone: {timezone_str}")
            return False
    
    def get_current_time(self, timezone=None):
        """Get the current time in the specified timezone"""
        tz = timezone if timezone else self.current_timezone
        return datetime.datetime.now(tz)
    
    def parse_time_expression(self, time_expr):
        """Parse natural language time expressions"""
        try:
            # Handle relative time expressions
            time_expr = time_expr.lower()
            now = datetime.datetime.now(self.current_timezone)
            
            # Check for relative time patterns
            for pattern, delta in self.relative_time_patterns.items():
                if pattern in time_expr:
                    return now - delta
            
            # Check for "X days/weeks/months/years ago"
            ago_match = re.search(r'(\d+)\s+(day|week|month|year)s?\s+ago', time_expr)
            if ago_match:
                num = int(ago_match.group(1))
                unit = ago_match.group(2)
                
                if unit == 'day':
                    return now - datetime.timedelta(days=num)
                elif unit == 'week':
                    return now - datetime.timedelta(weeks=num)
                elif unit == 'month':
                    return now - relativedelta(months=num)
                elif unit == 'year':
                    return now - relativedelta(years=num)
            
            # Try to parse as an absolute date
            return parse_date(time_expr)
            
        except Exception as e:
            print(f"Error parsing time expression: {e}")
            return None
    
    def add_temporal_fact(self, fact, timestamp=None, expiration=None, confidence=0.9):
        """Add a time-dependent fact"""
        if timestamp is None:
            timestamp = time.time()
            
        fact_entry = {
            "fact": fact,
            "added_at": timestamp,
            "confidence": confidence
        }
        
        if expiration:
            fact_entry["expires_at"] = expiration
            
        self.time_data["temporal_facts"].append(fact_entry)
        self.save_time_data()
        
        return True
    
    def get_valid_temporal_facts(self):
        """Get all currently valid temporal facts"""
        current_time = time.time()
        valid_facts = []
        
        for fact in self.time_data["temporal_facts"]:
            # Skip if expired
            if "expires_at" in fact and fact["expires_at"] < current_time:
                continue
                
            valid_facts.append(fact)
            
        return valid_facts
    
    def add_event(self, name, date, description=None, recurring=None):
        """Add a temporal event"""
        event = {
            "name": name,
            "date": date.isoformat() if isinstance(date, datetime.datetime) else date,
            "added_at": time.time()
        }
        
        if description:
            event["description"] = description
            
        if recurring:
            event["recurring"] = recurring
            
        self.time_data["events"].append(event)
        self.save_time_data()
        
        return True
    
    def get_upcoming_events(self, days=30):
        """Get events occurring within the specified number of days"""
        try:
            now = datetime.datetime.now(self.current_timezone)
            end_date = now + datetime.timedelta(days=days)
            
            upcoming = []
            
            for event in self.time_data["events"]:
                event_date = parse_date(event["date"])
                
                # Check if event is in the future and within the specified range
                if now <= event_date <= end_date:
                    upcoming.append({
                        "name": event["name"],
                        "date": event["date"],
                        "description": event.get("description", ""),
                        "days_from_now": (event_date - now).days
                    })
                
                # Handle recurring events
                if "recurring" in event:
                    recurring = event["recurring"]
                    base_date = parse_date(event["date"])
                    
                    if recurring == "daily":
                        increment = datetime.timedelta(days=1)
                    elif recurring == "weekly":
                        increment = datetime.timedelta(weeks=1)
                    elif recurring == "monthly":
                        increment = relativedelta(months=1)
                    elif recurring == "yearly":
                        increment = relativedelta(years=1)
                    else:
                        continue
                    
                    # Generate recurring instances within the date range
                    current_date = base_date
                    while current_date <= end_date:
                        if now <= current_date <= end_date:
                            upcoming.append({
                                "name": event["name"],
                                "date": current_date.isoformat(),
                                "description": event.get("description", ""),
                                "days_from_now": (current_date - now).days,
                                "recurring": recurring
                            })
                        
                        current_date += increment
            
            # Sort by date
            upcoming.sort(key=lambda x: parse_date(x["date"]))
            
            return upcoming
            
        except Exception as e:
            print(f"Error getting upcoming events: {e}")
            return []
    
    def add_time_dependent_knowledge(self, topic, content, valid_from=None, valid_until=None):
        """Add knowledge that is time-dependent"""
        if valid_from is None:
            valid_from = time.time()
            
        knowledge_entry = {
            "content": content,
            "added_at": time.time(),
            "valid_from": valid_from
        }
        
        if valid_until:
            knowledge_entry["valid_until"] = valid_until
            
        if topic not in self.time_data["time_dependent_knowledge"]:
            self.time_data["time_dependent_knowledge"][topic] = []
            
        self.time_data["time_dependent_knowledge"][topic].append(knowledge_entry)
        self.save_time_data()
        
        return True
    
    def get_current_knowledge(self, topic):
        """Get the currently valid knowledge for a topic"""
        if topic not in self.time_data["time_dependent_knowledge"]:
            return None
            
        current_time = time.time()
        valid_entries = []
        
        for entry in self.time_data["time_dependent_knowledge"][topic]:
            # Skip if not yet valid
            if entry["valid_from"] > current_time:
                continue
                
            # Skip if expired
            if "valid_until" in entry and entry["valid_until"] < current_time:
                continue
                
            valid_entries.append(entry)
            
        if not valid_entries:
            return None
            
        # Sort by added_at (newest first) and return the most recent
        valid_entries.sort(key=lambda x: x["added_at"], reverse=True)
        return valid_entries[0]["content"]
    
    def update_time_dependent_data(self):
        """Update time-dependent data (should be called periodically)"""
        try:
            # Only update if last update was more than a day ago
            if time.time() - self.time_data["last_updated"] < 86400:  # 24 hours
                return
                
            # Fetch current date/time
            current_time = time.time()
            self.time_data["last_updated"] = current_time
            
            # Clean up expired facts
            self.time_data["temporal_facts"] = [
                fact for fact in self.time_data["temporal_facts"]
                if "expires_at" not in fact or fact["expires_at"] > current_time
            ]
            
            # Update confidence of older facts (decay factor)
            for fact in self.time_data["temporal_facts"]:
                age_days = (current_time - fact["added_at"]) / 86400
                if age_days > 30:  # Older than 30 days
                    # Apply decay function
                    fact["confidence"] = fact["confidence"] * 0.99 ** (age_days - 30)
                    
                    # Remove if confidence too low
                    if fact["confidence"] < 0.4:
                        self.time_data["temporal_facts"].remove(fact)
            
            self.save_time_data()
            return True
            
        except Exception as e:
            print(f"Error updating time-dependent data: {e}")
            return False
    
    def process_temporal_query(self, query):
        """Process a query with temporal aspects"""
        time_words = ["yesterday", "today", "tomorrow", "last week", "next week", 
                     "last month", "next month", "last year", "next year",
                     "ago", "since", "before", "after", "during", "between"]
                     
        has_temporal_aspect = any(word in query.lower() for word in time_words)
        
        if not has_temporal_aspect:
            return None  # No temporal processing needed
            
        try:
            # Extract time expression from query
            time_expr = None
            for word in time_words:
                if word in query.lower():
                    # Find the time expression containing this word
                    pattern = r'((?:\w+\s+){0,3}' + word + r'(?:\s+\w+){0,3})'
                    match = re.search(pattern, query, re.IGNORECASE)
                    if match:
                        time_expr = match.group(1)
                        break
            
            if not time_expr:
                return None
                
            # Parse the time expression
            parsed_time = self.parse_time_expression(time_expr)
            
            if not parsed_time:
                return None
                
            # Return temporal context
            return {
                "time_expression": time_expr,
                "parsed_time": parsed_time.isoformat(),
                "relative_to_now": self.describe_time_difference(parsed_time)
            }
            
        except Exception as e:
            print(f"Error processing temporal query: {e}")
            return None
    
    def describe_time_difference(self, dt):
        """Describe the difference between a datetime and now"""
        now = datetime.datetime.now(self.current_timezone)
        
        # Add timezone if missing
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self.current_timezone)
            
        diff = now - dt
        
        # Future
        if diff.total_seconds() < 0:
            diff = abs(diff)
            if diff.days == 0:
                hours = diff.seconds // 3600
                if hours == 0:
                    minutes = diff.seconds // 60
                    return f"{minutes} minutes from now"
                return f"{hours} hours from now"
            elif diff.days == 1:
                return "tomorrow"
            elif diff.days < 7:
                return f"{diff.days} days from now"
            elif diff.days < 30:
                weeks = diff.days // 7
                return f"{weeks} weeks from now"
            elif diff.days < 365:
                months = diff.days // 30
                return f"{months} months from now"
            else:
                years = diff.days // 365
                return f"{years} years from now"
        # Past
        else:
            if diff.days == 0:
                hours = diff.seconds // 3600
                if hours == 0:
                    minutes = diff.seconds // 60
                    return f"{minutes} minutes ago"
                return f"{hours} hours ago"
            elif diff.days == 1:
                return "yesterday"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            elif diff.days < 30:
                weeks = diff.days // 7
                return f"{weeks} weeks ago"
            elif diff.days < 365:
                months = diff.days // 30
                return f"{months} months ago"
            else:
                years = diff.days // 365
                return f"{years} years ago"

# Create singleton instance
temporal_awareness = TemporalAwareness()
