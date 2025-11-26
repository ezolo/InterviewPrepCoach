"""
Application tracking service
"""
from typing import List, Dict, Optional
from datetime import datetime
from database.connection import execute_query

class ApplicationService:
    """Handle job application tracking"""
    
    @staticmethod
    def create_application(user_id: int, company_name: str, job_title: str,
                          job_url: Optional[str] = None,
                          location: Optional[str] = None,
                          jd_id: Optional[int] = None,
                          status: str = 'saved',
                          notes: Optional[str] = None,
                          applied_date: Optional = None,
                          interview_date: Optional = None,
                          salary_offered: Optional[float] = None) -> Optional[int]:
        """Create application record"""
        try:
            from database.connection import get_connection
            
            print(f"[DEBUG] create_application called: user_id={user_id}, company={company_name}, title={job_title}")
            print(f"[DEBUG] Dates: applied_date={applied_date}, interview_date={interview_date}, salary={salary_offered}")
            
            query = """
                INSERT INTO applications 
                (user_id, company, company_name, job_title, position, job_url, location, jd_id, status, notes, 
                 applied_date, interview_date, salary_offered, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            
            # Both 'company' and 'company_name' are required - use company_name for both
            # Also set position to job_title for consistency
            params = (user_id, company_name, company_name, job_title, job_title, job_url, location, jd_id, status, notes,
                     applied_date, interview_date, salary_offered)
            
            print(f"[DEBUG] Executing query with {len(params)} parameters")
            
            # Use direct connection to get lastrowid properly
            conn = None
            cursor = None
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                application_id = cursor.lastrowid
                
                # Sync application_id column with id for code compatibility
                if application_id:
                    cursor.execute(
                        "UPDATE applications SET application_id = id WHERE id = %s",
                        (application_id,)
                    )
                    conn.commit()
                
                cursor.close()
                conn.close()
                
                print(f"[DEBUG] Application created successfully with ID: {application_id}")
                return application_id if application_id and application_id > 0 else None
            except Exception as db_error:
                if conn:
                    conn.rollback()
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
                raise db_error
                
        except Exception as e:
            print(f"[ERROR] Error creating application: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_applications(user_id: int, status: Optional[str] = None) -> List[Dict]:
        """Get user's applications, optionally filtered by status"""
        if status:
            query = """
            SELECT * FROM applications 
            WHERE user_id = %s AND status = %s
            ORDER BY created_at DESC
            """
            return execute_query(query, (user_id, status), fetch_all=True) or []
        else:
            query = """
            SELECT * FROM applications 
            WHERE user_id = %s 
            ORDER BY created_at DESC
            """
            return execute_query(query, (user_id,), fetch_all=True) or []
    
    @staticmethod
    def get_application_by_id(application_id: int) -> Optional[Dict]:
        """Get a specific application"""
        query = "SELECT * FROM applications WHERE application_id = %s"
        return execute_query(query, (application_id,), fetch_one=True)
    
    @staticmethod
    def update_status(application_id: int, status: str) -> bool:
        """Update application status"""
        try:
            query = """
                UPDATE applications 
                SET status = %s, updated_at = NOW()
                WHERE application_id = %s
            """
            execute_query(query, (status, application_id), commit=True)
            return True
        except Exception as e:
            print(f"Error updating application status: {e}")
            return False
    
    @staticmethod
    def update_application(application_id: int, **kwargs) -> bool:
        """Update application fields"""
        try:
            # Build dynamic update query
            allowed_fields = ['company', 'company_name', 'job_title', 'position', 'job_url', 'location', 
                            'status', 'notes', 'applied_date', 'interview_date', 
                            'follow_up_date', 'salary_offered']
            
            updates = []
            values = []
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    updates.append(f"{field} = %s")
                    values.append(value)
            
            # If company_name is updated, also update company (they should match)
            if 'company_name' in kwargs and 'company' not in kwargs:
                updates.append("company = %s")
                values.append(kwargs['company_name'])
            
            # If job_title is updated, also update position (they should match)
            if 'job_title' in kwargs and 'position' not in kwargs:
                updates.append("position = %s")
                values.append(kwargs['job_title'])
            
            if not updates:
                return False
            
            values.append(application_id)
            query = f"UPDATE applications SET {', '.join(updates)}, updated_at = NOW() WHERE application_id = %s"
            
            execute_query(query, tuple(values), commit=True)
            return True
        except Exception as e:
            print(f"Error updating application: {e}")
            return False
    
    @staticmethod
    def delete_application(application_id: int) -> bool:
        """Delete an application"""
        try:
            query = "DELETE FROM applications WHERE application_id = %s"
            execute_query(query, (application_id,), commit=True)
            return True
        except Exception as e:
            print(f"Error deleting application: {e}")
            return False
    
    @staticmethod
    def create_reminder(application_id: int, reminder_date: str,
                       reminder_type: str, message: str) -> Optional[int]:
        """Create reminder for an application"""
        try:
            query = """
                INSERT INTO reminders 
                (application_id, reminder_date, reminder_type, message, is_completed, created_at)
                VALUES (%s, %s, %s, %s, FALSE, NOW())
            """
            reminder_id = execute_query(
                query,
                (application_id, reminder_date, reminder_type, message),
                commit=True
            )
            return reminder_id
        except Exception as e:
            print(f"Error creating reminder: {e}")
            return None
    
    @staticmethod
    def get_reminders(user_id: int, include_completed: bool = False) -> List[Dict]:
        """Get upcoming reminders"""
        if include_completed:
            query = """
            SELECT r.*, a.company_name, a.job_title 
            FROM reminders r
            JOIN applications a ON r.application_id = a.application_id
            WHERE a.user_id = %s
            ORDER BY r.reminder_date ASC
            """
        else:
            query = """
            SELECT r.*, a.company_name, a.job_title 
            FROM reminders r
            JOIN applications a ON r.application_id = a.application_id
            WHERE a.user_id = %s AND r.is_completed = FALSE
            ORDER BY r.reminder_date ASC
            """
        return execute_query(query, (user_id,), fetch_all=True) or []
    
    @staticmethod
    def complete_reminder(reminder_id: int) -> bool:
        """Mark a reminder as completed"""
        try:
            query = """
                UPDATE reminders 
                SET is_completed = TRUE, sent_at = NOW()
                WHERE reminder_id = %s
            """
            execute_query(query, (reminder_id,), commit=True)
            return True
        except Exception as e:
            print(f"Error completing reminder: {e}")
            return False
    
    @staticmethod
    def get_application_stats(user_id: int) -> Dict:
        """Get application statistics for a user"""
        query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status IN ('interview', 'final_round', 'offer') THEN 1 ELSE 0 END) as interviews,
            SUM(CASE WHEN status = 'offer' THEN 1 ELSE 0 END) as offers
        FROM applications 
        WHERE user_id = %s
        """
        result = execute_query(query, (user_id,), fetch_one=True)
        
        if result and result.get('total', 0):
            total = result.get('total', 0) or 0
            interviews = result.get('interviews', 0) or 0
            interview_rate = round((interviews / total * 100) if total > 0 else 0, 1)
            
            return {
                'total': total,
                'interviews': interviews,
                'offers': result.get('offers', 0) or 0,
                'interview_rate': interview_rate
            }
        
        return {'total': 0, 'interviews': 0, 'offers': 0, 'interview_rate': 0}
    
    @staticmethod
    def get_stats_by_status(user_id: int) -> Dict[str, int]:
        """Get count of applications by status"""
        query = """
        SELECT status, COUNT(*) as count
        FROM applications
        WHERE user_id = %s
        GROUP BY status
        """
        results = execute_query(query, (user_id,), fetch_all=True) or []
        
        stats = {}
        for row in results:
            stats[row['status']] = row['count']
        
        return stats
