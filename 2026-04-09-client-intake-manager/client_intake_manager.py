#!/usr/bin/env python3
"""
Client Intake & Onboarding Manager
Helps Victor manage new client inquiries efficiently for his sports analytics business.
Reduces context-switching by providing structured workflows for different client types.
"""

import sqlite3
import argparse
import sys
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
import csv
from pathlib import Path
import textwrap

# Database schema
DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    client_type TEXT CHECK(client_type IN ('coach', 'analyst', 'broadcaster', 'school', 'agent', 'other')),
    source TEXT CHECK(source IN ('referral', 'website', 'social', 'conference', 'cold', 'other')),
    status TEXT CHECK(status IN ('new', 'contacted', 'discovery-call', 'proposal-sent', 'onboarded', 'archived')),
    initial_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    interaction_type TEXT CHECK(interaction_type IN ('email', 'call', 'meeting', 'note')),
    notes TEXT,
    scheduled_time TIMESTAMP,
    completed_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    due_date TIMESTAMP,
    completed INTEGER DEFAULT 0,
    priority INTEGER CHECK(priority BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS briefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    content TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
);
"""

class ClientIntakeManager:
    def __init__(self, db_path: str = "client_intake.db"):
        """Initialize the database connection."""
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database with schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(DB_SCHEMA)
            conn.commit()
    
    def add_client(self, name: str, email: str = "", phone: str = "", 
                   client_type: str = "other", source: str = "other", 
                   initial_notes: str = "") -> int:
        """Add a new client inquiry."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clients (name, email, phone, client_type, source, status, initial_notes)
                VALUES (?, ?, ?, ?, ?, 'new', ?)
            """, (name, email, phone, client_type, source, initial_notes))
            client_id = cursor.lastrowid
            conn.commit()
        
        print(f"✅ Added client #{client_id}: {name}")
        return client_id
    
    def update_status(self, client_id: int, status: str, notes: str = ""):
        """Update client status."""
        valid_statuses = ['new', 'contacted', 'discovery-call', 'proposal-sent', 'onboarded', 'archived']
        if status not in valid_statuses:
            print(f"❌ Invalid status. Must be one of: {', '.join(valid_statuses)}")
            return
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE clients 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, client_id))
            
            if notes:
                conn.execute("""
                    INSERT INTO interactions (client_id, interaction_type, notes)
                    VALUES (?, 'note', ?)
                """, (client_id, f"Status changed to {status}: {notes}"))
            
            conn.commit()
        
        print(f"✅ Updated client #{client_id} status to '{status}'")
    
    def schedule_interaction(self, client_id: int, interaction_type: str, 
                            scheduled_time: str, notes: str = ""):
        """Schedule an interaction with a client."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO interactions (client_id, interaction_type, notes, scheduled_time)
                VALUES (?, ?, ?, ?)
            """, (client_id, interaction_type, notes, scheduled_time))
            conn.commit()
        
        print(f"✅ Scheduled {interaction_type} for client #{client_id} at {scheduled_time}")
    
    def add_task(self, client_id: int, description: str, due_date: str = None, 
                 priority: int = 3):
        """Add a follow-up task for a client."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO tasks (client_id, description, due_date, priority)
                VALUES (?, ?, ?, ?)
            """, (client_id, description, due_date, priority))
            conn.commit()
        
        print(f"✅ Added task for client #{client_id}: {description}")
    
    def generate_brief(self, client_id: int, output_dir: str = "./briefs") -> str:
        """Generate a client brief in markdown format."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            client = conn.execute("""
                SELECT * FROM clients WHERE id = ?
            """, (client_id,)).fetchone()
            
            if not client:
                print(f"❌ Client #{client_id} not found")
                return ""
            
            interactions = conn.execute("""
                SELECT * FROM interactions 
                WHERE client_id = ? 
                ORDER BY created_at
            """, (client_id,)).fetchall()
            
            tasks = conn.execute("""
                SELECT * FROM tasks 
                WHERE client_id = ? AND completed = 0
                ORDER BY priority, due_date
            """, (client_id,)).fetchall()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate brief content
        brief = f"""# Client Brief: {client['name']}

## 📋 Basic Information
- **Client ID:** #{client['id']}
- **Type:** {client['client_type'].title()}
- **Source:** {client['source'].title()}
- **Status:** {client['status'].title().replace('-', ' ')}
- **Created:** {client['created_at']}
- **Last Updated:** {client['updated_at']}

## 📞 Contact Information
- **Email:** {client['email'] or 'Not provided'}
- **Phone:** {client['phone'] or 'Not provided'}

## 📝 Initial Notes
{client['initial_notes'] or 'No initial notes provided.'}

