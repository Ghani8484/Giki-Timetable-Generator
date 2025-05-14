from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import networkx as nx
from datetime import datetime, timedelta

@dataclass
class TimeSlot:
    day: str
    start_time: datetime
    end_time: datetime

@dataclass
class Course:
    id: str
    name: str
    teacher: str
    student_group: str
    duration: int  # in minutes
    department: str  # Added department field

@dataclass
class Room:
    id: str
    capacity: int
    department: str  # Added department field
    room_type: str  # 'LH' or 'MLH' or 'Seminar' or 'Exam'

class TimetableGenerator:
    def __init__(self):
        self.courses: List[Course] = []
        self.time_slots: List[TimeSlot] = []
        self.rooms: List[Room] = []
        self.graph = nx.Graph()
        self.color_assignments: Dict[str, int] = {}  # course_id -> time_slot_index
        self.room_assignments: Dict[str, str] = {}  # course_id -> room_id
        self.teacher_schedules: Dict[str, List[Tuple[Course, TimeSlot, Room]]] = defaultdict(list)
        self.student_schedules: Dict[str, List[Tuple[Course, TimeSlot, Room]]] = defaultdict(list)

    def add_course(self, course: Course):
        """Add a course to the system."""
        self.courses.append(course)
        self.graph.add_node(course.id)

    def add_time_slot(self, time_slot: TimeSlot):
        """Add a time slot to the system."""
        self.time_slots.append(time_slot)

    def add_room(self, room: Room):
        """Add a room to the system."""
        self.rooms.append(room)

    def build_conflict_graph(self):
        """Build the conflict graph where edges represent course conflicts."""
        for i, course1 in enumerate(self.courses):
            for course2 in self.courses[i+1:]:
                if (course1.teacher == course2.teacher or 
                    course1.student_group == course2.student_group):
                    self.graph.add_edge(course1.id, course2.id)

    def welsh_powell_coloring(self) -> Dict[str, int]:
        """
        Implement Welsh-Powell graph coloring algorithm.
        Returns a dictionary mapping course IDs to time slot indices.
        Time Complexity: O(V^2 + E), where V is number of vertices and E is number of edges
        """
        # Sort vertices by degree in descending order
        vertices = sorted(self.graph.nodes(), 
                        key=lambda x: self.graph.degree(x), 
                        reverse=True)
        
        colors = {}  # vertex -> color
        available_colors = set(range(len(self.time_slots)))
        
        for vertex in vertices:
            # Find colors used by adjacent vertices
            used_colors = {colors[neighbor] for neighbor in self.graph.neighbors(vertex)
                         if neighbor in colors}
            
            # Assign the first available color
            color = next(color for color in available_colors if color not in used_colors)
            colors[vertex] = color
            
        return colors

    def assign_rooms(self):
        """
        Assign rooms to courses using a three-tier approach:
        1. Try department's own rooms first
        2. Try NAB rooms if department rooms are full
        3. Try other departments' rooms as a last resort
        Time Complexity: O(C * R), where C is number of courses and R is number of rooms
        """
        for course in self.courses:
            time_slot_idx = self.color_assignments[course.id]
            time_slot = self.time_slots[time_slot_idx]
            assigned = False

            # Tier 1: Try department's own rooms
            department_rooms = [r for r in self.rooms if r.department == course.department]
            for room in department_rooms:
                if self._is_room_available(room.id, time_slot):
                    self.room_assignments[course.id] = room.id
                    assigned = True
                    break

            # Tier 2: Try NAB rooms if department rooms are full
            if not assigned:
                nab_rooms = [r for r in self.rooms if r.department.upper() == 'NAB']
                for room in nab_rooms:
                    if self._is_room_available(room.id, time_slot):
                        self.room_assignments[course.id] = room.id
                        assigned = True
                        break

            # Tier 3: Try other departments' rooms as a last resort
            if not assigned:
                other_rooms = [r for r in self.rooms 
                             if r.department != course.department 
                             and r.department.upper() != 'NAB']
                for room in other_rooms:
                    if self._is_room_available(room.id, time_slot):
                        self.room_assignments[course.id] = room.id
                        assigned = True
                        break

            # If still not assigned, print debug info
            if not assigned:
                print(f"Warning: Could not assign room for {course.id} ({course.name})")
                print(f"Department: {course.department}")
                print(f"Time slot: {time_slot.day} {time_slot.start_time.strftime('%H:%M')}")

    def _is_room_available(self, room_id: str, time_slot: TimeSlot) -> bool:
        """Check if a room is available during a given time slot."""
        for course_id, assigned_room in self.room_assignments.items():
            if assigned_room == room_id:
                course_time_slot = self.time_slots[self.color_assignments[course_id]]
                if self._time_slots_overlap(time_slot, course_time_slot):
                    return False
        return True

    def _time_slots_overlap(self, slot1: TimeSlot, slot2: TimeSlot) -> bool:
        """Check if two time slots overlap."""
        return (slot1.day == slot2.day and
                slot1.start_time < slot2.end_time and
                slot2.start_time < slot1.end_time)

    def optimize_schedules(self):
        """
        Optimize teacher and student schedules using dynamic programming
        to minimize idle time.
        Time Complexity: O(N * T), where N is number of courses and T is number of time slots
        """
        for course in self.courses:
            if course.id not in self.room_assignments:
                print(f"Skipping {course.id} ({course.name}) - no room assigned.")
                continue  # Skip courses with no room assigned
            time_slot_idx = self.color_assignments[course.id]
            time_slot = self.time_slots[time_slot_idx]
            room = next(r for r in self.rooms if r.id == self.room_assignments[course.id])
            self.teacher_schedules[course.teacher].append((course, time_slot, room))
            self.student_schedules[course.student_group].append((course, time_slot, room))

        # Sort schedules by time
        for teacher in self.teacher_schedules:
            self.teacher_schedules[teacher].sort(key=lambda x: x[1].start_time)
        for group in self.student_schedules:
            self.student_schedules[group].sort(key=lambda x: x[1].start_time)

    def generate_timetable(self):
        """Generate the complete timetable."""
        self.build_conflict_graph()
        self.color_assignments = self.welsh_powell_coloring()
        self.assign_rooms()
        self.optimize_schedules()
        return self._format_timetable()

    def _format_timetable(self) -> str:
        """Format the timetable for display."""
        output = []
        
        # Course assignments
        output.append("Course Assignments:")
        for course in self.courses:
            time_slot = self.time_slots[self.color_assignments[course.id]]
            room = next(r for r in self.rooms if r.id == self.room_assignments[course.id])
            output.append(f"{course.name}: {time_slot.day} {time_slot.start_time.strftime('%H:%M')}-"
                        f"{time_slot.end_time.strftime('%H:%M')} in Room {room.id}")
        
        # Teacher schedules
        output.append("\nTeacher Schedules:")
        for teacher, schedule in self.teacher_schedules.items():
            output.append(f"\n{teacher}:")
            for course, time_slot, room in schedule:
                output.append(f"  {time_slot.day} {time_slot.start_time.strftime('%H:%M')}-"
                            f"{time_slot.end_time.strftime('%H:%M')}: {course.name} in Room {room.id}")
        
        # Student group schedules
        output.append("\nStudent Group Schedules:")
        for group, schedule in self.student_schedules.items():
            output.append(f"\n{group}:")
            for course, time_slot, room in schedule:
                output.append(f"  {time_slot.day} {time_slot.start_time.strftime('%H:%M')}-"
                            f"{time_slot.end_time.strftime('%H:%M')}: {course.name} in Room {room.id}")
        
        return "\n".join(output) 

 