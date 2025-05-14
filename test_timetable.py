from timetable_generator import TimetableGenerator, Course, TimeSlot, Room
from datetime import datetime, timedelta
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

def create_time_slots():
    """Create time slots for a week."""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    time_slots = []
    
    for day in days:
        start_time = datetime.strptime('08:00', '%H:%M')
        for _ in range(8):  # 8 time slots per day
            end_time = start_time + timedelta(hours=1)
            time_slots.append(TimeSlot(day, start_time, end_time))
            start_time = end_time
    
    return time_slots

def create_rooms():
    """Create rooms for all departments except SMgs."""
    rooms = []
    
    # FCSE rooms
    for i in range(1, 4):
        rooms.append(Room(f'FCSE-LH{i}', 50, 'FCSE', 'LH'))
    rooms.append(Room('FCSE-MLH1', 100, 'FCSE', 'MLH'))
    
    # FEE rooms
    for i in range(4, 7):
        rooms.append(Room(f'FEE-LH{i}', 50, 'FEE', 'LH'))
    rooms.append(Room('FEE-MLH2', 100, 'FEE', 'MLH'))
    
    # FME rooms
    for i in range(1, 5):
        rooms.append(Room(f'FME-LH{i}', 50, 'FME', 'LH'))
    rooms.append(Room('FME-MLH1', 100, 'FME', 'MLH'))
    
    # FES rooms
    for i in range(1, 7):
        rooms.append(Room(f'FES-LH{i}', 50, 'FES', 'LH'))
    rooms.append(Room('FES-MLH1', 100, 'FES', 'MLH'))
    
    # FMCE rooms
    for i in range(1, 7):
        rooms.append(Room(f'FMCE-LH{i}', 50, 'FMCE', 'LH'))
    rooms.append(Room('FMCE-MLH1', 100, 'FMCE', 'MLH'))
    
    # DCve rooms
    for i in range(1, 4):
        rooms.append(Room(f'DCve-LH{i}', 50, 'DCve', 'LH'))
    rooms.append(Room('DCve-MLH1', 100, 'DCve', 'MLH'))

    # New Academic Block rooms (LH5-LH9)
    for i in range(5, 10):  # Changed from range(1, 7) to range(5, 10)
        rooms.append(Room(f'NAB-LH{i}', 50, 'NAB', 'LH'))
    for i in range(1, 3):
        rooms.append(Room(f'NAB-MLH{i}', 100, 'NAB', 'MLH'))
    
    return rooms

def load_courses_from_excel():
    """Load courses from the Excel file using the correct column names, and skip HM, HUM, Humanities, SMgs courses, and labs (courses ending with 'L')."""
    excel_path = r'D:\codes\GIKI Timetable\List of Offered Courses.xlsx'
    try:
        df = pd.read_excel(excel_path)
        print("\nFirst few rows of Excel file:")
        print(df.head())
        print("\nColumns in Excel file:")
        print(df.columns)
        
        courses = []
        print("\nProcessing courses...")
        for _, row in df.iterrows():
            department = str(row['Offered By']).strip().upper()
            course_code = str(row['Code']).strip().upper()
            
            # Skip labs (courses ending with 'L')
            if course_code.endswith('L'):
                print(f"SKIPPING LAB: {course_code} ({row['Course Title']})")
                continue
            
            # Map DMTE and DCHE to FMCE
            if department in ['DMTE', 'DCHE']:
                department = 'FMCE'
            # Skip HM, HUM, Humanities, and SMgs courses
            if department in ['HM', 'HUM', 'HUMANITIES', 'SMGS']:
                print(f"SKIPPING: {row['Code']} ({row['Course Title']}) offered by {row['Offered By']} (department: {department})")
                continue
                
            ch_str = str(row['CH'])
            if pd.isnull(row['CH']) or ch_str.lower() == 'nan':
                ch_main = 1
            elif '+' in ch_str:
                ch_main = sum(int(x) for x in ch_str.split('+') if x.isdigit())
            else:
                ch_main = int(ch_str)
            duration = 60  # Each session is 1 hour
            # Create a separate session for each credit hour
            for session_num in range(1, ch_main + 1):
                course = Course(
                    id=f"{row['Code']}-{session_num}",
                    name=f"{row['Course Title']} (Session {session_num})",
                    teacher=str(row['Course Instructor']),
                    student_group=str(row['Offered For']),
                    duration=duration,
                    department=department
                )
                courses.append(course)
        
        # Print summary of courses by department
        print("\nCourses by Department:")
        print("====================")
        dept_courses = {}
        for course in courses:
            if course.department not in dept_courses:
                dept_courses[course.department] = []
            dept_courses[course.department].append(course.id)
        
        for dept, course_list in dept_courses.items():
            print(f"\n{dept} Courses ({len(course_list)}):")
            for course_id in course_list:
                print(f"- {course_id}")
            
        return courses
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []

def plot_room_timetable(generator):
    # Build a DataFrame for plotting
    data = []
    for course in generator.courses:
        if course.id in generator.room_assignments:
            time_slot = generator.time_slots[generator.color_assignments[course.id]]
            room = generator.room_assignments[course.id]
            data.append({
                'Room': room,
                'Day': time_slot.day,
                'Start': time_slot.start_time.strftime('%H:%M'),
                'Course': course.name
            })
    import pandas as pd
    df = pd.DataFrame(data)
    # Pivot for heatmap: index=Room, columns=Day+Start, values=Course
    df['Slot'] = df['Day'] + ' ' + df['Start']
    timetable = df.pivot(index='Room', columns='Slot', values='Course')
    plt.figure(figsize=(18, len(timetable) * 0.5 + 4))
    sns.heatmap(timetable.isnull(), cbar=False, cmap='Blues', linewidths=0.5, linecolor='gray')
    for y in range(timetable.shape[0]):
        for x in range(timetable.shape[1]):
            val = timetable.iloc[y, x]
            if pd.notnull(val):
                plt.text(x + 0.5, y + 0.5, val, ha='center', va='center', fontsize=8)
    plt.title('Room Timetable')
    plt.xlabel('Time Slot')
    plt.ylabel('Room')
    plt.tight_layout()
    plt.show()

def plot_department_timetable(generator, department):
    """Plot timetable for a specific department."""
    print(f"\n{'='*50}")
    print(f"Timetable for {department}")
    print(f"{'='*50}")
    
    # Get all courses for this department
    dept_courses = [c for c in generator.courses if c.department.upper() == department.upper()]
    if not dept_courses:
        print(f"No courses found for department {department}")
        return
    
    # Get all rooms for this department
    dept_rooms = [r for r in generator.rooms if r.department.upper() == department.upper()]
    print(f"\nAvailable rooms for {department}:")
    for room in dept_rooms:
        print(f"- {room.id} (Capacity: {room.capacity})")
    
    # Get scheduled courses
    scheduled_courses = []
    unscheduled_courses = []
    for course in dept_courses:
        if course.id in generator.room_assignments:
            time_slot = generator.time_slots[generator.color_assignments[course.id]]
            room = generator.room_assignments[course.id]
            course_code = course.id.split('-')[0]
            scheduled_courses.append({
                'Course': course_code,
                'Teacher': course.teacher,
                'Group': course.student_group,
                'Day': time_slot.day,
                'Time': time_slot.start_time.strftime('%H:%M'),
                'Room': room
            })
        else:
            unscheduled_courses.append(course)
    
    # Print scheduled courses
    if scheduled_courses:
        print(f"\nScheduled courses ({len(scheduled_courses)}):")
        df_scheduled = pd.DataFrame(scheduled_courses)
        print(df_scheduled.to_string(index=False))
    else:
        print("\nNo courses scheduled for this department!")
    
    # Print unscheduled courses
    if unscheduled_courses:
        print(f"\nUnscheduled courses ({len(unscheduled_courses)}):")
        for course in unscheduled_courses:
            course_code = course.id.split('-')[0]
            print(f"- {course_code} (Teacher: {course.teacher}, Group: {course.student_group})")
    
    # Create a more readable timetable format
    if scheduled_courses:
        df = pd.DataFrame(scheduled_courses)
        
        # Create a pivot table with days as index and times as columns
        timetable = pd.pivot_table(
            df,
            values='Course',
            index=['Day', 'Room'],
            columns='Time',
            aggfunc=lambda x: ', '.join(x)
        )
        
        # Sort the index by day
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        timetable.index = pd.MultiIndex.from_arrays([
            pd.Categorical(timetable.index.get_level_values(0), categories=days_order),
            timetable.index.get_level_values(1)
        ])
        timetable = timetable.sort_index()
        
        # Display the timetable
        print("\nDepartment Timetable:")
        print("===================")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(timetable.to_string())
        
        # Reset display options
        pd.reset_option('display.max_columns')
        pd.reset_option('display.width')