## 📊 Status Timeline
"""
        
        # Add interactions
        if interactions:
            for interaction in interactions:
                brief += f"- **{interaction['interaction_type'].title()}** ({interaction['created_at']}): {interaction['notes'] or 'No notes'}\n"
        else:
            brief += "No interactions recorded yet.\n"
        
        # Add pending tasks
        brief += "\n## ✅ Pending Tasks\n"
        if tasks:
            for task in tasks:
                priority_stars = "⭐" * task['priority']
                due_info = f" (Due: {task['due_date']})" if task['due_date'] else ""
                brief += f"- {priority_stars} {task['description']}{due_info}\n"
        else:
            brief += "No pending tasks.\n"
        
        # Add recommendations based on status
        brief += "\n## 🎯 Recommended Next Steps\n"
        status_actions = {
            'new': "Send welcome email and schedule discovery call.",
            'contacted': "Follow up within 48 hours if no response.",
            'discovery-call': "Prepare for discovery call and send calendar invite.",
            'proposal-sent': "Follow up on proposal within 3-5 business days.",
            'onboarded': "Schedule kickoff meeting and set up project workspace.",
            'archived': "Consider re-engagement if conditions change."
        }
        brief += f"- {status_actions.get(client['status'], 'Review client status and determine next actions.')}\n"
        
        # Save to file
        filename = f"client_{client_id}_{client['name'].replace(' ', '_').lower()}.md"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(brief)
        
        print(f"✅ Generated brief for client #{client_id}: {filepath}")
        return filepath
    
    def search_clients(self, client_type: str = None, status: str = None, 
                       source: str = None, limit: int = 50) -> List[Dict]:
        """Search for clients with optional filters."""
        query = "SELECT * FROM clients WHERE 1=1"
        params = []
        
        if client_type:
            query += " AND client_type = ?"
            params.append(client_type)
        if status:
            query += " AND status = ?"
            params.append(status)
        if source:
            query += " AND source = ?"
            params.append(source)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_dashboard(self) -> Dict[str, Any]:
        """Get dashboard metrics."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Status counts
            status_counts = conn.execute("""
                SELECT status, COUNT(*) as count 
                FROM clients 
                GROUP BY status 
                ORDER BY 
                    CASE status 
                        WHEN 'new' THEN 1
                        WHEN 'contacted' THEN 2
                        WHEN 'discovery-call' THEN 3
                        WHEN 'proposal-sent' THEN 4
                        WHEN 'onboarded' THEN 5
                        WHEN 'archived' THEN 6
                        ELSE 7
                    END
            """).fetchall()
            
            # Type counts
            type_counts = conn.execute("""
                SELECT client_type, COUNT(*) as count 
                FROM clients 
                GROUP BY client_type 
                ORDER BY count DESC
            """).fetchall()
            
            # Recent activity
            recent_clients = conn.execute("""
                SELECT id, name, status, created_at 
                FROM clients 
                ORDER BY created_at DESC 
                LIMIT 5
            """).fetchall()
            
            # Upcoming tasks
            upcoming_tasks = conn.execute("""
                SELECT t.id, c.name, t.description, t.due_date, t.priority
                FROM tasks t
                JOIN clients c ON t.client_id = c.id
                WHERE t.completed = 0 AND t.due_date IS NOT NULL
                ORDER BY t.due_date, t.priority
                LIMIT 10
            """).fetchall()
        
        return {
            'status_counts': [dict(row) for row in status_counts],
            'type_counts': [dict(row) for row in type_counts],
            'recent_clients': [dict(row) for row in recent_clients],
            'upcoming_tasks': [dict(row) for row in upcoming_tasks]
        }
    
    def export_to_csv(self, output_file: str = "client_export.csv"):
        """Export all client data to CSV."""
        clients = self.search_clients(limit=1000)
        
        if not clients:
            print("❌ No clients to export")
            return
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=clients[0].keys())
            writer.writeheader()
            writer.writerows(clients)
        
        print(f"✅ Exported {len(clients)} clients to {output_file}")

def print_dashboard(dashboard: Dict[str, Any]):
    """Print dashboard in a formatted way."""
    print("\n" + "="*60)
    print("📊 CLIENT INTAKE DASHBOARD")
    print("="*60)
    
    # Status summary
    print("\n📈 Pipeline Status:")
    for item in dashboard['status_counts']:
        emoji = {
            'new': '🆕',
            'contacted': '📞',
            'discovery-call': '📅',
            'proposal-sent': '📄',
            'onboarded': '✅',
            'archived': '📁'
        }.get(item['status'], '•')
        print(f"  {emoji} {item['status'].title().replace('-', ' ')}: {item['count']}")
    
    # Client types
    print("\n👥 Client Types:")
    for item in dashboard['type_counts']:
        print(f"  • {item['client_type'].title()}: {item['count']}")
    
    # Recent clients
    print("\n🆕 Recent Inquiries:")
    for client in dashboard['recent_clients']:
        print(f"  #{client['id']}: {client['name']} ({client['status']}) - {client['created_at'][:10]}")
    
    # Upcoming tasks
    if dashboard['upcoming_tasks']:
        print("\n✅ Upcoming Tasks:")
        for task in dashboard['upcoming_tasks']:
            priority_stars = "⭐" * task['priority']
            due_date = f" ({task['due_date'][:10]})" if task['due_date'] else ""
            print(f"  {priority_stars} {task['name']}: {task['description']}{due_date}")
    
    print("\n" + "="*60)

