from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Lesson Models
class LessonBase(BaseModel):
    title: str
    title_ru: str
    title_kk: str
    description: str
    description_ru: str
    description_kk: str
    content: str
    content_ru: str
    content_kk: str
    category: str
    difficulty: str  # beginner, intermediate, advanced
    xp_reward: int = 50
    order: int = 0

class LessonResponse(LessonBase):
    id: str
    is_completed: bool = False

# Quiz Models
class QuizQuestion(BaseModel):
    id: str
    question: str
    question_ru: str
    question_kk: str
    options: List[str]
    options_ru: List[str]
    options_kk: List[str]
    correct_answer: int  # index of correct option

class QuizSubmit(BaseModel):
    answers: List[int]  # list of selected option indexes

class QuizResult(BaseModel):
    correct: int
    total: int
    xp_earned: int
    passed: bool

# Progress Models
class UserProgress(BaseModel):
    user_id: str
    xp: int = 0
    level: int = 1
    level_name: str = "Новичок"
    level_name_en: str = "Beginner"
    level_name_kk: str = "Жаңадан бастаушы"
    completed_lessons: List[str] = []
    completed_quizzes: List[str] = []
    achievements: List[str] = []
    current_streak: int = 0
    longest_streak: int = 0
    last_activity_date: Optional[str] = None
    total_quizzes_passed: int = 0
    total_lessons_completed: int = 0

class Achievement(BaseModel):
    id: str
    name: str
    name_ru: str
    name_kk: str
    description: str
    description_ru: str
    description_kk: str
    icon: str
    xp_reward: int
    requirement_type: str  # lessons, quizzes, streak, xp, goals
    requirement_value: int

class DailyCheckinResponse(BaseModel):
    streak: int
    xp_earned: int
    new_achievements: List[str] = []