def main():
    # Initialize the timetable generator
    generator = TimetableGenerator()
    
    # Add rooms
    rooms = create_rooms()
    for room in rooms:
        generator.add_room(room)
    
    # Add time slots
    time_slots = create_time_slots()
    for slot in time_slots:
        generator.add_time_slot(slot)
    
    # Load courses from Excel
    courses = load_courses_from_excel()
    if not courses:
        print("No courses loaded from Excel file. Using example courses.")
        # Fallback to example courses if Excel loading fails
        courses = [
            Course('CS101', 'Introduction to Programming', 'Dr. Smith', 'Group A', 60, 'FCSE'),
            Course('CS102', 'Data Structures', 'Dr. Smith', 'Group B', 60, 'FCSE'),
            Course('EE201', 'Circuit Analysis', 'Dr. Johnson', 'Group A', 60, 'FEE'),
            Course('EE202', 'Digital Electronics', 'Dr. Johnson', 'Group B', 60, 'FEE'),
            Course('ME301', 'Thermodynamics', 'Dr. Brown', 'Group A', 60, 'FME'),
            Course('ME302', 'Fluid Mechanics', 'Dr. Brown', 'Group B', 60, 'FME'),
            Course('ES401', 'Environmental Science', 'Dr. Wilson', 'Group A', 60, 'FES'),
            Course('ES402', 'Climate Change', 'Dr. Wilson', 'Group B', 60, 'FES')
        ]
    
    # Add courses to the generator
    for course in courses:
        generator.add_course(course)
    
    try:
        # Generate the timetable
        timetable = generator.generate_timetable()
        
        # Print and plot timetables for each department
        departments = ['FCSE', 'FEE', 'FME', 'FES', 'FMCE', 'DCve', 'NAB']
        for dept in departments:
            plot_department_timetable(generator, dept)
            
    except KeyError as e:
        # Handle the case where a course doesn't have a room assignment
        course_id = str(e).strip("'")
        print(f"\nError: Course {course_id} could not be assigned a room.")
        print("\nDebugging Information:")
        print("=====================")
        
        # Find the course details
        course = next((c for c in courses if c.id == course_id), None)
        if course:
            print(f"Course Details:")
            print(f"- Name: {course.name}")
            print(f"- Department: {course.department}")
            print(f"- Teacher: {course.teacher}")
            print(f"- Group: {course.student_group}")
            
            # Check available rooms for this department
            dept_rooms = [r for r in rooms if r.department == course.department]
            print(f"\nAvailable rooms in {course.department}:")
            for room in dept_rooms:
                print(f"- {room.id} (Capacity: {room.capacity})")
            
            # Check if any rooms are available in NAB
            nab_rooms = [r for r in rooms if r.department == 'NAB']
            print(f"\nAvailable NAB rooms:")
            for room in nab_rooms:
                print(f"- {room.id} (Capacity: {room.capacity})")
        
        print("\nSuggested Solutions:")
        print("1. Check if there are enough rooms in the department")
        print("2. Consider using NAB rooms for overflow")
        print("3. Check for scheduling conflicts with other courses")
        
        # Continue with the rest of the departments
        print("\nContinuing with other departments...")
        departments = ['FCSE', 'FEE', 'FME', 'FES', 'FMCE', 'DCve', 'NAB']
        for dept in departments:
            if dept != course.department:  # Skip the problematic department
                plot_department_timetable(generator, dept)

if __name__ == '__main__':
    main() 