def main():
    parser = argparse.ArgumentParser(
        description="Client Intake & Onboarding Manager for Victor's sports analytics business",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              %(prog)s add --name "John Doe" --type coach --source referral --email john@example.com
              %(prog)s update-status 123 --status discovery-call --notes "Scheduled for Friday"
              %(prog)s schedule 123 --type call --time "2026-04-12 15:00" --notes "Discovery call"
              %(prog)s generate-brief 123 --output ./briefs/
              %(prog)s dashboard
              %(prog)s search --type coach --status new
              %(prog)s export --output clients.csv
        """)
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Add client command
    add_parser = subparsers.add_parser('add', help='Add a new client inquiry')
    add_parser.add_argument('--name', required=True, help='Client name')
    add_parser.add_argument('--email', help='Client email')
    add_parser.add_argument('--phone', help='Client phone')
    add_parser.add_argument('--type', choices=['coach', 'analyst', 'broadcaster', 'school', 'agent', 'other'], 
                           default='other', help='Client type')
    add_parser.add_argument('--source', choices=['referral', 'website', 'social', 'conference', 'cold', 'other'],
                           default='other', help='Inquiry source')
    add_parser.add_argument('--notes', help='Initial notes')
    
    # Update status command
    update_parser = subparsers.add_parser('update-status', help='Update client status')
    update_parser.add_argument('client_id', type=int, help='Client ID')
    update_parser.add_argument('--status', required=True, 
                               choices=['new', 'contacted', 'discovery-call', 'proposal-sent', 'onboarded', 'archived'],
                               help='New status')
    update_parser.add_argument('--notes', help='Status change notes')
    
    # Schedule command
    schedule_parser = subparsers.add_parser('schedule', help='Schedule interaction')
    schedule_parser.add_argument('client_id', type=int, help='Client ID')
    schedule_parser.add_argument('--type', required=True, 
                                 choices=['email', 'call', 'meeting', 'note'],
                                 help='Interaction type')
    schedule_parser.add_argument('--time', required=True, help='Scheduled time (YYYY-MM-DD HH:MM)')
    schedule_parser.add_argument('--notes', help='Interaction notes')
    
    # Generate brief command
    brief_parser = subparsers.add_parser('generate-brief', help='Generate client brief')
    brief_parser.add_argument('client_id', type=int, help='Client ID')
    brief_parser.add_argument('--output', default='./briefs', help='Output directory')
    
    # Dashboard command
    subparsers.add_parser('dashboard', help='Show dashboard')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search clients')
    search_parser.add_argument('--type', choices=['coach', 'analyst', 'broadcaster', 'school', 'agent', 'other'],
                              help='Filter by client type')
    search_parser.add_argument('--status', choices=['new', 'contacted', 'discovery-call', 'proposal-sent', 'onboarded', 'archived'],
                              help='Filter by status')
    search_parser.add_argument('--source', choices=['referral', 'website', 'social', 'conference', 'cold', 'other'],
                              help='Filter by source')
    search_parser.add_argument('--limit', type=int, default=20, help='Limit results')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export to CSV')
    export_parser.add_argument('--output', default='client_export.csv', help='Output file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = ClientIntakeManager()
    
    try:
        if args.command == 'add':
            client_id = manager.add_client(
                name=args.name,
                email=args.email or "",
                phone=args.phone or "",
                client_type=args.type,
                source=args.source,
                initial_notes=args.notes or ""
            )
            # Add initial task
            manager.add_task(
                client_id=client_id,
                description=f"Follow up with {args.name}",
                priority=3
            )
            
        elif args.command == 'update-status':
            manager.update_status(
                client_id=args.client_id,
                status=args.status,
                notes=args.notes or ""
            )
            
        elif args.command == 'schedule':
            manager.schedule_interaction(
                client_id=args.client_id,
                interaction_type=args.type,
                scheduled_time=args.time,
                notes=args.notes or ""
            )
            
        elif args.command == 'generate-brief':
            manager.generate_brief(
                client_id=args.client_id,
                output_dir=args.output
            )
            
        elif args.command == 'dashboard':
            dashboard = manager.get_dashboard()
            print_dashboard(dashboard)
            
        elif args.command == 'search':
            clients = manager.search_clients(
                client_type=args.type,
                status=args.status,
                source=args.source,
                limit=args.limit
            )
            
            if clients:
                print(f"\n🔍 Found {len(clients)} clients:")
                for client in clients:
                    print(f"\n  #{client['id']}: {client['name']}")
                    print(f"     Type: {client['client_type']}, Status: {client['status']}")
                    print(f"     Source: {client['source']}, Created: {client['created_at'][:10]}")
                    if client['email']:
                        print(f"     Email: {client['email']}")
            else:
                print("❌ No clients found matching criteria")
                
        elif args.command == 'export':
            manager.export_to_csv(args.output)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()